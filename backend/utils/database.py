import time
import datetime
import os
import json
import logging
from datetime import datetime, timedelta

# Configure logger
logger = logging.getLogger('EDUGuard.Database')

# Helper function to ensure log messages are safe for all consoles
def safe_log(message):
    """Replace emoji characters with text alternatives"""
    return message

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
                logger.info("[SUCCESS] Firebase database connection verified successfully")
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
                logger.info("[SUCCESS] Firebase database connection verified after reinitialization")
            
            # Create database references using the working Firebase app
            self.predictions_ref = db.reference(f'predictions/{self.user_id}', app=app)
            self.alerts_ref = db.reference(f'alerts/{self.user_id}', app=app)
            self.users_ref = db.reference(f'users/{self.user_id}', app=app)
            self.user_status_ref = db.reference(f'user_status/{self.user_id}', app=app)
            
            self.db_initialized = True
            self.db_type = 'firebase'
            logger.info(f"[SUCCESS] Firebase database initialized successfully for user {self.user_id}")
            
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
                
                logger.info(f"[SUCCESS] Firebase app initialized with database URL: {database_url}")
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
                
                logger.info(f"[SAVED TO FIREBASE] {model_name} prediction for user {self.user_id}")
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
                
                logger.warning(f"[SAVED TO LOCAL DB] {model_name} prediction for user {self.user_id}")
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
                
                logger.info(f"[SAVED ALERT TO FIREBASE] {message} for user {self.user_id}")
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
                
                logger.warning(f"[SAVED ALERT TO LOCAL DB] {message} for user {self.user_id}")
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
                    logger.debug(f"[BOOK] Retrieved {len(alerts)} alerts from FIREBASE for user {self.user_id}")
                    return alerts[:limit]  # Apply limit after sorting
                return []
            else:
                # Local DB operation
                alerts = [{'id': key, **value} for key, value in self.local_db['alerts'].items()]
                alerts.sort(key=lambda a: a.get('timestamp', 0), reverse=True)
                logger.debug(f"[BOOK] Retrieved {len(alerts)} alerts from LOCAL DB for user {self.user_id}")
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
                    recent_predictions = []
                    for key, prediction in query.items():
                        # Skip if prediction is not a dictionary
                        if not isinstance(prediction, dict):
                            logger.warning(f"Skipping non-dict prediction in {model_name}: {type(prediction)}")
                            continue
                            
                        timestamp = prediction.get('timestamp', 0)
                        if timestamp >= cutoff_time:
                            # Add prediction ID to the object
                            prediction_with_id = dict(prediction)
                            prediction_with_id['id'] = key
                            recent_predictions.append(prediction_with_id)
                    
                    # Sort by timestamp (newest first)
                    recent_predictions.sort(key=lambda p: p.get('timestamp', 0), reverse=True)
                    logger.debug(f"[BOOK] Retrieved {len(recent_predictions)} {model_name} predictions from FIREBASE for user {self.user_id}")
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
                logger.debug(f"[BOOK] Retrieved {len(recent_predictions)} {model_name} predictions from LOCAL DB for user {self.user_id}")
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
                posture_values = []
                for p in predictions:
                    # Skip if prediction is not properly structured
                    if not isinstance(p.get('prediction'), dict):
                        continue
                    posture = p.get('prediction', {}).get('posture', '')
                    if posture:
                        posture_values.append(posture)
                
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
                stress_values = []
                for p in predictions:
                    # Skip if prediction is not properly structured
                    if not isinstance(p.get('prediction'), dict):
                        continue
                    stress_level = p.get('prediction', {}).get('stress_level', '')
                    if stress_level:
                        stress_values.append(stress_level)
                
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
                blink_values = []
                for p in predictions:
                    # Skip if prediction is not properly structured
                    if not isinstance(p.get('prediction'), dict):
                        continue
                    blink_count = p.get('prediction', {}).get('blink_count', 0)
                    if isinstance(blink_count, (int, float)):
                        blink_values.append(blink_count)
                
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
            elif model_name == 'hydration':
                # Calculate hydration statistics
                hydration_values = []
                dryness_scores = []
                
                for p in predictions:
                    # Skip if prediction is not properly structured
                    if not isinstance(p.get('prediction'), dict):
                        continue
                    
                    hydration_status = p.get('prediction', {}).get('hydration_status', '')
                    if hydration_status:
                        hydration_values.append(hydration_status)
                    
                    dryness_score = p.get('prediction', {}).get('dryness_score', None)
                    if isinstance(dryness_score, (int, float)):
                        dryness_scores.append(dryness_score)
                
                if not hydration_values and not dryness_scores:
                    return None
                
                # Default values in case we're missing data
                dry_count = 0
                normal_count = 0
                total_count = 0
                
                # Count lip statuses if we have that data
                if hydration_values:
                    dry_count = sum(1 for status in hydration_values if status == 'Dry Lips')
                    normal_count = sum(1 for status in hydration_values if status == 'Normal Lips')
                    total_count = len(hydration_values)
                
                # Get average dryness score
                avg_dryness_score = sum(dryness_scores) / len(dryness_scores) if dryness_scores else 0
                
                # If we have no hydration status data but we have dryness scores,
                # infer the status from the scores
                if not hydration_values and dryness_scores:
                    # Count lips as dry if dryness score > 0.5
                    dry_count = sum(1 for score in dryness_scores if score >= 0.5)
                    normal_count = len(dryness_scores) - dry_count
                    total_count = len(dryness_scores)
                
                # Calculate percentages
                dry_percentage = (dry_count / total_count) * 100 if total_count > 0 else 0
                normal_percentage = (normal_count / total_count) * 100 if total_count > 0 else 0
                
                return {
                    'dry_lips_count': dry_count,
                    'normal_lips_count': normal_count,
                    'dry_lips_percentage': dry_percentage,
                    'normal_lips_percentage': normal_percentage,
                    'avg_dryness_score': avg_dryness_score,
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
                logger.debug(f"[SUCCESS] Updated monitoring status in FIREBASE for user {self.user_id}: {is_monitoring}")
            else:
                self.local_db['user_status'].update(status_data)
                logger.debug(f"[WARNING] Updated monitoring status in LOCAL DB for user {self.user_id}: {is_monitoring}")
                
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
                logger.debug(f"[INFO] Retrieved profile from FIREBASE for user {self.user_id}")
                return profile if profile else {}
            else:
                logger.debug(f"[INFO] Retrieved profile from LOCAL DB for user {self.user_id}")
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
                logger.info(f"[SUCCESS] Created user profile in FIREBASE for user {self.user_id}")
            else:
                self.local_db['user_profile'] = profile_data
                logger.warning(f"[WARNING] Created user profile in LOCAL DB for user {self.user_id}")
                
            return True
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return False
    
    def update_user_profile(self, update_data):
        """Update a user's profile data in the database.
        
        Args:
            update_data (dict): The profile data to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if self.db_type == 'firebase':
                self.users_ref.update(update_data)
                logger.info(f"[UPDATED IN FIREBASE] User profile for {self.user_id}")
                return True
            else:
                # Local DB operation
                self.local_db['user_profile'].update(update_data)
                logger.warning(f"[UPDATED IN LOCAL DB] User profile for {self.user_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
            
    # -----------------------------------------------------------------------------
    # Reports Data Methods
    # -----------------------------------------------------------------------------
    def get_posture_data_range(self, start_date, end_date):
        """Get posture data for a specific date range."""
        try:
            # Convert dates to timestamps (milliseconds)
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1000)
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp() * 1000)
            
            logger.info(f"Fetching posture data from {start_date} to {end_date} (timestamps: {start_timestamp} to {end_timestamp})")
            
            if self.db_type == 'firebase':
                try:
                    from firebase_admin import db
                    
                    # Get data from Firebase ordered by timestamp
                    posture_ref = self.predictions_ref.child('posture')
                    logger.info(f"Querying Firebase path: predictions/{self.user_id}/posture")
                    
                    # First try to get all data and filter in code (more reliable)
                    all_results = posture_ref.get()
                    logger.debug(f"Raw Firebase response: {all_results}")
                    
                    # Convert to list of entries
                    data = []
                    if all_results:
                        for key, value in all_results.items():
                            # Get timestamp for filtering
                            entry_timestamp = value.get('timestamp', 0)
                            
                            # Filter by time range
                            if entry_timestamp >= start_timestamp and entry_timestamp <= end_timestamp:
                                # Extract data
                                entry = {'timestamp': entry_timestamp}
                                
                                # Check for different data structures
                                if 'prediction' in value:
                                    if 'average' in value['prediction']:
                                        # From average data
                                        entry['good_posture_percentage'] = value['prediction']['average'].get('good_posture_percentage', 0)
                                        entry['bad_posture_percentage'] = value['prediction']['average'].get('bad_posture_percentage', 0)
                                        entry['total_samples'] = value['prediction']['average'].get('total_samples', 0)
                                    elif 'posture' in value['prediction']:
                                        # From direct prediction
                                        good_posture = 100 if value['prediction']['posture'] == 'Good Posture' else 0
                                        entry['good_posture_percentage'] = good_posture
                                        entry['bad_posture_percentage'] = 100 - good_posture
                                        entry['total_samples'] = 1
                                    else:
                                        continue
                                else:
                                    continue
                                    
                                # Add to result list
                                data.append(entry)
                    
                    # Group by timeframe (hourly for daily, daily for weekly, etc.)
                    # This helps when we have too many data points
                    grouped_data = self._group_time_series_data(data, start_date, end_date, 'posture')
                    
                    logger.info(f"Retrieved {len(data)} raw posture entries, grouped into {len(grouped_data)} entries")
                    return grouped_data
                except Exception as e:
                    logger.error(f"Firebase error fetching posture data: {e}")
                    return []
            else:
                # Return empty array instead of sample data
                logger.warning(f"Firebase not available. Returning empty posture data for date range {start_date} to {end_date}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving posture data for date range: {e}")
            return []
        
    def _group_time_series_data(self, data, start_date, end_date, data_type):
        """Group time series data by appropriate time intervals based on date range.
        
        Args:
            data (list): List of data entries with timestamps.
            start_date (datetime.date): Start date.
            end_date (datetime.date): End date.
            data_type (str): Type of data ('posture', 'stress', 'cvs', 'hydration').
            
        Returns:
            list: List of grouped data entries.
        """
        if not data:
            logger.warning(f"No data available for {data_type} in date range {start_date} to {end_date}")
            return []
        
        # Sort data by timestamp
        data.sort(key=lambda x: x.get('timestamp', 0))
        
        # Determine grouping interval
        days_difference = (end_date - start_date).days
        
        if days_difference <= 1:
            # Group by hour for daily view
            interval = 'hour'
        elif days_difference <= 7:
            # Group by day for weekly view
            interval = 'day'
        else:
            # Group by day for monthly view
            interval = 'day'
        
        logger.info(f"Grouping {data_type} data by {interval} for {days_difference} day(s) range")
        
        # Group data
        grouped_data = []
        current_group = None
        current_date = None
        
        for entry in data:
            timestamp = entry.get('timestamp', 0)
            entry_date = datetime.fromtimestamp(timestamp / 1000)
            
            # Get the key for grouping
            if interval == 'hour':
                group_key = entry_date.strftime('%Y-%m-%d %H')
            elif interval == 'day':
                group_key = entry_date.strftime('%Y-%m-%d')
            
            # Start a new group if needed
            if current_date != group_key:
                # Save previous group if exists
                if current_group:
                    grouped_data.append(current_group)
                
                # Initialize new group with timestamp of first entry
                current_group = {
                    'timestamp': timestamp,
                    'entry_count': 0
                }
                
                # Add the appropriate fields based on data type
                if data_type == 'posture':
                    current_group['good_posture_percentage'] = 0
                    current_group['bad_posture_percentage'] = 0
                elif data_type == 'stress':
                    current_group['low_stress_percentage'] = 0
                    current_group['medium_stress_percentage'] = 0
                    current_group['high_stress_percentage'] = 0
                elif data_type == 'cvs':
                    current_group['normal_blink_percentage'] = 0
                    current_group['low_blink_percentage'] = 0
                    current_group['high_blink_percentage'] = 0
                    current_group['avg_blink_count'] = 0
                elif data_type == 'hydration':
                    current_group['normal_lips_percentage'] = 0
                    current_group['dry_lips_percentage'] = 0
                    current_group['avg_dryness_score'] = 0
                    
                current_date = group_key
            
            # Update group with current entry
            current_group['entry_count'] += 1
            
            # Sum values based on data type (we'll calculate averages later)
            if data_type == 'posture':
                current_group['good_posture_percentage'] += entry.get('good_posture_percentage', 0)
                current_group['bad_posture_percentage'] += entry.get('bad_posture_percentage', 0)
            elif data_type == 'stress':
                current_group['low_stress_percentage'] += entry.get('low_stress_percentage', 0)
                current_group['medium_stress_percentage'] += entry.get('medium_stress_percentage', 0)
                current_group['high_stress_percentage'] += entry.get('high_stress_percentage', 0)
            elif data_type == 'cvs':
                current_group['normal_blink_percentage'] += entry.get('normal_blink_percentage', 0)
                current_group['low_blink_percentage'] += entry.get('low_blink_percentage', 0)
                current_group['high_blink_percentage'] += entry.get('high_blink_percentage', 0)
                current_group['avg_blink_count'] += entry.get('avg_blink_count', 0)
            elif data_type == 'hydration':
                current_group['normal_lips_percentage'] += entry.get('normal_lips_percentage', 0)
                current_group['dry_lips_percentage'] += entry.get('dry_lips_percentage', 0)
                current_group['avg_dryness_score'] += entry.get('avg_dryness_score', 0)
        
        # Add the last group
        if current_group:
            grouped_data.append(current_group)
        
        # Calculate averages for each group
        for group in grouped_data:
            count = group['entry_count']
            if count > 0:
                if data_type == 'posture':
                    group['good_posture_percentage'] /= count
                    group['bad_posture_percentage'] /= count
                elif data_type == 'stress':
                    group['low_stress_percentage'] /= count
                    group['medium_stress_percentage'] /= count
                    group['high_stress_percentage'] /= count
                elif data_type == 'cvs':
                    group['normal_blink_percentage'] /= count
                    group['low_blink_percentage'] /= count
                    group['high_blink_percentage'] /= count
                    group['avg_blink_count'] /= count
                elif data_type == 'hydration':
                    group['normal_lips_percentage'] /= count
                    group['dry_lips_percentage'] /= count
                    group['avg_dryness_score'] /= count
        
        logger.info(f"Successfully grouped {data_type} data into {len(grouped_data)} entries")
        return grouped_data
    
    def get_stress_data_range(self, start_date, end_date):
        """Get stress data for a specific date range."""
        try:
            # Convert dates to timestamps (milliseconds)
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1000)
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp() * 1000)
            
            logger.info(f"Fetching stress data from {start_date} to {end_date} (timestamps: {start_timestamp} to {end_timestamp})")
            
            if self.db_type == 'firebase':
                try:
                    from firebase_admin import db
                    
                    # Get data from Firebase ordered by timestamp
                    stress_ref = self.predictions_ref.child('stress')
                    logger.info(f"Querying Firebase path: predictions/{self.user_id}/stress")
                    
                    # First try to get all data and filter in code (more reliable)
                    all_results = stress_ref.get()
                    
                    # Convert to list of entries
                    data = []
                    if all_results:
                        for key, value in all_results.items():
                            # Get timestamp for filtering
                            entry_timestamp = value.get('timestamp', 0)
                            
                            # Filter by time range
                            if entry_timestamp >= start_timestamp and entry_timestamp <= end_timestamp:
                                # Extract data
                                entry = {'timestamp': entry_timestamp}
                                
                                # Check for different data structures
                                if 'prediction' in value:
                                    if 'average' in value['prediction']:
                                        # From average data
                                        entry['low_stress_percentage'] = value['prediction']['average'].get('low_stress_percentage', 0)
                                        entry['medium_stress_percentage'] = value['prediction']['average'].get('medium_stress_percentage', 0)
                                        entry['high_stress_percentage'] = value['prediction']['average'].get('high_stress_percentage', 0)
                                        entry['total_samples'] = value['prediction']['average'].get('total_samples', 0)
                                    elif 'stress_level' in value['prediction']:
                                        # From direct prediction
                                        stress_level = value['prediction']['stress_level']
                                        low = 100 if stress_level == 'Low Stress' else 0
                                        medium = 100 if stress_level == 'Medium Stress' else 0
                                        high = 100 if stress_level == 'High Stress' else 0
                                        
                                        entry['low_stress_percentage'] = low
                                        entry['medium_stress_percentage'] = medium
                                        entry['high_stress_percentage'] = high
                                        entry['total_samples'] = 1
                                    else:
                                        continue
                                else:
                                    continue
                                    
                                # Add to result list
                                data.append(entry)
                    
                    # Group by timeframe (hourly for daily, daily for weekly, etc.)
                    # This helps when we have too many data points
                    grouped_data = self._group_time_series_data(data, start_date, end_date, 'stress')
                    
                    logger.info(f"Retrieved {len(data)} raw stress entries, grouped into {len(grouped_data)} entries")
                    return grouped_data
                except Exception as e:
                    logger.error(f"Firebase error fetching stress data: {e}")
                    return []
            else:
                # Return empty array instead of sample data
                logger.warning(f"Firebase not available. Returning empty stress data for date range {start_date} to {end_date}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving stress data for date range: {e}")
            return []
    
    def get_cvs_data_range(self, start_date, end_date):
        """Get CVS (eye strain) data for a specific date range."""
        try:
            # Convert dates to timestamps (milliseconds)
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1000)
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp() * 1000)
            
            logger.info(f"Fetching CVS data from {start_date} to {end_date} (timestamps: {start_timestamp} to {end_timestamp})")
            
            if self.db_type == 'firebase':
                try:
                    from firebase_admin import db
                    
                    # Get data from Firebase ordered by timestamp
                    cvs_ref = self.predictions_ref.child('cvs')
                    logger.info(f"Querying Firebase path: predictions/{self.user_id}/cvs")
                    
                    # First try to get all data and filter in code (more reliable)
                    all_results = cvs_ref.get()
                    
                    # Convert to list of entries
                    data = []
                    if all_results:
                        for key, value in all_results.items():
                            # Get timestamp for filtering
                            entry_timestamp = value.get('timestamp', 0)
                            
                            # Filter by time range
                            if entry_timestamp >= start_timestamp and entry_timestamp <= end_timestamp:
                                # Extract data
                                entry = {'timestamp': entry_timestamp}
                                
                                # Check for different data structures
                                if 'prediction' in value:
                                    if 'average' in value['prediction']:
                                        # From average data
                                        entry['avg_blink_count'] = value['prediction']['average'].get('avg_blink_count', 0)
                                        entry['normal_blink_percentage'] = value['prediction']['average'].get('normal_blink_percentage', 0)
                                        entry['low_blink_percentage'] = value['prediction']['average'].get('low_blink_percentage', 0)
                                        entry['high_blink_percentage'] = value['prediction']['average'].get('high_blink_percentage', 0)
                                        entry['total_samples'] = value['prediction']['average'].get('total_samples', 0)
                                    elif 'blink_count' in value['prediction']:
                                        # From direct prediction
                                        blink_count = value['prediction']['blink_count']
                                        # Categorize blink rate
                                        low_blink = 100 if blink_count < 17 else 0
                                        normal_blink = 100 if 17 <= blink_count <= 20 else 0 
                                        high_blink = 100 if blink_count > 20 else 0
                                        
                                        entry['avg_blink_count'] = blink_count
                                        entry['normal_blink_percentage'] = normal_blink
                                        entry['low_blink_percentage'] = low_blink
                                        entry['high_blink_percentage'] = high_blink
                                        entry['total_samples'] = 1
                                    else:
                                        continue
                                else:
                                    continue
                                    
                                # Add to result list
                                data.append(entry)
                    
                    # Group by timeframe (hourly for daily, daily for weekly, etc.)
                    # This helps when we have too many data points
                    grouped_data = self._group_time_series_data(data, start_date, end_date, 'cvs')
                    
                    logger.info(f"Retrieved {len(data)} raw CVS entries, grouped into {len(grouped_data)} entries")
                    return grouped_data
                except Exception as e:
                    logger.error(f"Firebase error fetching CVS data: {e}")
                    return []
            else:
                # Return empty array instead of sample data
                logger.warning(f"Firebase not available. Returning empty CVS data for date range {start_date} to {end_date}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving CVS data for date range: {e}")
            return []
    
    def get_hydration_data_range(self, start_date, end_date):
        """Get hydration data for a specific date range."""
        try:
            # Convert dates to timestamps (milliseconds)
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1000)
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp() * 1000)
            
            logger.info(f"Fetching hydration data from {start_date} to {end_date} (timestamps: {start_timestamp} to {end_timestamp})")
            
            if self.db_type == 'firebase':
                try:
                    from firebase_admin import db
                    
                    # Get data from Firebase ordered by timestamp
                    hydration_ref = self.predictions_ref.child('hydration')
                    logger.info(f"Querying Firebase path: predictions/{self.user_id}/hydration")
                    
                    # First try to get all data and filter in code (more reliable)
                    all_results = hydration_ref.get()
                    
                    if all_results:
                        logger.info(f"Raw Firebase hydration data found with {len(all_results)} entries")
                    else:
                        logger.warning(f"No raw Firebase hydration data found for user {self.user_id}")
                    
                    # Convert to list of entries
                    data = []
                    if all_results:
                        for key, value in all_results.items():
                            # Skip if value is not a dictionary or has unexpected format
                            if not isinstance(value, dict):
                                logger.warning(f"Skipping non-dict entry in hydration data: {type(value)}")
                                continue
                                
                            # Get timestamp for filtering
                            entry_timestamp = value.get('timestamp', 0)
                            
                            # Filter by time range
                            if entry_timestamp >= start_timestamp and entry_timestamp <= end_timestamp:
                                # Extract data
                                entry = {'timestamp': entry_timestamp}
                                
                                # Check for different data structures
                                if 'prediction' in value:
                                    prediction = value['prediction']
                                    # Skip if prediction is not a dictionary
                                    if not isinstance(prediction, dict):
                                        logger.warning(f"Skipping entry with non-dict prediction: {type(prediction)}")
                                        continue
                                        
                                    if 'average' in prediction:
                                        average = prediction['average']
                                        # Skip if average is not a dictionary
                                        if not isinstance(average, dict):
                                            logger.warning(f"Skipping entry with non-dict average: {type(average)}")
                                            continue
                                            
                                            # From average data
                                            entry['normal_lips_percentage'] = average.get('normal_lips_percentage', 0)
                                            entry['dry_lips_percentage'] = average.get('dry_lips_percentage', 0)
                                            entry['avg_dryness_score'] = average.get('avg_dryness_score', 0)
                                            entry['total_samples'] = average.get('total_samples', 0)
                                        elif 'hydration_status' in prediction:
                                            # From direct prediction
                                            hydration_status = prediction['hydration_status']
                                            normal = 100 if hydration_status == 'Normal Lips' else 0
                                            dry = 100 if hydration_status == 'Dry Lips' else 0
                                            dryness_score = prediction.get('dryness_score', 0.5)
                                            
                                            entry['normal_lips_percentage'] = normal
                                            entry['dry_lips_percentage'] = dry
                                            entry['avg_dryness_score'] = dryness_score
                                            entry['total_samples'] = 1
                                        else:
                                            # Try to extract any hydration-related data we can find
                                            if 'dryness_score' in prediction:
                                                dryness_score = prediction.get('dryness_score', 0.5)
                                                # Determine status based on score threshold
                                                normal = 100 if dryness_score < 0.5 else 0
                                                dry = 100 if dryness_score >= 0.5 else 0
                                                
                                                entry['normal_lips_percentage'] = normal
                                                entry['dry_lips_percentage'] = dry
                                                entry['avg_dryness_score'] = dryness_score
                                                entry['total_samples'] = 1
                                            else:
                                                # Skip entries with insufficient data
                                                logger.debug(f"Skipping hydration entry with insufficient data")
                                                continue
                                    else:
                                        # Skip entries without prediction data
                                        logger.debug(f"Skipping hydration entry without prediction data")
                                        continue
                                    
                                    # Add to result list
                                    data.append(entry)
                    
                    # Log the data we've collected
                    logger.info(f"Retrieved {len(data)} raw hydration entries for time range")
                    
                    # Group by timeframe (hourly for daily, daily for weekly, etc.)
                    # This helps when we have too many data points
                    grouped_data = self._group_time_series_data(data, start_date, end_date, 'hydration')
                    
                    logger.info(f"Retrieved {len(data)} raw hydration entries, grouped into {len(grouped_data)} entries")
                    return grouped_data
                    
                except Exception as e:
                    logger.error(f"Firebase error fetching hydration data: {e}")
                    logger.error(f"Error details: {str(e)}")
                    return []
            else:
                # Return empty array
                logger.warning(f"Firebase not available. Returning empty hydration data for date range {start_date} to {end_date}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving hydration data for date range: {e}")
            return []
    
    # Sample data generators for testing
    def _generate_sample_posture_data(self, start_date, end_date):
        """Generate sample posture data for testing."""
        import random
        import numpy as np
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate entries for each hour of the day
            for hour in range(8, 18):  # 8 AM to 6 PM
                timestamp = int(datetime.combine(current_date, datetime.min.time().replace(hour=hour)).timestamp() * 1000)
                
                # Generate random percentages with a tendency to improve over time
                good_percentage = max(50, min(95, random.gauss(70, 10) + (hour - 8) * 1.5))
                bad_percentage = 100 - good_percentage
                
                entry = {
                    'timestamp': timestamp,
                    'good_posture_percentage': good_percentage,
                    'bad_posture_percentage': bad_percentage,
                    'total_samples': random.randint(30, 60)
                }
                data.append(entry)
            
            # Move to next day
            current_date += datetime.timedelta(days=1)
        
        return data
    
    def _generate_sample_stress_data(self, start_date, end_date):
        """Generate sample stress data for testing."""
        import random
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate entries for each hour of the day
            for hour in range(8, 18):  # 8 AM to 6 PM
                timestamp = int(datetime.combine(current_date, datetime.min.time().replace(hour=hour)).timestamp() * 1000)
                
                # Stress tends to increase during the day
                low_stress = max(10, min(80, random.gauss(70, 15) - (hour - 8) * 3))
                high_stress = max(5, min(60, random.gauss(10, 5) + (hour - 8) * 2))
                
                # Adjust to ensure percentages add up to 100%
                if low_stress + high_stress > 100:
                    factor = 100 / (low_stress + high_stress)
                    low_stress *= factor
                    high_stress *= factor
                
                medium_stress = 100 - low_stress - high_stress
                
                entry = {
                    'timestamp': timestamp,
                    'low_stress_percentage': low_stress,
                    'medium_stress_percentage': medium_stress,
                    'high_stress_percentage': high_stress,
                    'total_samples': random.randint(30, 60)
                }
                data.append(entry)
            
            # Move to next day
            current_date += datetime.timedelta(days=1)
        
        return data
    
    def _generate_sample_cvs_data(self, start_date, end_date):
        """Generate sample CVS data for testing."""
        import random
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate entries for each hour of the day
            for hour in range(8, 18):  # 8 AM to 6 PM
                timestamp = int(datetime.combine(current_date, datetime.min.time().replace(hour=hour)).timestamp() * 1000)
                
                # Blink patterns tend to worsen during the day
                normal_blink = max(20, min(90, random.gauss(70, 15) - (hour - 8) * 2))
                low_blink = max(5, min(60, random.gauss(15, 10) + (hour - 8) * 1.5))
                
                # Adjust to ensure percentages add up to 100%
                if normal_blink + low_blink > 100:
                    factor = 100 / (normal_blink + low_blink)
                    normal_blink *= factor
                    low_blink *= factor
                
                high_blink = 100 - normal_blink - low_blink
                
                # Blink count decreases as eye fatigue increases
                avg_blink_count = max(10, min(25, random.gauss(18, 3) - (hour - 8) * 0.5))
                
                entry = {
                    'timestamp': timestamp,
                    'avg_blink_count': avg_blink_count,
                    'normal_blink_percentage': normal_blink,
                    'low_blink_percentage': low_blink,
                    'high_blink_percentage': high_blink,
                    'total_samples': random.randint(30, 60)
                }
                data.append(entry)
            
            # Move to next day
            current_date += datetime.timedelta(days=1)
        
        return data
    
    def _generate_sample_hydration_data(self, start_date, end_date):
        """Generate sample hydration data for testing."""
        import random
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate entries for each hour of the day
            for hour in range(8, 18):  # 8 AM to 6 PM
                timestamp = int(datetime.combine(current_date, datetime.min.time().replace(hour=hour)).timestamp() * 1000)
                
                # Hydration tends to decrease during the day
                normal_lips = max(40, min(95, random.gauss(80, 10) - (hour - 8) * 2))
                dry_lips = 100 - normal_lips
                
                # Dryness score (0-1 scale)
                avg_dryness_score = max(0.1, min(0.9, random.gauss(0.3, 0.1) + (hour - 8) * 0.02))
                
                entry = {
                    'timestamp': timestamp,
                    'normal_lips_percentage': normal_lips,
                    'dry_lips_percentage': dry_lips,
                    'avg_dryness_score': avg_dryness_score,
                    'total_samples': random.randint(30, 60)
                }
                data.append(entry)
            
            # Move to next day
            current_date += datetime.timedelta(days=1)
        
        return data