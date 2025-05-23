import cv2
import time
import json
import os
import argparse
from threading import Thread
import logging
from dotenv import load_dotenv

# Local imports
from models import ModelManager
from utils.database import DatabaseManager
from utils.alert_manager import AlertManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EDUGuard')

# Load environment variables
load_dotenv()

class MonitoringApp:
    """Main EDUGuard application for monitoring and analysis."""
    
    def __init__(self, user_id=None):
        """Initialize the monitoring application.
        
        Args:
            user_id (str, optional): The user ID for database operations.
                If None, will use the one from environment variables.
        """
        # Load configuration
        self.load_config()
        
        # Set up the user ID
        self.user_id = user_id or os.getenv('USER_ID')
        if not self.user_id:
            raise ValueError("User ID is required. Provide it as an argument or set USER_ID environment variable.")
            
        logger.info(f"Initializing monitoring for user {self.user_id}")
        
        # Initialize models
        self.model_manager = ModelManager(
            emotion_model_path=self.config.get('emotion_model_path')
        )
        
        # Initialize database
        self.db_manager = DatabaseManager(self.user_id)
        
        # Initialize alert manager
        self.alert_manager = AlertManager(self.db_manager)
        
        # Set up the webcam
        self.camera_index = self.config.get('camera_index', 0)
        self.cap = None
        self.running = False
        self.monitoring_thread = None
        
        # Tracking
        self.frame_count = 0
        self.last_alert_check = 0
        self.alert_check_interval = self.config.get('alert_check_interval', 15)  # seconds
        
    def load_config(self):
        """Load application configuration."""
        config_path = os.getenv('CONFIG_PATH', 'config.json')
        
        # Default configuration
        self.config = {
            'camera_index': 0,
            'capture_interval': 0.1,  # seconds between frame captures
            'prediction_interval': 0.5,  # seconds between predictions
            'alert_check_interval': 15,  # seconds between alert checks
            'database_sync_interval': 5,  # seconds between database syncs
            'emotion_model_path': None,
            'frame_width': 640,
            'frame_height': 480
        }
        
        # Load from file if exists
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        else:
            logger.info(f"No configuration file found at {config_path}, using defaults")
    
    def start(self):
        """Start the monitoring process."""
        if self.running:
            logger.warning("Monitoring is already running")
            return
            
        logger.info("Starting monitoring")
        
        # Set status flag
        self.running = True
        
        # Update the database status
        self.db_manager.update_user_monitoring_status(True)
        
        # Start the monitoring thread
        self.monitoring_thread = Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("Monitoring started")
    
    def stop(self):
        """Stop the monitoring process."""
        if not self.running:
            logger.warning("Monitoring is not running")
            return
            
        logger.info("Stopping monitoring")
        
        # Set status flag
        self.running = False
        
        # Wait for thread to finish
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
            
        # Release the camera
        if self.cap:
            self.cap.release()
            self.cap = None
            
        # Update the database status
        self.db_manager.update_user_monitoring_status(False)
        
        logger.info("Monitoring stopped")
    
    def _init_camera(self):
        """Initialize the camera."""
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.get('frame_width', 640))
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.get('frame_height', 480))
            
            # Check if camera opened successfully
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera with index {self.camera_index}")
                
            logger.info(f"Camera initialized with index {self.camera_index}")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        try:
            self._init_camera()
            
            last_capture_time = 0
            last_db_sync_time = 0
            
            while self.running:
                # Capture at specified interval
                current_time = time.time()
                if current_time - last_capture_time < self.config.get('capture_interval', 0.1):
                    time.sleep(0.01)  # Small sleep to prevent CPU spin
                    continue
                    
                last_capture_time = current_time
                
                # Capture frame from webcam
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.1)
                    continue
                    
                self.frame_count += 1
                
                # Process the frame through all models
                predictions = self.model_manager.process_frame(frame)
                
                # Save predictions to the database
                for model_name, prediction in predictions.items():
                    if prediction:
                        self.db_manager.save_prediction(model_name, prediction)
                
                # Check for alerts periodically
                if current_time - self.last_alert_check >= self.alert_check_interval:
                    self.last_alert_check = current_time
                    self.alert_manager.check_all_alerts()
                    
                # Sync database status periodically
                if current_time - last_db_sync_time >= self.config.get('database_sync_interval', 5):
                    last_db_sync_time = current_time
                    self.db_manager.update_user_monitoring_status(True)
                    
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
            self.running = False
            
        finally:
            # Release the camera
            if self.cap:
                self.cap.release()
                self.cap = None
                
            # Update status
            try:
                self.db_manager.update_user_monitoring_status(False)
            except Exception as e:
                logger.error(f"Error updating status: {e}")
                
            logger.info("Monitoring loop terminated")

def main():
    """Main function to start the application."""
    parser = argparse.ArgumentParser(description="EDUGuard Monitoring Application")
    parser.add_argument('--user-id', type=str, help="User ID for database operations")
    parser.add_argument('--config', type=str, help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Set config path if provided
    if args.config:
        os.environ['CONFIG_PATH'] = args.config
    
    try:
        # Initialize and start the application
        app = MonitoringApp(user_id=args.user_id)
        app.start()
        
        # Keep running until interrupted
        try:
            while app.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            app.stop()
            
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main()) 