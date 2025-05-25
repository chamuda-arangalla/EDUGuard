import cv2
import socket
import struct
import pickle
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('WebcamServer')

# Socket setup
HOST = '127.0.0.1'  
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)  # Allow multiple clients
logger.info(f"Webcam server started on {HOST}:{PORT}. Waiting for connections...")

# Open webcam with improved settings
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    logger.error("Error: Could not open webcam.")
    server_socket.close()
    exit(1)

# Set webcam properties for better quality
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)  # Increase brightness for better face detection
cap.set(cv2.CAP_PROP_CONTRAST, 150)    # Increase contrast for better feature detection

# Get actual webcam properties
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = cap.get(cv2.CAP_PROP_FPS)
logger.info(f"Webcam initialized with resolution: {width}x{height}, FPS: {fps}")

# Function to handle client connections
def handle_client(client_socket, address):
    logger.info(f"New connection from: {address}")
    frame_count = 0
    start_time = time.time()
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                logger.error("Error: Failed to capture frame from webcam.")
                break

            # Process frame to improve face detection
            # 1. Apply brightness/contrast adjustment if needed
            # frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=10)
            
            # 2. Resize if needed (smaller for faster transmission, larger for better detection)
            # frame = cv2.resize(frame, (640, 480))
            
            # Serialize the frame
            data = pickle.dumps(frame, protocol=pickle.HIGHEST_PROTOCOL)
            message = struct.pack("Q", len(data)) + data

            try:
                client_socket.sendall(message)
                frame_count += 1
                
                # Log performance every 100 frames
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    logger.info(f"Sent {frame_count} frames at {fps:.2f} FPS to {address}")
                
            except BrokenPipeError:
                logger.info(f"Client {address} disconnected.")
                break
    except Exception as e:
        logger.error(f"Error handling client {address}: {e}")
    finally:
        client_socket.close()
        logger.info(f"Connection closed for {address}")

# Accept multiple clients
try:
    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.daemon = True
        client_thread.start()
except KeyboardInterrupt:
    logger.info("Shutting down server due to KeyboardInterrupt.")
finally:
    cap.release()
    server_socket.close()
    logger.info("Server shut down.")
