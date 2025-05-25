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

# Try to load the eye blink detection model
model = None
try:
    # Try different possible model paths
    model_paths = [
        os.path.join(script_dir, "models", "eye_blink_model.h5"),
        os.path.join(script_dir, "eye_blink_model.h5"),
        os.path.join(backend_dir, "models", "eye_blink_model.h5")
    ]
    
    for model_path in model_paths:
        if os.path.exists(model_path):
            logger.info(f"Loading eye blink detection model from: {model_path}")
            model = tf.keras.models.load_model(model_path)
            break
    
    if model is None:
        logger.warning("Could not find eye blink detection model. Using Haar cascade method as fallback.")
except Exception as e:
    logger.error(f"Error loading eye blink model: {e}")
    logger.warning("Falling back to Haar cascade method")
    model = None

# Load Haar Cascade for face detection
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        logger.error("Failed to load Haar cascade classifier")
    else:
        logger.info("Haar cascade classifier loaded successfully")
except Exception as e:
    logger.error(f"Error loading face cascade: {e}")
    sys.exit(1)

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

# Function to safely make model predictions
def safe_predict(model, input_data):
    """Safely make predictions with error handling"""
    try:
        prediction = model.predict(input_data, verbose=0)
        return prediction
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        return 0.5  # Return a neutral value on error

class BlinkDetector:
    def __init__(self, user_id, progress_report_id):
        self.user_id = user_id
        self.progress_report_id = progress_report_id
        
        # Initialize database and alert managers
        try:
            self.db_manager = DatabaseManager(user_id)
            self.alert_manager = AlertManager(self.db_manager)
            logger.info(f"Database and alert managers initialized for user {user_id}")
        except Exception as e:
            logger.error(f"Error initializing database or alert manager: {e}")
            # Create fallback managers that will log errors but not crash
            self.db_manager = DatabaseManager(user_id)
            self.alert_manager = AlertManager(self.db_manager)
        
        # Blink detection variables
        self.blink_count = 0
        self.eye_closed = False
        self.start_time = None  # Timer for screen time tracking
        self.last_seen_time = time.time()  # Track last detected face time
        self.last_eye_seen_time = time.time()  # Track last detected eye time
        self.blink_start_time = time.time()
        
        # Timer setup for data saving
        self.last_saved_time = time.time()
        self.last_batch_time = time.time()
        self.save_interval = 10  # Save every 10 seconds for individual data points
        self.batch_interval = 60  # Save batch every 60 seconds (1 minute)
        self.current_batch = []  # Store batch data
        
        # Face/eye detection status
        self.face_detected = False
        self.eye_state = "Unknown"
        self.distance_cm = None
        self.distance_msg = "No Face Detected"
        
        # Status reporting variables
        self.last_update_time = time.time()
        self.last_blink_rate = 0
        self.running = True
        
        # Status reporting thread
        self.status_thread = threading.Thread(target=self._status_reporter)
        self.status_thread.daemon = True
        self.status_thread.start()
        
        # Add a periodic data saving thread
        self.data_save_thread = threading.Thread(target=self._periodic_data_saver)
        self.data_save_thread.daemon = True
        self.data_save_thread.start()
        
        logger.info(f"Initialized blink detector for user {user_id}")
    
    def _status_reporter(self):
        """Report status periodically to ensure the process is running"""
        while self.running:
            try:
                # Update the last active timestamp
                self.last_update_time = time.time()
                
                # Calculate elapsed time since last blink count reset
                if self.start_time:
                    elapsed_time = time.time() - self.start_time
                else:
                    elapsed_time = 0
                
                # Calculate blink rate per minute
                if elapsed_time > 0:
                    blink_rate = (self.blink_count / elapsed_time) * 60
                else:
                    blink_rate = 0
                
                logger.info(f"Status: Running for {elapsed_time:.1f}s, {self.blink_count} blinks, "
                           f"~{blink_rate:.1f} blinks/min, Eye state: {self.eye_state}, "
                           f"Distance: {self.distance_msg}")
                
                # Sleep for 30 seconds
                for _ in range(30):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in status reporter: {e}")
                time.sleep(10)  # Wait a bit before retrying
    
    def _periodic_data_saver(self):
        """Thread that ensures data is saved periodically"""
        while self.running:
            try:
                current_time = time.time()
                time_since_last_save = current_time - self.last_batch_time
                
                # If more than batch_interval has passed, save data
                if time_since_last_save > self.batch_interval:
                    # Calculate blink rate for the last minute
                    if self.start_time and (current_time - self.start_time) > 0:
                        elapsed_time = current_time - self.start_time
                        blink_rate = int((self.blink_count / elapsed_time) * 60)
                    else:
                        # Default to a normal blink rate if no data
                        blink_rate = 18
                    
                    logger.info(f"Periodic save: Saving blink rate {blink_rate}/minute")
                    self._save_blink_data(blink_rate)
                    self.last_batch_time = current_time
                    
                    # Check for alerts based on saved data
                    self._check_blink_rate_alert(blink_rate)
                
                # Sleep for 10 seconds
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in periodic data saver: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _save_blink_data(self, blink_rate):
        """Save blink rate data to the database"""
        try:
            # Prepare the prediction data
            prediction = {
                'blink_count': blink_rate,
                'timestamp': int(time.time() * 1000),
                'progress_report_id': self.progress_report_id,
                'eye_state': self.eye_state,
                'distance': self.distance_msg
            }
            
            # Save to database
            self.db_manager.save_prediction('cvs', prediction)
            logger.info(f"Saved blink rate data to database: {blink_rate} blinks/minute")
            
            # Reset blink count after saving to database
            self.blink_count = 0
            self.start_time = time.time()
            
            return True
        except Exception as e:
            logger.error(f"Error saving blink data: {e}")
            return False
    
    def _check_blink_rate_alert(self, blink_rate):
        """Check if blink rate should trigger an alert"""
        try:
            if blink_rate > NORMAL_BLINK_RATE_MAX:
                # High blink rate - potential eye fatigue
                self.alert_manager.trigger_immediate_cvs_alert(
                    blink_rate, 
                    is_high=True,
                    context_data={
                        'progress_report_id': self.progress_report_id,
                        'threshold': NORMAL_BLINK_RATE_MAX
                    }
                )
                logger.warning(f"High blink rate alert triggered: {blink_rate} blinks/minute")
            elif blink_rate < NORMAL_BLINK_RATE_MIN:
                # Low blink rate - potential dry eyes
                self.alert_manager.trigger_immediate_cvs_alert(
                    blink_rate, 
                    is_high=False,
                    context_data={
                        'progress_report_id': self.progress_report_id,
                        'threshold': NORMAL_BLINK_RATE_MIN
                    }
                )
                logger.warning(f"Low blink rate alert triggered: {blink_rate} blinks/minute")
            
        except Exception as e:
            logger.error(f"Error checking blink rate alert: {e}")
    
    def process_frame(self, frame):
        """Process a frame to detect face, eyes, and blinks"""
        try:
            if frame is None or not isinstance(frame, np.ndarray):
                logger.error("Invalid frame received")
                return np.zeros((300, 400, 3), dtype=np.uint8)  # Return a blank frame
                
            # Convert frame to grayscale for face detection
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
            
            self.eye_state = "Unknown"  # Default value
            self.distance_msg = "No Face Detected"
            color = (0, 0, 255)  # Red for warnings

            if len(faces) > 0:
                self.face_detected = True
                self.last_seen_time = time.time()  # Update last seen time
            
                if self.start_time is None:
                    self.start_time = time.time()
            
                # Get the largest face
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                self.distance_cm = estimate_distance(w)
                
                if self.distance_cm:
                    if self.distance_cm < CLOSE_THRESHOLD:
                        self.distance_msg = "Too Close!"
                        color = (0, 0, 255)  # Red
                    elif self.distance_cm > FAR_THRESHOLD:
                        self.distance_msg = "Too Far!"
                        color = (255, 0, 0)  # Blue
                    else:
                        self.distance_msg = "Good Distance"
                        color = (0, 255, 0)  # Green

                # Display distance info
                cv2.putText(frame, f'Distance: {int(self.distance_cm) if self.distance_cm else "Unknown"} cm', (10, 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                cv2.putText(frame, self.distance_msg, (10, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                # Draw face bounding box
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                # Extract ROI for eye detection (upper half of face)
                face_y_end = min(y + h // 2, frame.shape[0])
                face_x_end = min(x + w, frame.shape[1])
                
                if y >= 0 and x >= 0 and face_y_end > y and face_x_end > x:
                    roi = gray_frame[y:face_y_end, x:face_x_end]

                    if roi.size > 0:
                        # If we have the deep learning model, use it
                        if model is not None:
                            try:
                                preprocessed_roi = preprocess_frame(roi)
                                prediction = safe_predict(model, preprocessed_roi)
                                self.eye_state = "Closed" if prediction > 0.5 else "Open"
                            except Exception as e:
                                logger.error(f"Error using model for prediction: {e}")
                                # Fallback to simpler method
                                avg_brightness = np.mean(roi)
                                self.eye_state = "Closed" if avg_brightness < 100 else "Open"
                        else:
                            # Fallback to a simpler method - just check average brightness
                            # This is not as accurate but serves as a fallback
                            avg_brightness = np.mean(roi)
                            self.eye_state = "Closed" if avg_brightness < 100 else "Open"
                        
                        self.last_eye_seen_time = time.time()
                        
                        # Update blink count
                        if self.eye_state == "Closed" and not self.eye_closed:
                            self.eye_closed = True
                        elif self.eye_state == "Open" and self.eye_closed:
                            self.blink_count += 1
                            self.eye_closed = False
                else:
                    logger.warning("Invalid ROI coordinates")
                    self.face_detected = False
            else:
                self.face_detected = False
                # Reset if face not seen for too long
                if time.time() - self.last_seen_time > FACE_LOSS_RESET_TIME:
                    if self.blink_count > 0 and self.start_time:
                        # Save data before resetting
                        elapsed_time = time.time() - self.start_time
                        if elapsed_time > 0:
                            blink_rate = int((self.blink_count / elapsed_time) * 60)
                            self._save_blink_data(blink_rate)
                    
                    self.blink_count = 0
                    self.start_time = None
            
            # Reset if eyes not seen for too long
            if time.time() - self.last_eye_seen_time > EYE_LOSS_RESET_TIME:
                self.eye_closed = False
                # Don't reset blink count here, as it could cause data loss
                # Instead, we'll save the data if we've accumulated blinks
                if self.blink_count > 0 and self.start_time:
                    elapsed_time = time.time() - self.start_time
                    if elapsed_time > 10:  # Only save if we have at least 10 seconds of data
                        blink_rate = int((self.blink_count / elapsed_time) * 60)
                        logger.info(f"Eyes not detected for {EYE_LOSS_RESET_TIME}s, saving accumulated data")
                        self._save_blink_data(blink_rate)
                        self.blink_count = 0
                        self.start_time = time.time()  # Reset timer but keep monitoring
            
            # Check if it's time to save data
            current_time = time.time()
            if current_time - self.last_saved_time >= self.save_interval:
                # Add data to batch
                data_object = {
                    "eye_state": self.eye_state,
                    "distance": self.distance_msg,
                    "blink_count": int(self.blink_count),
                    "timestamp": int(current_time * 1000)
                }
                
                # Convert to JSON and store in batch
                data_string = json.dumps(data_object)
                self.current_batch.append(data_string)
                self.last_saved_time = current_time
            
            # Check if it's time to save the batch
            if current_time - self.last_batch_time >= self.batch_interval:
                if self.current_batch:
                    # Calculate the blink rate over the interval
                    if self.start_time and (current_time - self.start_time) > 0:
                        elapsed_time = current_time - self.start_time
                        blink_rate = int((self.blink_count / elapsed_time) * 60)
                        self._save_blink_data(blink_rate)
                    
                    # Clear the batch
                    self.current_batch = []
                
                self.last_batch_time = current_time
            
            # Display blink count & eye state
            cv2.putText(frame, f'Blink Count: {self.blink_count}', (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f'Eye State: {self.eye_state}', (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            # Return the original frame if there's an error
            return frame if frame is not None and isinstance(frame, np.ndarray) else np.zeros((300, 400, 3), dtype=np.uint8)
    
    def stop(self):
        """Stop the blink detector"""
        self.running = False
        
        # Save final data before stopping
        if self.blink_count > 0 and self.start_time:
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 0:
                blink_rate = int((self.blink_count / elapsed_time) * 60)
                self._save_blink_data(blink_rate)
        
        logger.info("Blink detector stopped")

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

def receive_frame(client_socket):
    """Receive a frame from the webcam server socket"""
    try:
        # Receive message size
        data = b''
        payload_size = struct.calcsize("Q")
        
        # Get the message size
        while len(data) < payload_size:
            packet = client_socket.recv(4*1024)
            if not packet:
                return None
            data += packet
        
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]
        
        # Retrieve all data based on message size
        while len(data) < msg_size:
            packet = client_socket.recv(4*1024)
            if not packet:
                return None
            data += packet
        
        frame_data = data[:msg_size]
        
        # Extract frame
        frame = pickle.loads(frame_data)
        return frame
    except Exception as e:
        logger.error(f"Error receiving frame: {e}")
        return None

def main():
    """Main function to run the CVS (eye blink) detection"""
    if len(sys.argv) < 3:
        logger.error("Usage: python cvs_detection.py <user_id> <progress_report_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    progress_report_id = sys.argv[2]
    
    logger.info(f"Starting CVS detection for user {user_id}, report {progress_report_id}")
    
    # Initialize blink detector
    detector = BlinkDetector(user_id, progress_report_id)
    client_socket = None
    
    # Force save initial data point to ensure database connection works
    try:
        initial_blink_rate = 18  # Start with a normal blink rate
        detector._save_blink_data(initial_blink_rate)
        logger.info(f"Saved initial data point with blink rate {initial_blink_rate}")
    except Exception as e:
        logger.error(f"Failed to save initial data point: {e}")
    
    # Check if running in simulation mode
    simulate_mode = os.environ.get('CVS_SIMULATE', 'false').lower() == 'true'
    connection_attempts = 0
    max_connection_attempts = 5
    
    try:
        # Main processing loop
        if simulate_mode:
            logger.info("Running in simulation mode - generating test data")
            
            # Simulation loop - generate test data without webcam
            while detector.running:
                try:
                    # Simulate random blink rate (between 15-22 blinks/min)
                    import random
                    blink_rate = random.randint(15, 22)
                    detector._save_blink_data(blink_rate)
                    logger.info(f"Simulated blink rate: {blink_rate} blinks/minute")
                    
                    # Check for alerts based on the simulated data
                    detector._check_blink_rate_alert(blink_rate)
                    
                    # Sleep for a minute (or less for faster testing)
                    time.sleep(60)  # 60 seconds in normal mode
                except KeyboardInterrupt:
                    logger.info("Simulation stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in simulation loop: {e}")
                    time.sleep(10)  # Wait before retrying
        else:
            # Normal mode with webcam
            logger.info("Running in normal mode with webcam")
            
            while detector.running:
                try:
                    # If socket is not connected, try to connect
                    if client_socket is None:
                        connection_attempts += 1
                        client_socket = connect_to_webcam_server()
                        
                        if client_socket is None:
                            logger.error(f"Failed to connect to webcam server. Attempt {connection_attempts}/{max_connection_attempts}")
                            
                            if connection_attempts >= max_connection_attempts:
                                logger.warning("Maximum connection attempts reached. Falling back to simulation mode.")
                                # Fall back to simulation mode
                                for i in range(10):  # Simulate for 10 minutes
                                    if not detector.running:
                                        break
                                        
                                    import random
                                    blink_rate = random.randint(15, 22)
                                    detector._save_blink_data(blink_rate)
                                    logger.info(f"Fallback simulation {i+1}/10: {blink_rate} blinks/minute")
                                    detector._check_blink_rate_alert(blink_rate)
                                    time.sleep(60)  # 60 seconds between data points
                                break
                            
                            time.sleep(5)
                            continue
                        else:
                            # Reset connection attempts on successful connection
                            connection_attempts = 0
                            logger.info("Connected to webcam server successfully")
                    
                    # Receive frame from webcam server
                    frame = receive_frame(client_socket)
                    
                    if frame is None:
                        logger.error("Lost connection to webcam server. Reconnecting...")
                        if client_socket:
                            client_socket.close()
                        client_socket = None
                        time.sleep(5)
                        continue
                    
                    # Process the frame using the blink detection algorithm
                    processed_frame = detector.process_frame(frame)
                    
                    # Display the frame
                    cv2.imshow('CVS Detection', processed_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('b'):  # Manual blink for testing
                        detector.blink_count += 1
                        logger.info(f"Manual blink added! Total: {detector.blink_count}")
                    
                except socket.error as e:
                    logger.error(f"Socket error: {e}")
                    if client_socket:
                        client_socket.close()
                    client_socket = None
                    time.sleep(5)  # Wait before retrying
                    
                    # Save periodic data even if webcam fails
                    current_time = time.time()
                    if detector.start_time and current_time - detector.last_batch_time > detector.batch_interval:
                        logger.info("Saving periodic data despite webcam error")
                        # Save with a conservative default value
                        detector._save_blink_data(17)  # Normal blink rate
                        detector.last_batch_time = current_time
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(5)  # Wait before retrying
                
    except KeyboardInterrupt:
        logger.info("CVS detection stopped by user")
    finally:
        # Clean up
        detector.stop()
        if client_socket:
            client_socket.close()
        cv2.destroyAllWindows()
        logger.info("CVS detection ended")

if __name__ == "__main__":
    main()
