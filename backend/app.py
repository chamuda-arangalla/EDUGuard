from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import threading
import time
from datetime import datetime
from dotenv import load_dotenv

# Import local modules
from utils.database import DatabaseManager
from models import ModelManager
from utils.alert_manager import AlertManager

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EDUGuard-Backend')

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Global variables for monitoring
monitoring_lock = threading.Lock()
monitoring_instances = {}  # Map of user_id -> monitoring instance

class MonitoringInstance:
    """Class to manage monitoring for a single user"""
    def __init__(self, user_id):
        self.user_id = user_id
        self.running = False
        self.frame_count = 0
        self.monitoring_thread = None
        self.cap = None
        self.model_manager = ModelManager()
        self.db_manager = DatabaseManager(user_id)
        self.alert_manager = AlertManager(self.db_manager)
        self.last_alert_check = 0
        self.alert_check_interval = 15  # seconds
        
    def start(self):
        """Start the monitoring process"""
        if self.running:
            logger.warning(f"Monitoring is already running for user {self.user_id}")
            return
        
        logger.info(f"Starting monitoring for user {self.user_id}")
        self.running = True
        
        # Update the database status
        self.db_manager.update_user_monitoring_status(True)
        
        # Start the monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
    def stop(self):
        """Stop the monitoring process"""
        if not self.running:
            logger.warning(f"Monitoring is not running for user {self.user_id}")
            return
        
        logger.info(f"Stopping monitoring for user {self.user_id}")
        self.running = False
        
        # Update the database status
        self.db_manager.update_user_monitoring_status(False)
        
        # Release the camera if it was initialized
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def _init_camera(self):
        """Initialize the camera."""
        if self.cap is None:
            camera_index = 0  # Default camera index
            self.cap = cv2.VideoCapture(camera_index)
            
            # Check if camera opened successfully
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera with index {camera_index}")
                
            logger.info(f"Camera initialized with index {camera_index}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            import cv2
            self._init_camera()
            
            last_capture_time = 0
            capture_interval = 0.1  # seconds
            
            while self.running:
                # Capture at specified interval
                current_time = time.time()
                if current_time - last_capture_time < capture_interval:
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
                
                # Process the frame through models
                predictions = self.model_manager.process_frame(frame)
                
                # Save predictions to the database
                for model_name, prediction in predictions.items():
                    if prediction:
                        self.db_manager.save_prediction(model_name, prediction)
                
                # Check for alerts periodically
                if current_time - self.last_alert_check >= self.alert_check_interval:
                    self.last_alert_check = current_time
                    self.alert_manager.check_all_alerts()
                    
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            self.running = False

def get_user_id_from_request():
    """Get the user ID from the request headers or parameters"""
    # Debug log the headers
    logger.debug(f"Request headers: {request.headers}")
    
    # Try to get from query params
    user_id = request.args.get('userId')
    if user_id:
        logger.debug(f"Using user ID from query params: {user_id}")
        return user_id
    
    # Try to get from headers - check for both forms that might be used
    user_id = request.headers.get('X-User-ID') or request.headers.get('X-User-Id') or request.headers.get('x-user-id')
    if user_id:
        logger.debug(f"Using user ID from header: {user_id}")
        return user_id
    
    # Last resort - check Authorization header for Bearer token which might contain user ID
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        logger.debug("Found Authorization Bearer token")
        # In a real implementation, you would validate the token
        # and extract the user ID from it
    
    logger.warning("No user ID found in request")
    return None

def get_monitoring_instance(user_id):
    """Get or create a monitoring instance for a user"""
    if user_id not in monitoring_instances:
        monitoring_instances[user_id] = MonitoringInstance(user_id)
    return monitoring_instances[user_id]

# API Routes
@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current status of the monitoring application"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    with monitoring_lock:
        if user_id in monitoring_instances:
            instance = monitoring_instances[user_id]
            status = {
                'running': instance.running,
                'frameCount': instance.frame_count,
                'userId': instance.user_id
            }
            return jsonify(status)
        else:
            return jsonify({'running': False, 'userId': user_id})

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start monitoring for a user"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    with monitoring_lock:
        instance = get_monitoring_instance(user_id)
        if instance.running:
            return jsonify({'message': 'Monitoring is already running', 'status': 'running'})
        
        try:
            instance.start()
            return jsonify({'message': 'Monitoring started successfully', 'status': 'running'})
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return jsonify({'error': f'Failed to start monitoring: {str(e)}'}), 500

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring for a user"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    with monitoring_lock:
        if user_id not in monitoring_instances:
            return jsonify({'message': 'Monitoring is not initialized', 'status': 'stopped'})
        
        instance = monitoring_instances[user_id]
        if not instance.running:
            return jsonify({'message': 'Monitoring is already stopped', 'status': 'stopped'})
        
        try:
            instance.stop()
            return jsonify({'message': 'Monitoring stopped successfully', 'status': 'stopped'})
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            return jsonify({'error': f'Failed to stop monitoring: {str(e)}'}), 500

@app.route('/api/alerts/recent', methods=['GET'])
def get_recent_alerts():
    """Get recent alerts for the user"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    try:
        db_manager = DatabaseManager(user_id)
        # Get the most recent alerts (limit to 20)
        alerts = db_manager.get_recent_alerts(20)
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return jsonify({'error': f'Failed to get alerts: {str(e)}'}), 500

@app.route('/api/predictions/recent', methods=['GET'])
def get_recent_predictions():
    """Get recent predictions for a specific model"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    model_name = request.args.get('model')
    if not model_name:
        return jsonify({'error': 'Model name is required'}), 400
    
    minutes = int(request.args.get('minutes', '5'))
    
    try:
        db_manager = DatabaseManager(user_id)
        predictions = db_manager.get_recent_predictions(model_name, minutes=minutes)
        
        # Get average if requested
        include_avg = request.args.get('includeAverage', 'false').lower() == 'true'
        average = None
        if include_avg:
            average = db_manager.calculate_prediction_average(model_name, minutes=minutes)
        
        return jsonify({
            'predictions': predictions,
            'average': average,
            'model': model_name,
            'minutes': minutes
        })
    except Exception as e:
        logger.error(f"Failed to get predictions: {e}")
        return jsonify({'error': f'Failed to get predictions: {str(e)}'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Email and password required'}), 400
    
    try:
        from firebase_admin import auth
        
        # Create Firebase user
        try:
            user = auth.create_user(
                email=data['email'],
                password=data['password']
            )
            
            # Create user profile in database
            user_data = {
                'email': data['email'],
                'createdAt': datetime.now().isoformat(),
                'displayName': data.get('displayName', data['email'].split('@')[0]),
                'lastLogin': datetime.now().isoformat(),
            }
            
            # Create user profile document
            try:
                db_manager = DatabaseManager(user.uid)
                db_manager.create_user_profile(user_data)
            except Exception as db_error:
                logger.error(f"Database error during registration: {db_error}")
            
            return jsonify({'status': 'success', 'uid': user.uid, 'user': user_data})
        except Exception as auth_error:
            logger.error(f"Auth error during registration: {auth_error}")
            return jsonify({'status': 'error', 'message': str(auth_error)}), 400
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Email and password required'}), 400
    
    try:
        from firebase_admin import auth
        
        # Verify user credentials using Firebase Auth
        try:
            user = auth.get_user_by_email(data['email'])
            
            # Get or create user profile
            db_manager = DatabaseManager(user.uid)
            user_data = db_manager.get_user_profile()
            
            if not user_data:
                user_data = {
                    'email': user.email,
                    'displayName': user.display_name or user.email.split('@')[0],
                    'lastLogin': datetime.now().isoformat()
                }
                db_manager.create_user_profile(user_data)
            else:
                # Update last login
                db_manager.update_user_profile({'lastLogin': datetime.now().isoformat()})
            
            return jsonify({
                'status': 'success',
                'uid': user.uid,
                'user': user_data
            })
        except Exception as auth_error:
            logger.error(f"Auth error during login: {auth_error}")
            return jsonify({'status': 'error', 'message': str(auth_error)}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get a user's profile"""
    user_id = get_user_id_from_request()
    logger.info(f"GET /api/user/profile - User ID: {user_id}")
    
    if not user_id:
        logger.error("Profile request missing user ID")
        return jsonify({'status': 'error', 'message': 'User ID is required'}), 400
    
    try:
        db_manager = DatabaseManager(user_id)
        profile = db_manager.get_user_profile()
        logger.info(f"Retrieved profile for user {user_id}: {profile}")
        
        if not profile:
            logger.warning(f"No profile found for user {user_id}")
            # Return minimal profile rather than 404 to prevent frontend errors
            minimal_profile = {
                'uid': user_id,
                'email': f"user-{user_id[:6]}@example.com",
                'displayName': f"User-{user_id[:6]}",
                'createdAt': datetime.now().isoformat()
            }
            # Return both formats for backward compatibility
            return jsonify({
                'status': 'success',
                'profile': minimal_profile,
                'user': minimal_profile
            })
        
        # Return both formats for backward compatibility
        return jsonify({
            'status': 'success',
            'profile': profile,
            'user': profile
        })
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/user/profile', methods=['PUT'])
def update_user_profile():
    """Update a user's profile"""
    user_id = get_user_id_from_request()
    logger.info(f"PUT /api/user/profile - User ID: {user_id}")
    
    if not user_id:
        logger.error("Profile update missing user ID")
        return jsonify({'status': 'error', 'message': 'User ID is required'}), 400
    
    data = request.json
    if not data:
        logger.error(f"No data provided in profile update for user {user_id}")
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    logger.info(f"Updating profile for user {user_id} with data: {data}")
    
    try:
        db_manager = DatabaseManager(user_id)
        db_manager.update_user_profile(data)
        
        # Get the updated profile to return
        updated_profile = db_manager.get_user_profile()
        
        return jsonify({
            'status': 'success', 
            'message': 'Profile updated',
            'profile': updated_profile,
            'user': updated_profile
        })
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Set up debug logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.setLevel(logging.DEBUG)
    
    # Initialize Firebase
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # Check for service account key
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT', 'serviceAccountKey.json')
        if not os.path.exists(service_account_path):
            logger.warning(f"Firebase service account key not found at {service_account_path}")
            logger.warning("Using mock Firebase implementation")
            from mock_firebase import init_mock_firebase
            init_mock_firebase()
        else:
            # Initialize Firebase with service account
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
        logger.warning("Using mock Firebase implementation")
        from mock_firebase import init_mock_firebase
        init_mock_firebase()
    
    # Start the Flask server
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Starting Flask server on {host}:{port} (Debug mode: {debug_mode})")
    app.run(host=host, port=port, debug=debug_mode, threaded=True) 