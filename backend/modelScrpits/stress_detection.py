import cv2
import numpy as np
import time
import socket
import struct
import pickle
import sys
import os
import logging
from keras.models import load_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('StressDetection')

# Add the parent directory to the path so we can import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import DatabaseManager
from utils.alert_manager import AlertManager

# Define stress thresholds for alerts
HIGH_STRESS_THRESHOLD = 0.7
STRESS_CHECK_INTERVAL = 60  # seconds

# Get the authenticated user email from command-line arguments
if len(sys.argv) < 2:
    logger.error("Error: No user ID provided as an argument.")
    sys.exit(1)

USER_ID = sys.argv[1]  # Get user ID from the arguments
progress_report_id = sys.argv[2] if len(sys.argv) > 2 else None

logger.info(f"Starting stress detection for user {USER_ID}, report {progress_report_id}")

# Define paths relative to the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, 'models', 'model_file_30epochs.h5')
FACE_CASCADE_PATH = os.path.join(SCRIPT_DIR, 'models', 'haarcascade_frontalface_default.xml')

logger.info(f"Looking for model at: {MODEL_PATH}")

# Load the model
try:
    model = load_model(MODEL_PATH)
    logger.info(f"Model loaded from {MODEL_PATH}")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    sys.exit(1)

# Load face detector
try:
    faceDetect = cv2.CascadeClassifier(FACE_CASCADE_PATH)
    if faceDetect.empty():
        # Fallback to OpenCV's built-in cascades
        faceDetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        logger.info("Using OpenCV's built-in face cascade")
    else:
        logger.info(f"Face detector loaded from {FACE_CASCADE_PATH}")
except Exception as e:
    logger.error(f"Error loading face detector: {e}")
    sys.exit(1)

# Define labels for stress detection
labels_dict = {0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Neutral', 5: 'Sad', 6: 'Surprise'}

# Connect to the webcam server
HOST = '127.0.0.1'
PORT = 9999

# Initialize database and alert managers
try:
    db_manager = DatabaseManager(USER_ID)
    alert_manager = AlertManager(db_manager)
    logger.info(f"Database and alert managers initialized for user {USER_ID}")
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    db_manager = None
    alert_manager = None

# Function to map emotions to stress levels
def map_emotion_to_stress(emotion):
    """Map detected emotion to stress level value"""
    if emotion in ['Angry', 'Fear', 'Sad']:
        return 0.8  # High stress
    elif emotion == 'Disgust':
        return 0.6  # Medium stress
    elif emotion == 'Surprise':
        return 0.4  # Low-medium stress
    else:  # Happy or Neutral
        return 0.2  # Low stress

# Function to save stress data to database
def save_stress_data(emotions, progress_report_id):
    """Save stress data to the database with retry logic"""
    if not db_manager:
        logger.warning("Database manager not available. Cannot save data.")
        return False
    
    if not emotions:
        logger.warning("No emotions to save.")
        return False
    
    try:
        # Calculate average stress level from emotions
        stress_values = [map_emotion_to_stress(emotion) for emotion in emotions]
        avg_stress = sum(stress_values) / len(stress_values) if stress_values else 0
        
        # Map numerical stress value to categorical value for dashboard
        stress_category = "Low Stress"
        if avg_stress >= 0.7:
            stress_category = "High Stress"
        elif avg_stress >= 0.4:
            stress_category = "Medium Stress"
        
        # Create prediction data in the exact format expected by the dashboard
        prediction = {
            'stress_level': stress_category,  # Use category string instead of numerical value
            'numerical_stress': avg_stress,   # Keep numerical value for reference
            'emotions': emotions,
            'timestamp': int(time.time() * 1000),
            'progress_report_id': progress_report_id
        }
        
        # Save to database with retry logic
        for attempt in range(3):
            try:
                key = db_manager.save_prediction('stress', prediction)
                if key:
                    logger.info(f"Saved stress data to database: {stress_category} ({avg_stress:.2f}) from {len(emotions)} readings")
                    return True
                else:
                    logger.warning(f"Database save returned None on attempt {attempt+1}")
            except Exception as e:
                logger.error(f"Error saving stress data (attempt {attempt+1}/3): {e}")
                if attempt < 2:  # Only sleep if we're going to retry
                    time.sleep(2)
        
        logger.error("All 3 attempts to save data failed")
        return False
        
    except Exception as e:
        logger.error(f"Error preparing stress data: {e}")
        return False

# Function to check stress level and trigger alerts if needed
def check_stress_alert(alert_manager, stress_level, progress_report_id):
    """Check if stress level should trigger an alert"""
    try:
        # We're now using categorical stress levels for consistency with the dashboard
        if stress_level == "High Stress":
            # High stress detected
            alert_manager.trigger_immediate_alert(
                'stress', 
                f"High stress level detected",
                'warning',
                {
                    'stress_level': stress_level,
                    'progress_report_id': progress_report_id,
                    'threshold': HIGH_STRESS_THRESHOLD
                }
            )
            logger.warning(f"High stress alert triggered: {stress_level}")
        
    except Exception as e:
        logger.error(f"Error checking stress alert: {e}")

# Function to connect to webcam server
def connect_to_webcam_server():
    """Connect to the webcam server socket"""
    try:
        # Create socket connection
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        logger.info(f"Connected to webcam server at {HOST}:{PORT}")
        return client_socket
    except Exception as e:
        logger.error(f"Failed to connect to webcam server: {e}")
        return None

def main():
    """Main function to run the stress detection"""
    # Connect to webcam server
    client_socket = connect_to_webcam_server()
    if not client_socket:
        logger.error("Failed to connect to webcam server. Exiting...")
        sys.exit(1)
    
    data = b""  # Buffer for receiving data
    
    # Timer setup
    last_saved_time = time.time()
    last_batch_time = time.time()
    save_interval = 1  # Save data every 1 second
    batch_interval = 30  # Save the batch to the database every 30 seconds
    current_batch = []  # Temporary list to store data for the current batch
    
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
                
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = faceDetect.detectMultiScale(gray, 1.3, 3)
                
                # Store detected emotions for this frame
                frame_emotions = []
                
                for x, y, w, h in faces:
                    sub_face_img = gray[y:y+h, x:x+w]
                    resized = cv2.resize(sub_face_img, (48, 48))
                    normalized = resized / 255.0
                    reshaped = np.reshape(normalized, (1, 48, 48, 1))
                    
                    # Predict emotion
                    result = model.predict(reshaped, verbose=0)
                    label = np.argmax(result, axis=1)[0]
                    detected_emotion = labels_dict[label]
                    frame_emotions.append(detected_emotion)
                    
                    # Draw the detected face and label on the frame
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 1)
                    cv2.rectangle(frame, (x, y - 40), (x + w, y), (50, 50, 255), -1)
                    cv2.putText(frame, detected_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    
                    # Log the detected emotion
                    logger.debug(f"Detected emotion: {detected_emotion}")
                
                # Add emotions to batch
                if frame_emotions:
                    current_time = time.time()
                    if current_time - last_saved_time >= save_interval:
                        current_batch.extend(frame_emotions)
                        last_saved_time = current_time
                        logger.debug(f"Added {len(frame_emotions)} emotions to batch. Batch size: {len(current_batch)}")
                
                # Save the batch to the database every batch_interval seconds
                current_time = time.time()
                if current_time - last_batch_time >= batch_interval and current_batch:
                    logger.info(f"Saving batch of {len(current_batch)} emotions to database")
                    
                    # Save batch to database
                    if save_stress_data(current_batch, progress_report_id):
                        # If save successful and we have an alert manager, check for stress alerts
                        if alert_manager:
                            # Calculate average stress for alert check
                            stress_values = [map_emotion_to_stress(emotion) for emotion in current_batch]
                            avg_stress = sum(stress_values) / len(stress_values) if stress_values else 0
                            
                            # Map numerical stress value to categorical value for alerts
                            stress_category = "Low Stress"
                            if avg_stress >= 0.7:
                                stress_category = "High Stress"
                            elif avg_stress >= 0.4:
                                stress_category = "Medium Stress"
                                
                            check_stress_alert(alert_manager, stress_category, progress_report_id)
                    
                    # Clear batch after saving
                    current_batch = []
                    last_batch_time = current_time
                
                # Show the frame
                # cv2.imshow(f"Stress Detection - {USER_ID}", frame)
                # key = cv2.waitKey(1) & 0xFF  # Use waitKey(1) for more responsive display
                # if key == ord('q'):
                #     break
                
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
        logger.info("Stress detection stopped by user")
    finally:
        # Save any remaining data
        if current_batch:
            logger.info(f"Saving {len(current_batch)} remaining emotion readings")
            save_stress_data(current_batch, progress_report_id)
            
        # Clean up
        if client_socket:
            client_socket.close()
        cv2.destroyAllWindows()
        logger.info("Stress detection ended")

if __name__ == "__main__":
    main()
