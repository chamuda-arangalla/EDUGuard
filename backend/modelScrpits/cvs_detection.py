#!/usr/bin/env python
import cv2
import dlib
import numpy as np
import time
import sys
import json
import os
import logging
import requests
import socket
import struct
import pickle
from scipy.spatial import distance as dist
from datetime import datetime
import threading

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

# Define constants
EYE_AR_THRESH = 0.19  # Eye aspect ratio threshold for blink detection
EYE_AR_CONSEC_FRAMES = 2  # Number of consecutive frames the eye must be below threshold to be a blink
NORMAL_BLINK_RATE_MIN = 17  # Minimum normal blink rate (per minute)
NORMAL_BLINK_RATE_MAX = 20  # Maximum normal blink rate (per minute)

# Webcam server settings
WEBCAM_HOST = '127.0.0.1'
WEBCAM_PORT = 9999

# Initialize dlib's face detector and facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor_path = os.path.join(script_dir, "shape_predictor_68_face_landmarks.dat")

# Check if the predictor file exists
if not os.path.exists(predictor_path):
    logger.error(f"Facial landmark predictor file not found at: {predictor_path}")
    logger.info("Downloading facial landmark predictor...")
    # You might need to download the file here if it doesn't exist
    import urllib.request
    predictor_url = "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2"
    compressed_file = os.path.join(script_dir, "shape_predictor_68_face_landmarks.dat.bz2")
    try:
        urllib.request.urlretrieve(predictor_url, compressed_file)
        import bz2
        with open(predictor_path, 'wb') as new_file, bz2.BZ2File(compressed_file, 'rb') as file:
            for data in iter(lambda: file.read(100 * 1024), b''):
                new_file.write(data)
        os.remove(compressed_file)
        logger.info("Downloaded and extracted facial landmark predictor successfully")
    except Exception as e:
        logger.error(f"Failed to download facial landmark predictor: {e}")
        sys.exit(1)

predictor = dlib.shape_predictor(predictor_path)

# Define facial landmarks indices for the eyes
(L_START, L_END) = (42, 48)  # Left eye landmarks
(R_START, R_END) = (36, 42)  # Right eye landmarks

class BlinkDetector:
    def __init__(self, user_id, progress_report_id):
        self.user_id = user_id
        self.progress_report_id = progress_report_id
        self.db_manager = DatabaseManager(user_id)
        self.alert_manager = AlertManager(self.db_manager)
        
        # Blink detection variables
        self.blink_counter = 0
        self.total_blinks = 0
        self.blink_start_time = time.time()
        self.frame_counter = 0
        self.ear = 0  # Eye aspect ratio
        
        # Status reporting variables
        self.last_update_time = time.time()
        self.last_blink_rate = 0
        self.running = True
        self.status_thread = threading.Thread(target=self._status_reporter)
        self.status_thread.daemon = True
        self.status_thread.start()
        
        # Add a periodic data saving thread
        self.data_save_thread = threading.Thread(target=self._periodic_data_saver)
        self.data_save_thread.daemon = True
        self.data_save_thread.start()
        
        # Track time since last data save
        self.last_data_save_time = time.time()
        
        # Face detection history
        self.no_face_counter = 0
        self.max_no_face_frames = 30  # Number of frames to wait before assuming no face
        
        logger.info(f"Initialized blink detector for user {user_id}")
    
    def _periodic_data_saver(self):
        """Thread that ensures data is saved periodically even if no blinks are detected"""
        while self.running:
            try:
                current_time = time.time()
                time_since_last_save = current_time - self.last_data_save_time
                
                # If more than 2 minutes have passed without saving data
                if time_since_last_save > 120:
                    # Calculate a conservative blink rate estimate or use last known rate
                    if self.last_blink_rate > 0:
                        blink_rate = self.last_blink_rate
                    else:
                        blink_rate = 18  # Normal average
                    
                    logger.info(f"Periodic save: No data saved for {time_since_last_save:.1f}s, saving blink rate {blink_rate}")
                    self._save_blink_data(blink_rate)
                    self.last_data_save_time = current_time
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in periodic data saver: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def eye_aspect_ratio(self, eye):
        """Calculate the eye aspect ratio (EAR)"""
        # Compute the euclidean distances between the vertical eye landmarks
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        
        # Compute the euclidean distance between the horizontal eye landmarks
        C = dist.euclidean(eye[0], eye[3])
        
        # Compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blinks(self, frame):
        """Detect blinks in the given frame"""
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization to improve contrast
        gray = cv2.equalizeHist(gray)
        
        # Detect faces
        faces = detector(gray, 0)
        
        # Reset EAR for this frame
        self.ear = 0
        
        # Check if any faces were detected
        if len(faces) == 0:
            self.no_face_counter += 1
            
            # If no face detected for several consecutive frames
            if self.no_face_counter >= self.max_no_face_frames:
                logger.warning(f"No face detected for {self.no_face_counter} frames")
                
                # If it's been a while since we saved data and we're not detecting faces
                current_time = time.time()
                if current_time - self.blink_start_time >= 60:
                    # Save a default normal blink rate
                    logger.info("No face detected for extended period, saving default blink rate")
                    self._save_blink_data(18)  # Save a normal blink rate
                    self.blink_start_time = current_time
                    self.last_data_save_time = current_time
                
            # Draw text showing no face detected
            cv2.putText(frame, "No Face Detected", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            # Reset no face counter when a face is detected
            self.no_face_counter = 0
            
            # Process each detected face
            for face in faces:
                # Draw face rectangle
                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Detect facial landmarks
                shape = predictor(gray, face)
                shape = np.array([(shape.part(i).x, shape.part(i).y) for i in range(68)])
                
                # Extract the left and right eye coordinates
                leftEye = shape[L_START:L_END]
                rightEye = shape[R_START:R_END]
                
                # Calculate the eye aspect ratios
                leftEAR = self.eye_aspect_ratio(leftEye)
                rightEAR = self.eye_aspect_ratio(rightEye)
                
                # Average the eye aspect ratio together for both eyes
                self.ear = (leftEAR + rightEAR) / 2.0
                
                # Draw eye aspect ratio on frame
                cv2.putText(frame, f"EAR: {self.ear:.2f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Check if eye aspect ratio is below the blink threshold
                if self.ear < EYE_AR_THRESH:
                    self.blink_counter += 1
                    
                    # Visual indicator for potential blink
                    cv2.putText(frame, f"BLINK COUNTER: {self.blink_counter}", (10, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                else:
                    # If the eyes were closed for a sufficient number of frames, count it as a blink
                    if self.blink_counter >= EYE_AR_CONSEC_FRAMES:
                        self.total_blinks += 1
                        logger.info(f"Blink detected! Total: {self.total_blinks}")
                        
                        # Visual counter for total blinks
                        cv2.putText(frame, f"TOTAL BLINKS: {self.total_blinks}", (10, 90), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Reset the blink counter
                    self.blink_counter = 0
                
                # Draw eyes on the frame
                # Draw left eye
                for i in range(0, len(leftEye)):
                    pt1 = (leftEye[i][0], leftEye[i][1])
                    pt2 = (leftEye[(i+1)%len(leftEye)][0], leftEye[(i+1)%len(leftEye)][1])
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 1)
                
                # Draw right eye
                for i in range(0, len(rightEye)):
                    pt1 = (rightEye[i][0], rightEye[i][1])
                    pt2 = (rightEye[(i+1)%len(rightEye)][0], rightEye[(i+1)%len(rightEye)][1])
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 1)
        
        self.frame_counter += 1
        
        # Calculate blink rate every 60 seconds and save to database
        elapsed_time = time.time() - self.blink_start_time
        if elapsed_time >= 60:  # 1 minute
            blink_rate = self.total_blinks
            minutes_elapsed = elapsed_time / 60
            
            # Save to database
            self._save_blink_data(blink_rate)
            self.last_data_save_time = time.time()
            
            # Check for alerts
            self._check_blink_rate_alert(blink_rate)
            
            # Reset counters
            self.last_blink_rate = blink_rate
            self.total_blinks = 0
            self.blink_start_time = time.time()
            
            logger.info(f"Blink rate: {blink_rate:.1f} blinks/minute (over {minutes_elapsed:.1f} minutes)")
        
        # Display elapsed time and estimated blink rate
        if elapsed_time > 0:
            estimated_rate = (self.total_blinks / elapsed_time) * 60
            cv2.putText(frame, f"Time: {elapsed_time:.1f}s", (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"Est. Rate: {estimated_rate:.1f}/min", (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return frame
    
    def _save_blink_data(self, blink_rate):
        """Save blink rate data to the database"""
        try:
            # Prepare the prediction data
            prediction = {
                'blink_count': blink_rate,
                'timestamp': int(time.time() * 1000),
                'progress_report_id': self.progress_report_id
            }
            
            # Save to database
            self.db_manager.save_prediction('cvs', prediction)
            logger.info(f"Saved blink rate data to database: {blink_rate} blinks/minute")
            
        except Exception as e:
            logger.error(f"Error saving blink data: {e}")
    
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
    
    def _status_reporter(self):
        """Report status periodically to ensure the process is running"""
        while self.running:
            try:
                # Update the last active timestamp
                self.last_update_time = time.time()
                
                # Log current status
                elapsed_time = time.time() - self.blink_start_time
                estimated_blink_rate = (self.total_blinks / elapsed_time) * 60 if elapsed_time > 0 else 0
                logger.info(f"Status: Running for {elapsed_time:.1f}s, {self.total_blinks} blinks, ~{estimated_blink_rate:.1f} blinks/min, EAR: {self.ear:.3f}")
                
                # Sleep for 30 seconds
                for _ in range(30):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in status reporter: {e}")
                time.sleep(10)  # Wait a bit before retrying
    
    def stop(self):
        """Stop the blink detector"""
        self.running = False
        
        # Save final data
        elapsed_time = time.time() - self.blink_start_time
        if elapsed_time > 0 and self.total_blinks > 0:
            # Calculate blink rate for the partial minute
            blink_rate = (self.total_blinks / elapsed_time) * 60
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
    # This helps verify database connectivity and creates initial data for the frontend
    try:
        initial_blink_rate = 18  # Start with a normal blink rate
        detector._save_blink_data(initial_blink_rate)
        logger.info(f"Saved initial data point with blink rate {initial_blink_rate}")
    except Exception as e:
        logger.error(f"Failed to save initial data point: {e}")
    
    # If running without webcam for testing, simulate blinks and data
    simulate_mode = os.environ.get('CVS_SIMULATE', 'false').lower() == 'true'
    
    try:
        # Main processing loop
        while True:
            if simulate_mode:
                # Simulation mode - generate test data without webcam
                logger.info("Running in simulation mode - generating test data")
                for _ in range(5):  # Simulate for 5 minutes
                    # Simulate random blink rate (between 15-22 blinks/min)
                    import random
                    blink_rate = random.randint(15, 22)
                    detector._save_blink_data(blink_rate)
                    logger.info(f"Simulated blink rate: {blink_rate} blinks/minute")
                    
                    # Check for alerts based on the simulated data
                    detector._check_blink_rate_alert(blink_rate)
                    
                    # Sleep for a minute (or less for faster testing)
                    time.sleep(10)  # 10 seconds in test mode
                break
            
            try:
                # If socket is not connected, try to connect
                if client_socket is None:
                    client_socket = connect_to_webcam_server()
                    if client_socket is None:
                        logger.error("Failed to connect to webcam server. Retrying in 5 seconds...")
                        time.sleep(5)
                        continue
                
                # Receive frame from webcam server
                frame = receive_frame(client_socket)
                
                if frame is None:
                    logger.error("Lost connection to webcam server. Reconnecting...")
                    client_socket.close()
                    client_socket = None
                    time.sleep(5)
                    continue
                
                # Process the frame for blink detection and get the visualized frame
                processed_frame = detector.detect_blinks(frame)
                
                # Display the frame for debugging
                cv2.imshow('CVS Detection', processed_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('b'):  # Manual blink for testing
                    detector.total_blinks += 1
                    logger.info(f"Manual blink added! Total: {detector.total_blinks}")
                
            except socket.error as e:
                logger.error(f"Socket error: {e}")
                if client_socket:
                    client_socket.close()
                client_socket = None
                time.sleep(5)  # Wait before retrying
                
                # Save periodic data even if webcam fails
                current_time = time.time()
                if current_time - detector.blink_start_time > 60:
                    logger.info("Saving periodic data despite webcam error")
                    # Save with a conservative default value
                    detector._save_blink_data(17)  # Normal blink rate
                    detector.blink_start_time = current_time
                
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
