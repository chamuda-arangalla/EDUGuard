import cv2
import mediapipe as mp
import numpy as np
import joblib
import socket
import struct
import pickle
import time
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SimplePostureDetection')

# Get command line arguments
if len(sys.argv) < 3:
    logger.error("Error: Missing arguments (user_id, progress_report_id)")
    sys.exit(1)

USER_ID = sys.argv[1]
PROGRESS_REPORT_ID = sys.argv[2]

logger.info(f"Starting posture detection for user: {USER_ID}")

# Initialize database manager
db_manager = DatabaseManager(USER_ID)

# Load the posture model
try:
    model_path = './models/posture_classifier.pkl'
    if not os.path.exists(model_path):
        model_path = '../models/posture_classifier.pkl'
    
    model = joblib.load(model_path)
    logger.info(f"Loaded posture model from: {model_path}")
except Exception as e:
    logger.error(f"Error loading posture model: {e}")
    sys.exit(1)

# Webcam server connection
HOST = '127.0.0.1'
PORT = 9999

# Mediapipe setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Helper function to ensure log messages are safe for all consoles
def safe_log(message):
    """Replace emoji characters with text alternatives"""
    return message

def calculate_angle(vector1, vector2):
    """Calculate angle between two vectors"""
    dot_product = np.dot(vector1, vector2)
    magnitude1 = np.linalg.norm(vector1)
    magnitude2 = np.linalg.norm(vector2)
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    
    cos_angle = dot_product / (magnitude1 * magnitude2)
    # Clamp to valid range for arccos
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    
    return np.degrees(np.arccos(cos_angle))

def save_posture_data(posture):
    """Save posture data to Firebase database"""
    try:
        timestamp = int(time.time() * 1000)
        prediction_data = {
            'posture': posture,
            'timestamp': timestamp,
            'user_id': USER_ID
        }
        
        # Save to database
        key = db_manager.save_prediction('posture', prediction_data, timestamp)
        
        if key:
            logger.info(f"[OK] Saved posture data: {posture}")
            
            # Check for bad posture alert
            if posture == "Bad Posture":
                # Check recent posture data for alert
                recent_predictions = db_manager.get_recent_predictions('posture', minutes=2)
                if len(recent_predictions) >= 3:
                    bad_count = sum(1 for p in recent_predictions[-3:] 
                                  if p.get('prediction', {}).get('posture') == 'Bad Posture')
                    
                    if bad_count >= 2:  # 2 out of last 3 are bad
                        db_manager.save_alert(
                            'posture',
                            'Poor posture detected! Please adjust your sitting position.',
                            'warning',
                            {'consecutive_bad_postures': bad_count}
                        )
        else:
            logger.warning("Failed to save posture data")
            
    except Exception as e:
        logger.error(f"Error saving posture data: {e}")

def main():
    """Main posture detection function"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data = b""
    
    try:
        # Connect to webcam server
        logger.info(f"Connecting to webcam server at {HOST}:{PORT}")
        client_socket.connect((HOST, PORT))
        logger.info("[OK] Connected to webcam server")
        
        # Update monitoring status
        db_manager.update_user_monitoring_status(True)
        
        # Timing variables
        last_save_time = time.time()
        save_interval = 3  # Save every 3 seconds
        frame_count = 0
        
        logger.info("[CAMERA] Starting posture detection...")
        
        while True:
            try:
                # Receive frame size
                while len(data) < struct.calcsize("Q"):
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        logger.warning("No data received from webcam server")
                        break
                    data += packet

                if len(data) < struct.calcsize("Q"):
                    break

                packed_msg_size = data[:struct.calcsize("Q")]
                data = data[struct.calcsize("Q"):]
                msg_size = struct.unpack("Q", packed_msg_size)[0]

                # Receive frame data
                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)

                frame_data = data[:msg_size]
                data = data[msg_size:]

                # Deserialize frame
                frame = pickle.loads(frame_data)
                frame_count += 1

                # Process frame with Mediapipe
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image_rgb)

                posture = "Unknown"
                
                if results.pose_landmarks:
                    # Extract keypoints
                    landmarks = results.pose_landmarks.landmark
                    
                    # Get shoulder and nose positions
                    left_shoulder = (landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                   landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y)
                    right_shoulder = (landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                                    landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y)
                    nose = (landmarks[mp_pose.PoseLandmark.NOSE.value].x,
                           landmarks[mp_pose.PoseLandmark.NOSE.value].y)

                    # Convert to pixel coordinates
                    h, w, _ = frame.shape
                    left_shoulder = (int(left_shoulder[0] * w), int(left_shoulder[1] * h))
                    right_shoulder = (int(right_shoulder[0] * w), int(right_shoulder[1] * h))
                    nose = (int(nose[0] * w), int(nose[1] * h))

                    # Calculate vectors
                    green_line = np.array(right_shoulder) - np.array(left_shoulder)
                    red_line = np.array([1, 0])  # Horizontal reference
                    shoulder_center = [(left_shoulder[0] + right_shoulder[0]) / 2,
                                     (left_shoulder[1] + right_shoulder[1]) / 2]
                    blue_line = np.array(nose) - np.array(shoulder_center)

                    # Calculate angles
                    angle_red_green = calculate_angle(red_line, green_line)
                    angle_blue_green = calculate_angle(blue_line, green_line)

                    # Predict posture using the model
                    features = np.array([[angle_red_green, angle_blue_green]])
                    prediction = model.predict(features)
                    posture = "Good Posture" if prediction[0] == 1 else "Bad Posture"

                    # Draw pose landmarks
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # Display results on frame
                # color = (0, 255, 0) if posture == "Good Posture" else (0, 0, 255)
                # cv2.putText(frame, f"Posture: {posture}", (50, 50),
                #            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
                
                # cv2.putText(frame, f"User: {USER_ID}", (50, 100),
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                
                # cv2.putText(frame, f"Frames: {frame_count}", (50, 130),
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

                # Save posture data at intervals
                current_time = time.time()
                if current_time - last_save_time >= save_interval and posture != "Unknown":
                    save_posture_data(posture)
                    last_save_time = current_time

                # Display frame
                # cv2.imshow(f"EDUGuard Posture Detection - {USER_ID}", frame)
                
                # # Check for quit
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     logger.info("Quit signal received")
                #     break

            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                continue

    except Exception as e:
        logger.error(f"Error in posture detection: {e}")
    finally:
        # Cleanup
        db_manager.update_user_monitoring_status(False)
        
        try:
            client_socket.close()
            cv2.destroyAllWindows()
        except:
            pass
        
        logger.info("[STOP] Posture detection stopped")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Posture detection interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        # Final cleanup
        try:
            db_manager.update_user_monitoring_status(False)
        except:
            pass 