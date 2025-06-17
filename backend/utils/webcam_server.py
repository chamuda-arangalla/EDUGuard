import socket
import pickle
import struct
import cv2
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('WebcamServer')

class WebcamServer:
    def __init__(self, host='127.0.0.1', port=9999, camera_id=0):
        """Initialize the webcam server.
        
        Args:
            host (str): The host address to bind the server to.
            port (int): The port to bind the server to.
            camera_id (int): The camera device ID to use.
        """
        self.host = host
        self.port = port
        self.camera_id = camera_id
        self.server_socket = None
        self.connections = []
        self.running = False
        
    def start(self):
        """Start the webcam server."""
        # Create socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            # Bind socket
            self.server_socket.bind((self.host, self.port))
            
            # Listen for connections
            self.server_socket.listen(5)
            logger.info(f"Webcam server started on {self.host}:{self.port}")
            
            # Set running flag
            self.running = True
            
            # Start connection acceptance thread
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Start webcam streaming
            self._stream_webcam()
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            self.stop()
    
    def _accept_connections(self):
        """Accept incoming connections."""
        logger.info("Waiting for connections...")
        
        while self.running:
            try:
                # Accept client connection
                client_socket, addr = self.server_socket.accept()
                logger.info(f"Connection from {addr}")
                
                # Add to connections list
                self.connections.append(client_socket)
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.error(f"Error accepting connection: {e}")
                break
    
    def _stream_webcam(self):
        """Stream webcam frames to connected clients."""
        # Open webcam
        cap = cv2.VideoCapture(self.camera_id)
        
        if not cap.isOpened():
            logger.error("Failed to open webcam")
            self.stop()
            return
        
        logger.info("Webcam opened successfully")
        
        try:
            while self.running:
                # Capture frame
                ret, frame = cap.read()
                
                if not ret:
                    logger.error("Failed to capture frame")
                    # Try to reopen the camera
                    cap.release()
                    time.sleep(1)
                    cap = cv2.VideoCapture(self.camera_id)
                    continue
                
                # Serialize frame
                data = pickle.dumps(frame)
                message_size = struct.pack("Q", len(data))
                
                # Send to all clients
                disconnected = []
                for i, client_socket in enumerate(self.connections):
                    try:
                        client_socket.sendall(message_size + data)
                    except Exception as e:
                        logger.warning(f"Error sending to client {i}: {e}")
                        disconnected.append(client_socket)
                
                # Remove disconnected clients
                for client_socket in disconnected:
                    if client_socket in self.connections:
                        self.connections.remove(client_socket)
                        try:
                            client_socket.close()
                        except:
                            pass
                
                # Display frame (for debugging)
                cv2.imshow('Server View', frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                
                # Sleep to control frame rate
                time.sleep(0.03)  # ~30 FPS
                
        except Exception as e:
            logger.error(f"Error in webcam streaming: {e}")
        finally:
            # Release resources
            cap.release()
            cv2.destroyAllWindows()
            self.stop()
    
    def stop(self):
        """Stop the webcam server."""
        self.running = False
        
        # Close all client connections
        for client_socket in self.connections:
            try:
                client_socket.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("Webcam server stopped")

if __name__ == "__main__":
    # Create and start webcam server
    server = WebcamServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        server.stop() 