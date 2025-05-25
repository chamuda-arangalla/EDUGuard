import cv2
import numpy as np
import socket
import struct
import pickle
import time
import sys
import os

# Add parent directory to path so we can import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.database import DatabaseManager

# ---------------------------
# Client Setup - Connect to Frame Server
# ---------------------------
HOST = '127.0.0.1'
PORT = 9999

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
data = b""

# ---------------------------
# Dry Lips Detection Settings
# ---------------------------
TEXTURE_THRESHOLD = 30     # Used to normalize the texture score
DRYNESS_THRESHOLD = 0.17   # If normalized score > 0.17, consider lips as dry

# Determine the absolute path to the model files
current_dir = os.path.dirname(os.path.abspath(__file__))
face_cascade_path = os.path.join(current_dir, "models", "haarcascade_frontalface_default.xml")
mouth_cascade_path = os.path.join(current_dir, "models", "haarcascade_mcs_mouth.xml")

# Check if model files exist
if not os.path.exists(face_cascade_path):
    print(f"Error: Face cascade file not found at {face_cascade_path}")
    sys.exit(1)

if not os.path.exists(mouth_cascade_path):
    print(f"Error: Mouth cascade file not found at {mouth_cascade_path}")
    sys.exit(1)

# Load Haar Cascade Models for Face and Mouth Detection
face_cascade = cv2.CascadeClassifier(face_cascade_path)
mouth_cascade = cv2.CascadeClassifier(mouth_cascade_path)

# Verify the classifiers loaded correctly
if face_cascade.empty():
    print("Error: Face cascade failed to load")
    sys.exit(1)
    
if mouth_cascade.empty():
    print("Error: Mouth cascade failed to load")
    sys.exit(1)

print(f"Successfully loaded cascade models from {current_dir}/models/")

# -------------------------------
# Get User Information from Arguments
# -------------------------------
if len(sys.argv) < 2:
    print("Error: Missing user email argument")
    sys.exit(1)

USER_EMAIL = sys.argv[1]
progress_report_id = sys.argv[2] if len(sys.argv) > 2 else None

# Import database utilities
try:
    # No need to import DatabaseManager again, we already did above
    db_manager = DatabaseManager(USER_EMAIL)
    print(f"Connected to database for user: {USER_EMAIL}")
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit(1)

# -------------------------------
# Timer Setup
# -------------------------------
save_interval = 1  # Save lip dryness status every 1 second
batch_interval = 30  # Save the batch to the database every 30 seconds
last_saved_time = time.time()
last_batch_time = time.time()
lip_dryness_batch = []  # Store lip dryness data before saving

# -------------------------------
# Function to Detect Lip Dryness using Texture Analysis
# -------------------------------
def detect_lip_dryness(frame):
    """
    Detect lips in the given frame and classify as 'Dry Lips' or 'Normal Lips'
    using texture analysis, which is a technique already used in the existing models.
    """
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

            cv2.rectangle(frame, (x+mx, y+my), (x+mx+mw, y+my+mh), color, 2)
            cv2.putText(frame, dryness_label, (x+mx, y+my-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    return frame, dryness_label, normalized_texture

# -------------------------------
# Process Frames for Lip Dryness Detection
# -------------------------------
data = b""

try:
    print(f"Starting hydration monitoring for user: {USER_EMAIL}")
    
    # Update user monitoring status
    db_manager.update_user_monitoring_status(True)
    
    while True:
        # Receive frame size
        while len(data) < struct.calcsize("Q"):
            packet = client_socket.recv(4 * 1024)
            if not packet:
                break
            data += packet

        packed_msg_size = data[:struct.calcsize("Q")]
        data = data[struct.calcsize("Q"):]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            data += client_socket.recv(4 * 1024)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        # Deserialize the frame
        frame = pickle.loads(frame_data)

        # 1) Detect lip dryness
        frame, lip_status, dryness_score = detect_lip_dryness(frame)

        # Store lip dryness status for batch saving
        current_time = time.time()
        if current_time - last_saved_time >= save_interval:
            # Save to database
            prediction_data = {
                'hydration_status': lip_status,
                'dryness_score': float(dryness_score),
                'timestamp': int(current_time * 1000)
            }
            
            # Save prediction to database
            db_manager.save_prediction('hydration', prediction_data)
            
            # Save to batch for alert checking
            lip_dryness_batch.append(lip_status)
            last_saved_time = current_time

        # Check for alerts every 30 seconds
        if current_time - last_batch_time >= batch_interval:
            if lip_dryness_batch:
                # Calculate percentage of dry lips
                total_samples = len(lip_dryness_batch)
                dry_count = lip_dryness_batch.count("Dry Lips")
                dry_percentage = (dry_count / total_samples) * 100 if total_samples > 0 else 0
                
                # Check if we should trigger an alert (>60% dry lips)
                hydration_avg = db_manager.calculate_prediction_average('hydration', minutes=5)
                
                if hydration_avg and hydration_avg.get('dry_lips_percentage', 0) > 60:
                    # Trigger hydration alert
                    alert_message = f"Dehydration detected! Your lips appear dry {hydration_avg['dry_lips_percentage']:.1f}% of the time. Please drink some water."
                    db_manager.save_alert(
                        'hydration',
                        alert_message,
                        'warning',
                        {
                            'dry_lips_percentage': hydration_avg['dry_lips_percentage'],
                            'normal_lips_percentage': hydration_avg['normal_lips_percentage'],
                            'total_samples': hydration_avg['total_samples']
                        }
                    )
                    print(f"Hydration alert triggered: {dry_percentage:.1f}% dry lips detected")
                
                # Clear batch after processing
                lip_dryness_batch = []
            last_batch_time = current_time

        # Display frame
        cv2.imshow("Lip Dryness Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Hydration monitoring stopped by user")
except Exception as e:
    print(f"Error in hydration monitoring: {e}")
finally:
    # Update user monitoring status
    db_manager.update_user_monitoring_status(False)
    
    # Close connections and windows
    client_socket.close()
    cv2.destroyAllWindows()
    print("Hydration monitoring stopped")
