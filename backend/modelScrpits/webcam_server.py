import cv2
import socket
import struct
import pickle
import threading

# Socket setup
HOST = '127.0.0.1'  
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)  # Allow multiple clients
print("Webcam server started. Waiting for connections...")

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    server_socket.close()
    exit(1)

# Function to handle client connections
def handle_client(client_socket, address):
    print(f"New connection from: {address}")
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame from webcam.")
                break

            # Serialize the frame
            data = pickle.dumps(frame, protocol=pickle.HIGHEST_PROTOCOL)
            message = struct.pack("Q", len(data)) + data

            try:
                client_socket.sendall(message)
            except BrokenPipeError:
                print(f"Client {address} disconnected.")
                break
    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        client_socket.close()

# Accept multiple clients
try:
    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()
except KeyboardInterrupt:
    print("Shutting down server due to KeyboardInterrupt.")
finally:
    cap.release()
    server_socket.close()
    print("Server shut down.")
