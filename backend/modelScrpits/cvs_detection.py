#!/usr/bin/env python
import cv2
import numpy as np
import time
import sys
import json
import os
import logging
import socket
import struct
import pickle
import threading
from datetime import datetime
import tensorflow as tf

# Add parent directory to path so we can import from utils
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.append(backend_dir)

# Import database manager
from utils.database import DatabaseManager
from utils.alert_manager import AlertManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CVS_Detection')

# Webcam server settings
WEBCAM_HOST = '127.0.0.1'
WEBCAM_PORT = 9999

# Reference values for distance estimation
REFERENCE_FACE_WIDTH = 160  # Pixels (adjust based on testing)
NORMAL_DISTANCE_CM = 60
CLOSE_THRESHOLD = 50  # cm
FAR_THRESHOLD = 70  # cm
SCREEN_TIME_LIMIT = 20 * 60  # 20 minutes
FACE_LOSS_RESET_TIME = 3  # Time in seconds to reset blink count if face is lost
EYE_LOSS_RESET_TIME = 2  # Time in seconds to reset blink count if eyes are lost

# Define constants for blink rate tracking
NORMAL_BLINK_RATE_MIN = 17  # Minimum normal blink rate (per minute)
NORMAL_BLINK_RATE_MAX = 20  # Maximum normal blink rate (per minute)

# Define paths relative to the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, 'models', 'eye_blink_model.h5')
FACE_CASCADE_PATH = os.path.join(SCRIPT_DIR, 'models', 'haarcascade_frontalface_default.xml')

# Try to load the eye blink detection model
def load_blink_model():
    """Load the eye blink detection model from the models directory"""
    model = None
    try:
        if os.path.exists(MODEL_PATH):
            logger.info(f"Loading eye blink detection model from: {MODEL_PATH}")
            model = tf.keras.models.load_model(MODEL_PATH)
        else:
            logger.warning(f"Could not find eye blink detection model at {MODEL_PATH}. Using Haar cascade method as fallback.")
    except Exception as e:
        logger.error(f"Error loading eye blink model: {e}")
        logger.warning("Falling back to Haar cascade method")
    
    return model

# Function to preprocess frame for model
def preprocess_frame(frame, target_size=(26, 34)):
    if len(frame.shape) == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    resized_frame = cv2.resize(frame, (target_size[1], target_size[0]))  # (width, height)
    normalized_frame = resized_frame / 255.0
    
    return np.expand_dims(normalized_frame, axis=(0, -1))

# Function to estimate distance from face width
def estimate_distance(face_width):
    if face_width == 0:
        return None  # No face detected
    return (REFERENCE_FACE_WIDTH * NORMAL_DISTANCE_CM) / face_width

# Function to connect to webcam server
def connect_to_webcam_server():
    """Connect to the webcam server socket"""
    try:
        # Create socket connection
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((WEBCAM_HOST, WEBCAM_PORT))
        logger.info(f"Connected to webcam server at {WEBCAM_HOST}:{WEBCAM_PORT}")
        return client_socket
    except Exception as e:
        logger.error(f"Failed to connect to webcam server: {e}")
        return None

def main():
    """Main function to run the CVS (eye blink) detection"""
    global ENABLE_GUI
    
    # Force disable GUI to prevent any display windows
    ENABLE_GUI = False
    
    if len(sys.argv) < 3:
        logger.error("Usage: python cvs_detection.py <user_id> <progress_report_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    progress_report_id = sys.argv[2]
    
    logger.info(f"Starting CVS detection for user {user_id}, report {progress_report_id}")
    logger.info("Running in headless mode - no display window will be shown")
    
    # Initialize database connection
    try:
        db_manager = DatabaseManager(user_id)
        alert_manager = AlertManager(db_manager)
        logger.info(f"Database and alert managers initialized for user {user_id}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db_manager = None
        alert_manager = None
    
    # Load face cascade for face detection
    try:
        face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
        if face_cascade.empty():
            # Fallback to OpenCV's built-in cascades
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            logger.info("Using OpenCV's built-in face cascade")
        else:
            logger.info(f"Face detector loaded from {FACE_CASCADE_PATH}")
    except Exception as e:
        logger.error(f"Error loading face detector: {e}")
        # Fallback to OpenCV's built-in cascades
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        logger.info("Using OpenCV's built-in face cascade as fallback")
        
    if face_cascade.empty():
        logger.error("Failed to load Haar cascade classifier")
        sys.exit(1)
    
    # Load the eye blink detection model
    model = load_blink_model()
    
    # Initialize variables for blink detection
    blink_count = 0
    eye_closed = False
    start_time = None
    last_seen_time = time.time()
    last_eye_seen_time = time.time()
    eye_state = "Unknown"
    distance_msg = "No Face Detected"
    
    # Initialize variables for data saving
    last_saved_time = time.time()
    last_batch_time = time.time()
    save_interval = 10  # Save data every 10 seconds
    batch_interval = 60  # Save batch every 60 seconds
    current_batch = []
    
    # Connect to webcam server
    client_socket = connect_to_webcam_server()
    if not client_socket:
        logger.error("Failed to connect to webcam server. Exiting...")
        sys.exit(1)
    
    data = b""  # Buffer for receiving data
    
    try:
        logger.info("Starting main processing loop")
        while True:
            try:
                # Receive frame size
                while len(data) < struct.calcsize("Q"):
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        logger.error("Connection to webcam server lost")
                        break
                    data += packet
                
                if not packet:  # If connection was lost, try to reconnect
                    client_socket = connect_to_webcam_server()
                    if not client_socket:
                        logger.error("Failed to reconnect to webcam server")
                        time.sleep(5)
                        continue
                    data = b""
                    continue
                
                packed_msg_size = data[:struct.calcsize("Q")]
                data = data[struct.calcsize("Q"):]
                msg_size = struct.unpack("Q", packed_msg_size)[0]
                
                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)
                
                frame_data = data[:msg_size] 
                data = data[msg_size:]
                
                # Deserialize the frame
                frame = pickle.loads(frame_data)
                
                # Convert frame to grayscale for face detection
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
                
                # Default values
                eye_state = "Unknown"
                distance_msg = "No Face Detected"
                
                if len(faces) > 0:
                    last_seen_time = time.time()  # Update last seen time
                    
                    if start_time is None:
                        start_time = time.time()
                    
                    # Get the largest face
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    distance_cm = estimate_distance(w)
                    
                    if distance_cm:
                        if distance_cm < CLOSE_THRESHOLD:
                            distance_msg = "Too Close!"
                        elif distance_cm > FAR_THRESHOLD:
                            distance_msg = "Too Far!"
                        else:
                            distance_msg = "Good Distance"
                    
                    # Extract region of interest (ROI) for eye detection
                    roi = gray_frame[y:y + h // 2, x:x + w]
                    
                    if roi.size > 0:
                        if model is not None:
                            # Use the deep learning model for prediction
                            preprocessed_roi = preprocess_frame(roi)
                            prediction = model.predict(preprocessed_roi, verbose=0)
                            eye_state = "Closed" if prediction > 0.5 else "Open"
                        else:
                            # Fallback to simpler method based on brightness
                            avg_brightness = np.mean(roi)
                            eye_state = "Closed" if avg_brightness < 100 else "Open"
                        
                        last_eye_seen_time = time.time()
                        
                        # Update blink count based on eye state transitions
                        if eye_state == "Closed" and not eye_closed:
                            eye_closed = True
                        elif eye_state == "Open" and eye_closed:
                            blink_count += 1
                            eye_closed = False
                            logger.info(f"Blink detected! Total count: {blink_count}")
                
                else:
                    # Reset if face not seen for too long
                    if time.time() - last_seen_time > FACE_LOSS_RESET_TIME:
                        # Save data before resetting
                        if blink_count > 0 and start_time and db_manager:
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                blink_rate = int((blink_count / elapsed_time) * 60)
                                save_blink_data(db_manager, blink_rate, progress_report_id, eye_state, distance_msg)
                        
                        blink_count = 0
                        start_time = None
                
                # Reset if eyes not seen for too long
                if time.time() - last_eye_seen_time > EYE_LOSS_RESET_TIME:
                    eye_closed = False
                
                # Check if it's time to save data
                current_time = time.time()
                if current_time - last_saved_time >= save_interval:
                    # Add data to batch
                    data_object = {
                        "eye_state": eye_state,
                        "distance": distance_msg,
                        "blink_count": int(blink_count),
                        "timestamp": int(current_time * 1000)
                    }
                    
                    # Log the current state
                    logger.info(f"Current state: Eyes: {eye_state}, Distance: {distance_msg}, Blinks: {blink_count}")
                    
                    # Convert to JSON and store in batch
                    data_string = json.dumps(data_object)
                    current_batch.append(data_string)
                    last_saved_time = current_time
                
                # Check if it's time to save the batch
                if current_time - last_batch_time >= batch_interval and db_manager:
                    if start_time and (current_time - start_time) > 0:
                        elapsed_time = current_time - start_time
                        blink_rate = int((blink_count / elapsed_time) * 60)
                        save_blink_data(db_manager, blink_rate, progress_report_id, eye_state, distance_msg)
                        
                        # Check for alerts
                        if alert_manager:
                            check_blink_rate_alert(alert_manager, blink_rate, progress_report_id)
                        
                        # Reset for next interval
                        blink_count = 0
                        start_time = time.time()
                    
                    # Clear the batch
                    current_batch = []
                    last_batch_time = current_time
                
                # No GUI operations - just process frames silently
                # Add a small sleep to prevent CPU overload
                time.sleep(0.01)
            except socket.error as e:
                logger.error(f"Socket error: {e}")
                # Try to reconnect
                if client_socket:
                    client_socket.close()
                client_socket = connect_to_webcam_server()
                if not client_socket:
                    logger.error("Failed to reconnect to webcam server")
                    time.sleep(5)
                data = b""
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("CVS detection stopped by user")
    finally:
        # Save final data before exiting
        if blink_count > 0 and start_time and db_manager:
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                blink_rate = int((blink_count / elapsed_time) * 60)
                save_blink_data(db_manager, blink_rate, progress_report_id, eye_state, distance_msg)
        
        # Clean up
        if client_socket:
            client_socket.close()
        logger.info("CVS detection ended")

def save_blink_data(db_manager, blink_rate, progress_report_id, eye_state, distance_msg):
    """Save blink rate data to the database with retry logic"""
    try:
        # Prepare the prediction data
        prediction = {
            'blink_count': blink_rate,
            'timestamp': int(time.time() * 1000),
            'progress_report_id': progress_report_id,
            'eye_state': eye_state,
            'distance': distance_msg
        }
        
        # Save to database with retry logic
        for attempt in range(3):
            try:
                db_manager.save_prediction('cvs', prediction)
                logger.info(f"Saved blink rate data to database: {blink_rate} blinks/minute")
                return True
            except Exception as e:
                logger.error(f"Error saving blink data (attempt {attempt+1}/3): {e}")
                if attempt < 2:  # Only sleep if we're going to retry
                    time.sleep(2)
        
        logger.error("All 3 attempts to save data failed")
        return False
        
    except Exception as e:
        logger.error(f"Error preparing blink data: {e}")
        return False

def check_blink_rate_alert(alert_manager, blink_rate, progress_report_id):
    """Check if blink rate should trigger an alert"""
    try:
        if blink_rate > NORMAL_BLINK_RATE_MAX:
            # High blink rate - potential eye fatigue
            alert_manager.trigger_immediate_cvs_alert(
                blink_rate, 
                is_high=True,
                context_data={
                    'progress_report_id': progress_report_id,
                    'threshold': NORMAL_BLINK_RATE_MAX
                }
            )
            logger.warning(f"High blink rate alert triggered: {blink_rate} blinks/minute")
        elif blink_rate < NORMAL_BLINK_RATE_MIN:
            # Low blink rate - potential dry eyes
            alert_manager.trigger_immediate_cvs_alert(
                blink_rate, 
                is_high=False,
                context_data={
                    'progress_report_id': progress_report_id,
                    'threshold': NORMAL_BLINK_RATE_MIN
                }
            )
            logger.warning(f"Low blink rate alert triggered: {blink_rate} blinks/minute")
        
    except Exception as e:
        logger.error(f"Error checking blink rate alert: {e}")

if __name__ == "__main__":
    main()
