"""
Hydration Detection Module

This module detects lip dryness to monitor hydration levels.
It uses computer vision techniques to analyze lip texture and color
to determine if the user appears dehydrated.
"""

import cv2
import numpy as np
import socket
import struct
import pickle
import time
import sys
import os
import logging
import traceback

# Configure logger with more verbose output
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hydration_detection.log'))  # Output to file
    ]
)
logger = logging.getLogger('HydrationDetection')
logger.info("Starting hydration detection module")

# Add parent directory to path so we can import utils
# Determine the absolute path of the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, '..'))
logger.info(f"Current directory: {current_dir}")
logger.info(f"Backend directory: {backend_dir}")

# Add backend directory to path for imports
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
    logger.info(f"Added {backend_dir} to sys.path")

# Import database manager
try:
    logger.info("Attempting to import database manager...")
    from utils.database import DatabaseManager
    logger.info("Successfully imported database manager")
except ImportError as e:
    logger.error(f"Error importing database manager: {e}")
    logger.error(f"sys.path: {sys.path}")
    logger.error(traceback.format_exc())
    sys.exit(1)

# -----------------------------------------------------------------------------
# Configuration Constants
# -----------------------------------------------------------------------------
HOST = '127.0.0.1'  # Webcam server host
PORT = 9999         # Webcam server port
TEXTURE_THRESHOLD = 30     # Used to normalize the texture score
DRYNESS_THRESHOLD = 0.17   # If normalized score > 0.17, consider lips as dry
CONNECTION_TIMEOUT = 10    # Socket connection timeout in seconds

# Monitoring duration in seconds (2 minutes)
MONITORING_DURATION = 120

# -----------------------------------------------------------------------------
# Setup Client Connection to Webcam Server
# -----------------------------------------------------------------------------
def setup_client_connection():
    """Setup connection to webcam server with timeout"""
    try:
        logger.info(f"Attempting to connect to webcam server at {HOST}:{PORT}")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(CONNECTION_TIMEOUT)  # Set timeout
        client_socket.connect((HOST, PORT))
        client_socket.settimeout(None)  # Reset to blocking mode after connection
        logger.info(f"Connected to webcam server at {HOST}:{PORT}")
        return client_socket
    except socket.timeout:
        logger.error(f"Timeout connecting to webcam server at {HOST}:{PORT}")
        logger.error("Make sure the webcam server is running")
        sys.exit(1)
    except ConnectionRefusedError:
        logger.error(f"Connection refused by webcam server at {HOST}:{PORT}")
        logger.error("Make sure the webcam server is running")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error connecting to webcam server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

# -----------------------------------------------------------------------------
# Load Haar Cascade Models
# -----------------------------------------------------------------------------
def load_cascade_models():
    """Load Haar cascade models for face and mouth detection"""
    try:
        # Determine the absolute path to the model files
        models_dir = os.path.join(current_dir, "models")
        logger.info(f"Models directory: {models_dir}")
        
        face_cascade_path = os.path.join(models_dir, "haarcascade_frontalface_default.xml")
        mouth_cascade_path = os.path.join(models_dir, "haarcascade_mcs_mouth.xml")
        
        logger.info(f"Face cascade path: {face_cascade_path}")
        logger.info(f"Mouth cascade path: {mouth_cascade_path}")
        
        # Check if model files exist
        if not os.path.exists(face_cascade_path):
            logger.error(f"Error: Face cascade file not found at {face_cascade_path}")
            logger.error(f"Directory contents: {os.listdir(models_dir)}")
            sys.exit(1)
        
        if not os.path.exists(mouth_cascade_path):
            logger.error(f"Error: Mouth cascade file not found at {mouth_cascade_path}")
            logger.error(f"Directory contents: {os.listdir(models_dir)}")
            sys.exit(1)
        
        # Load Haar Cascade Models for Face and Mouth Detection
        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        mouth_cascade = cv2.CascadeClassifier(mouth_cascade_path)
        
        # Verify the classifiers loaded correctly
        if face_cascade.empty():
            logger.error("Error: Face cascade failed to load")
            sys.exit(1)
            
        if mouth_cascade.empty():
            logger.error("Error: Mouth cascade failed to load")
            sys.exit(1)
        
        logger.info(f"Successfully loaded cascade models from {models_dir}")
        return face_cascade, mouth_cascade
    except Exception as e:
        logger.error(f"Error loading cascade models: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

# -----------------------------------------------------------------------------
# Get User Information from Arguments
# -----------------------------------------------------------------------------
def get_user_info():
    """Get user information from command line arguments"""
    try:
        logger.info(f"Command line arguments: {sys.argv}")
        if len(sys.argv) < 2:
            logger.error("Error: Missing user email argument")
            logger.error("Usage: python hydration_detection.py <user_email> [progress_report_id]")
            sys.exit(1)
        
        user_email = sys.argv[1]
        progress_report_id = sys.argv[2] if len(sys.argv) > 2 else None
        
        logger.info(f"User email: {user_email}")
        if progress_report_id:
            logger.info(f"Progress report ID: {progress_report_id}")
        
        return user_email, progress_report_id
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

# -----------------------------------------------------------------------------
# Initialize Database Connection
# -----------------------------------------------------------------------------
def initialize_database(user_email):
    """Initialize database connection"""
    try:
        logger.info(f"Initializing database for user: {user_email}")
        db_manager = DatabaseManager(user_email)
        logger.info(f"Connected to database for user: {user_email}")
        return db_manager
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

# -----------------------------------------------------------------------------
# Main Processing Loop
# -----------------------------------------------------------------------------
def main():
    """Main processing loop for hydration detection"""
    try:
        # Get user information
        USER_EMAIL, progress_report_id = get_user_info()
        
        # Initialize database
        db_manager = initialize_database(USER_EMAIL)
        
        # Load cascade models
        face_cascade, mouth_cascade = load_cascade_models()
        
        # Connect to webcam server
        client_socket = setup_client_connection()
        
        # Timer setup for data collection
        save_interval = 1    # Save lip dryness status every 1 second
        last_saved_time = time.time()
        lip_dryness_batch = []  # Store lip dryness data before saving
        
        # Start time to track the 2-minute duration
        start_time = time.time()
        
        data = b""
        
        logger.info(f"Starting hydration monitoring for user: {USER_EMAIL}")
        logger.info(f"Monitoring will run for {MONITORING_DURATION} seconds (2 minutes)")
        
        # Update user monitoring status
        db_manager.update_user_monitoring_status(True)
        
        while True:
            try:
                # Check if we've exceeded the monitoring duration (2 minutes)
                current_time = time.time()
                elapsed_time = current_time - start_time
                
                if elapsed_time >= MONITORING_DURATION:
                    logger.info(f"Monitoring duration of {MONITORING_DURATION} seconds reached")
                    break
                
                # Receive frame size
                while len(data) < struct.calcsize("Q"):
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        logger.error("No data received from webcam server, retrying...")
                        time.sleep(1)
                        continue
                    data += packet
        
                if len(data) < struct.calcsize("Q"):
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
        
                # Detect lip dryness
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(60, 60))
                dryness_label = "Normal Lips"  # Default value if no lips detected
                normalized_texture = 0
            
                for (x, y, w, h) in faces:
                    face_roi = gray[y:y+h, x:x+w]
                    mouths = mouth_cascade.detectMultiScale(face_roi, scaleFactor=1.3, minNeighbors=8, minSize=(30, 30))
            
                    for (mx, my, mw, mh) in mouths:
                        if my < h / 2:
                            continue  # Ignore false positives from nose area
            
                        lips_roi = frame[y+my:y+my+mh, x+mx:x+mx+mw]
                        gray_lips = cv2.cvtColor(lips_roi, cv2.COLOR_BGR2GRAY)
                        
                        # Use Laplacian filter to detect texture - higher values indicate more texture (dryness)
                        laplacian = cv2.Laplacian(gray_lips, cv2.CV_64F)
                        texture_score = np.mean(np.abs(laplacian))
                        normalized_texture = min(1.0, texture_score / TEXTURE_THRESHOLD)
            
                        # Also analyze color - dry lips tend to be less red and more pale
                        hsv_lips = cv2.cvtColor(lips_roi, cv2.COLOR_BGR2HSV)
                        saturation = np.mean(hsv_lips[:,:,1])  # S channel in HSV
                        value = np.mean(hsv_lips[:,:,2])       # V channel in HSV
                        
                        # Combine texture and color analysis (this is how existing models determine dryness)
                        color_factor = 1.0 if saturation < 100 and value > 150 else 0.7
                        final_dryness_score = normalized_texture * color_factor
            
                        if final_dryness_score > DRYNESS_THRESHOLD:
                            dryness_label = "Dry Lips"
                            color = (0, 0, 255)  # Red
                        else:
                            dryness_label = "Normal Lips"
                            color = (0, 255, 0)  # Green
            
                        # Draw rectangle around lips and add label
                        cv2.rectangle(frame, (x+mx, y+my), (x+mx+mw, y+my+mh), color, 2)
                        cv2.putText(frame, dryness_label, (x+mx, y+my-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
                # Store lip dryness status for batch saving
                if current_time - last_saved_time >= save_interval:
                    # Save to database immediately
                    prediction_data = {
                        'hydration_status': dryness_label,
                        'dryness_score': float(normalized_texture),
                        'timestamp': int(current_time * 1000)
                    }
                    
                    # Save prediction to database
                    db_manager.save_prediction('hydration', prediction_data)
                    
                    # Save to batch for statistics
                    lip_dryness_batch.append(dryness_label)
                    last_saved_time = current_time
                    
                    # Log progress
                    remaining_time = int(MONITORING_DURATION - elapsed_time)
                    if remaining_time % 10 == 0:  # Log every 10 seconds
                        logger.info(f"Hydration monitoring in progress: {elapsed_time:.0f}s elapsed, {remaining_time}s remaining")
            
            except Exception as e:
                logger.error(f"Error in frame processing loop: {e}")
                logger.error(traceback.format_exc())
                # Continue with the next frame
                continue
        
        # After 2 minutes, calculate and save final statistics
        if lip_dryness_batch:
            # Calculate percentage of dry lips
            total_samples = len(lip_dryness_batch)
            dry_count = lip_dryness_batch.count("Dry Lips")
            normal_count = lip_dryness_batch.count("Normal Lips")
            dry_percentage = (dry_count / total_samples) * 100 if total_samples > 0 else 0
            normal_percentage = (normal_count / total_samples) * 100 if total_samples > 0 else 0
            
            # Calculate average dryness score
            avg_dryness = sum([1.0 if label == "Dry Lips" else 0.0 for label in lip_dryness_batch]) / total_samples if total_samples > 0 else 0.0
            
            # Save summary to database
            summary_data = {
                'dry_lips_count': dry_count,
                'normal_lips_count': normal_count,
                'dry_lips_percentage': dry_percentage,
                'normal_lips_percentage': normal_percentage,
                'avg_dryness_score': avg_dryness,
                'total_samples': total_samples,
                'timestamp': int(time.time() * 1000)
            }
            
            # Save summary to database
            db_manager.save_monitoring_summary('hydration', summary_data)
            
            # Check if we should trigger an alert (>60% dry lips)
            if dry_percentage > 60:
                # Trigger hydration alert
                alert_message = f"Dehydration detected! Your lips appear dry {dry_percentage:.1f}% of the time. Please drink some water."
                db_manager.save_alert(
                    'hydration',
                    alert_message,
                    'warning',
                    {
                        'dry_lips_percentage': dry_percentage,
                        'normal_lips_percentage': normal_percentage,
                        'total_samples': total_samples,
                        'threshold': 60
                    }
                )
                logger.info(f"Hydration alert triggered: {dry_percentage:.1f}% dry lips detected")
            
            # Log final results
            logger.info(f"Hydration monitoring completed: {total_samples} samples collected")
            logger.info(f"Results: {dry_percentage:.1f}% dry lips, {normal_percentage:.1f}% normal lips")
    
    except KeyboardInterrupt:
        logger.info("Hydration monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error in hydration monitoring: {e}")
        logger.error(traceback.format_exc())
    finally:
        try:
            # Update user monitoring status
            if 'db_manager' in locals():
                db_manager.update_user_monitoring_status(False)
            
            # Close connections and windows
            if 'client_socket' in locals():
                client_socket.close()
            
            cv2.destroyAllWindows()
            logger.info("Hydration monitoring stopped")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
