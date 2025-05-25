import time
import datetime
import os
import json
import logging
from datetime import datetime

# Configure logger
logger = logging.getLogger('EDUGuard.Database')

class DatabaseManager:
    """Manager for Firebase database operations."""
    
    def __init__(self, user_id):
        """Initialize the database manager for a specific user.
        
        Args:
            user_id (str): The ID of the user.
        """
        self.user_id = user_id
        self.db_type = 'local'  # Default to local, will try Firebase first
        
        # Always try Firebase first
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialize Firebase database references"""
        try:
            # Import Firebase modules
            import firebase_admin
            from firebase_admin import db
            
            # Check if Firebase app is initialized
            if not firebase_admin._apps:
                # Initialize Firebase if not already done
                logger.info("No Firebase app found. Initializing Firebase...")
                self._init_firebase_app()
            else:
                logger.info("Using existing Firebase app...")
            
            # Get the default app
            app = firebase_admin.get_app()
            
            # Try to create a test database reference to verify the connection works
            try:
                test_ref = db.reference('test', app=app)
                logger.info("✅ Firebase database connection verified successfully")
            except Exception as e:
                logger.warning(f"Firebase database connection test failed: {e}")
                # If the existing app doesn't work, try to reinitialize
                logger.info("Attempting to reinitialize Firebase with proper database URL...")
                
                # Delete existing app and start fresh
                firebase_admin.delete_app(app)
                self._init_firebase_app()
                app = firebase_admin.get_app()
                
                # Test again
                test_ref = db.reference('test', app=app)
                logger.info("✅ Firebase database connection verified after reinitialization")
            
            # Create database references using the working Firebase app
            self.predictions_ref = db.reference(f'predictions/{self.user_id}', app=app)
            self.alerts_ref = db.reference(f'alerts/{self.user_id}', app=app)
            self.users_ref = db.reference(f'users/{self.user_id}', app=app)
            self.user_status_ref = db.reference(f'user_status/{self.user_id}', app=app)
            
            self.db_initialized = True
            self.db_type = 'firebase'
            logger.info(f"✅ Firebase database initialized successfully for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Error initializing Firebase database: {e}")
            logger.info("Falling back to local database")
            self._init_local_db()
    
    def _init_firebase_app(self):
        """Initialize Firebase app if not already initialized"""
        try:
            import firebase_admin
            from firebase_admin import credentials
            
            # Check if service account key exists
            # Try both relative to current directory and backend directory
            service_account_paths = [
                'serviceAccountKey.json',
                'backend/serviceAccountKey.json',
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'serviceAccountKey.json')
            ]
            
            service_account_path = None
            for path in service_account_paths:
                if os.path.exists(path):
                    service_account_path = path
                    break
            
            if service_account_path:
                cred = credentials.Certificate(service_account_path)
                logger.info(f"Using Firebase service account key: {service_account_path}")
                
                # Extract project ID for database URL
                with open(service_account_path, 'r') as f:
                    service_account = json.load(f)
                    project_id = service_account.get('project_id', 'eduguard-db')
                
                database_url = f"https://{project_id}-default-rtdb.firebaseio.com"
                
                # Initialize Firebase app
                firebase_admin.initialize_app(cred, {
                    'databaseURL': database_url
                })
                
                logger.info(f"✅ Firebase app initialized with database URL: {database_url}")
            else:
                raise FileNotFoundError(f"Firebase service account key not found in any of these locations: {service_account_paths}")
                
        except Exception as e:
            logger.error(f"Error initializing Firebase app: {e}")
            raise
    
    def _init_local_db(self):
        """Initialize local database for testing and offline operation"""
        self.local_db = {
            'predictions': {},
            'alerts': {},
            'user_status': {},
            'user_profile': {}
        }
        
        self.db_initialized = True
        self.db_type = 'local'
        logger.warning(f"Using LOCAL database for user {self.user_id} - Firebase not available!")

    def save_prediction(self, model_name, prediction, timestamp=None):
        """Save a single model prediction to the database.
        
        Args:
            model_name (str): The name of the model (e.g., 'posture').
            prediction (dict): The prediction data to store.
            timestamp (int, optional): Unix timestamp. Defaults to current time.
        
        Returns:
            str: The key of the saved prediction.
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)  # milliseconds since epoch
            
        data = {
            'model': model_name,
            'prediction': prediction,
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat()
        }
        
        try:
            if self.db_type == 'firebase':
                # Push data to predictions/{user_id}/{model_name}
                model_ref = self.predictions_ref.child(model_name)
                push_result = model_ref.push()
                key = push_result.key
                model_ref.child(key).set(data)
                
                # Also update the latest prediction
                self.user_status_ref.child('latest_predictions').child(model_name).set({
                    **data,
                    'prediction_id': key
                })
                
                logger.info(f"✅ SAVED TO FIREBASE: {model_name} prediction for user {self.user_id}")
                return key
            else:
                # Local DB operation
                if model_name not in self.local_db['predictions']:
                    self.local_db['predictions'][model_name] = {}
                
                # Generate a simple key
                key = f"{int(time.time())}-{id(data)}"
                self.local_db['predictions'][model_name][key] = data
                
                # Update latest prediction
                if 'latest_predictions' not in self.local_db['user_status']:
                    self.local_db['user_status']['latest_predictions'] = {}
                
                self.local_db['user_status']['latest_predictions'][model_name] = {
                    **data,
                    'prediction_id': key
                }
                
                logger.warning(f"⚠️ SAVED TO LOCAL DB: {model_name} prediction for user {self.user_id}")
                return key
                
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return None
    
    def save_alert(self, alert_type, message, level='warning', data=None, timestamp=None):
        """Save an alert to the database.
        
        Args:
            alert_type (str): The type of alert (e.g., 'posture').
            message (str): The alert message.
            level (str, optional): Alert severity level. Defaults to 'warning'.
            data (dict, optional): Additional data for the alert. Defaults to None.
            timestamp (int, optional): Unix timestamp. Defaults to current time.
            
        Returns:
            str: The key of the saved alert.
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)
            
        if data is None:
            data = {}
            
        alert_data = {
            'type': alert_type,
            'message': message,
            'level': level,
            'data': data,
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat(),
            'read': False
        }
        
        try:
            if self.db_type == 'firebase':
                # Push alert to alerts/{user_id}
                push_result = self.alerts_ref.push()
                key = push_result.key
                self.alerts_ref.child(key).set(alert_data)
                
                # Update latest alert
                self.user_status_ref.child('latest_alert').set({
                    **alert_data,
                    'alert_id': key
                })
                
                logger.info(f"✅ SAVED ALERT TO FIREBASE: {message} for user {self.user_id}")
                return key
            else:
                # Local DB operation
                key = f"{int(time.time())}-{id(alert_data)}"
                self.local_db['alerts'][key] = alert_data
                
                # Update latest alert
                self.local_db['user_status']['latest_alert'] = {
                    **alert_data,
                    'alert_id': key
                }
                
                logger.warning(f"⚠️ SAVED ALERT TO LOCAL DB: {message} for user {self.user_id}")
                return key
                
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
            return None
    
    def get_recent_alerts(self, limit=20):
        """Get recent alerts for the user.
        
        Args:
            limit (int, optional): Maximum number of alerts to retrieve. Defaults to 20.
            
        Returns:
            list: List of recent alerts.
        """
        try:
            if self.db_type == 'firebase':
                # Get all alerts and sort in Python to avoid Firebase indexing issues
                query = self.alerts_ref.get()
                
                if query:
                    # Convert to list and add ID
                    alerts = [{'id': key, **value} for key, value in query.items()]
                    # Sort by timestamp (newest first)
                    alerts.sort(key=lambda a: a.get('timestamp', 0), reverse=True)
                    logger.debug(f"📖 Retrieved {len(alerts)} alerts from FIREBASE for user {self.user_id}")
                    return alerts[:limit]  # Apply limit after sorting
                return []
            else:
                # Local DB operation
                alerts = [{'id': key, **value} for key, value in self.local_db['alerts'].items()]
                alerts.sort(key=lambda a: a.get('timestamp', 0), reverse=True)
                logger.debug(f"📖 Retrieved {len(alerts)} alerts from LOCAL DB for user {self.user_id}")
                return alerts[:limit]
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []
    
    def get_recent_predictions(self, model_name, minutes=5, limit=100):
        """Get recent predictions for a specific model.
        
        Args:
            model_name (str): The name of the model.
            minutes (int, optional): Time window in minutes. Defaults to 5.
            limit (int, optional): Maximum number of predictions to retrieve. Defaults to 100.
            
        Returns:
            list: List of recent predictions.
        """
        try:
            # Calculate the cutoff timestamp
            cutoff_time = int((time.time() - (minutes * 60)) * 1000)  # milliseconds
            
            if self.db_type == 'firebase':
                # Get all predictions for the model and filter in Python to avoid indexing issues
                model_ref = self.predictions_ref.child(model_name)
                query = model_ref.get()
                
                # Filter to only include predictions within the time window
                if query:
                    recent_predictions = [
                        {**prediction, 'id': key} 
                        for key, prediction in query.items() 
                        if prediction.get('timestamp', 0) >= cutoff_time
                    ]
                    # Sort by timestamp (newest first)
                    recent_predictions.sort(key=lambda p: p.get('timestamp', 0), reverse=True)
                    logger.debug(f"📖 Retrieved {len(recent_predictions)} {model_name} predictions from FIREBASE for user {self.user_id}")
                    return recent_predictions[:limit]  # Apply limit after sorting
                return []
            else:
                # Local DB operation
                if model_name not in self.local_db['predictions']:
                    return []
                
                predictions = self.local_db['predictions'][model_name]
                recent_predictions = [
                    {**prediction, 'id': key} 
                    for key, prediction in predictions.items() 
                    if prediction.get('timestamp', 0) >= cutoff_time
                ]
                recent_predictions.sort(key=lambda p: p.get('timestamp', 0), reverse=True)
                logger.debug(f"📖 Retrieved {len(recent_predictions)} {model_name} predictions from LOCAL DB for user {self.user_id}")
                return recent_predictions[:limit]
        except Exception as e:
            logger.error(f"Error getting recent predictions: {e}")
            return []
    
    def calculate_prediction_average(self, model_name, minutes=5):
        """Calculate the average prediction for a model over a time window.
        
        Args:
            model_name (str): The name of the model.
            minutes (int, optional): Time window in minutes. Defaults to 5.
            
        Returns:
            dict: Average prediction values.
        """
        predictions = self.get_recent_predictions(model_name, minutes)
        
        if not predictions:
            return None
        
        try:
            if model_name == 'posture':
                # Calculate posture statistics
                posture_values = [
                    p.get('prediction', {}).get('posture', '') 
                    for p in predictions
                ]
                
                if not posture_values:
                    return None
                
                # Count good vs bad postures
                good_count = sum(1 for posture in posture_values if posture == 'Good Posture')
                bad_count = sum(1 for posture in posture_values if posture == 'Bad Posture')
                total_count = len(posture_values)
                
                # Calculate percentages
                good_percentage = (good_count / total_count) * 100 if total_count > 0 else 0
                bad_percentage = (bad_count / total_count) * 100 if total_count > 0 else 0
                
                return {
                    'good_posture_count': good_count,
                    'bad_posture_count': bad_count,
                    'good_posture_percentage': good_percentage,
                    'bad_posture_percentage': bad_percentage,
                    'total_samples': total_count,
                    'samples': len(predictions)
                }
            elif model_name == 'stress':
                # Calculate stress statistics
                stress_values = [
                    p.get('prediction', {}).get('stress_level', '') 
                    for p in predictions
                ]
                
                if not stress_values:
                    return None
                
                # Count stress levels
                low_count = sum(1 for stress in stress_values if stress == 'Low Stress')
                medium_count = sum(1 for stress in stress_values if stress == 'Medium Stress')
                high_count = sum(1 for stress in stress_values if stress == 'High Stress')
                total_count = len(stress_values)
                
                # Calculate percentages
                low_percentage = (low_count / total_count) * 100 if total_count > 0 else 0
                medium_percentage = (medium_count / total_count) * 100 if total_count > 0 else 0
                high_percentage = (high_count / total_count) * 100 if total_count > 0 else 0
                
                return {
                    'low_stress_count': low_count,
                    'medium_stress_count': medium_count,
                    'high_stress_count': high_count,
                    'low_stress_percentage': low_percentage,
                    'medium_stress_percentage': medium_percentage,
                    'high_stress_percentage': high_percentage,
                    'total_samples': total_count,
                    'samples': len(predictions)
                }
            elif model_name == 'cvs':
                # Calculate eye blink statistics
                blink_values = [
                    p.get('prediction', {}).get('blink_count', 0) 
                    for p in predictions
                ]
                
                if not blink_values:
                    return None
                
                # Average blink count over the time period
                total_blinks = sum(blink_values)
                avg_blink_count = total_blinks / len(blink_values) if blink_values else 0
                
                # Categorize blink rates
                # Low blink rate: < 17 blinks per minute (dry eyes)
                # Normal blink rate: 17-20 blinks per minute
                # High blink rate: > 20 blinks per minute (eye fatigue)
                low_blink_count = sum(1 for blink in blink_values if blink < 17)
                normal_blink_count = sum(1 for blink in blink_values if 17 <= blink <= 20)
                high_blink_count = sum(1 for blink in blink_values if blink > 20)
                total_count = len(blink_values)
                
                # Calculate percentages
                low_percentage = (low_blink_count / total_count) * 100 if total_count > 0 else 0
                normal_percentage = (normal_blink_count / total_count) * 100 if total_count > 0 else 0
                high_percentage = (high_blink_count / total_count) * 100 if total_count > 0 else 0
                
                return {
                    'avg_blink_count': avg_blink_count,
                    'low_blink_count': low_blink_count,
                    'normal_blink_count': normal_blink_count,
                    'high_blink_count': high_blink_count,
                    'low_blink_percentage': low_percentage,
                    'normal_blink_percentage': normal_percentage,
                    'high_blink_percentage': high_percentage,
                    'total_samples': total_count,
                    'samples': len(predictions)
                }
            return None
        except Exception as e:
            logger.error(f"Error calculating prediction average: {e}")
            return None
    
    def update_user_monitoring_status(self, is_monitoring):
        """Update the user's monitoring status.
        
        Args:
            is_monitoring (bool): Whether the user is currently being monitored.
        """
        try:
            status_data = {
                'is_monitoring': is_monitoring,
                'last_updated': datetime.now().isoformat()
            }
            
            if self.db_type == 'firebase':
                self.user_status_ref.update(status_data)
                logger.debug(f"✅ Updated monitoring status in FIREBASE for user {self.user_id}: {is_monitoring}")
            else:
                self.local_db['user_status'].update(status_data)
                logger.debug(f"⚠️ Updated monitoring status in LOCAL DB for user {self.user_id}: {is_monitoring}")
                
            return True
        except Exception as e:
            logger.error(f"Error updating user monitoring status: {e}")
            return False
    
    def get_user_profile(self):
        """Get the user's profile data.
        
        Returns:
            dict: User profile data.
        """
        try:
            if self.db_type == 'firebase':
                profile = self.users_ref.get()
                logger.debug(f"📖 Retrieved profile from FIREBASE for user {self.user_id}")
                return profile if profile else {}
            else:
                logger.debug(f"📖 Retrieved profile from LOCAL DB for user {self.user_id}")
                return self.local_db['user_profile']
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {}
    
    def create_user_profile(self, profile_data):
        """Create a new user profile.
        
        Args:
            profile_data (dict): User profile data.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if self.db_type == 'firebase':
                self.users_ref.set(profile_data)
                logger.info(f"✅ Created user profile in FIREBASE for user {self.user_id}")
            else:
                self.local_db['user_profile'] = profile_data
                logger.warning(f"⚠️ Created user profile in LOCAL DB for user {self.user_id}")
                
            return True
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return False
    
    def update_user_profile(self, update_data):
        """Update a user's profile.
        
        Args:
            update_data (dict): Data to update in the profile.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if self.db_type == 'firebase':
                self.users_ref.update(update_data)
                logger.info(f"✅ Updated user profile in FIREBASE for user {self.user_id}")
            else:
                self.local_db['user_profile'].update(update_data)
                logger.warning(f"⚠️ Updated user profile in LOCAL DB for user {self.user_id}")
                
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False