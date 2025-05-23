import time
import datetime
import os
import json
import logging
from datetime import datetime

# Configure logger
logger = logging.getLogger('EDUGuard.Database')

class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, user_id):
        """Initialize the database manager for a specific user.
        
        Args:
            user_id (str): The ID of the user.
        """
        self.user_id = user_id
        self.db_type = os.getenv('DB_TYPE', 'firebase')
        
        if self.db_type == 'firebase':
            self._init_firebase()
        else:
            self._init_local_db()
    
    def _init_firebase(self):
        """Initialize Firebase database references"""
        try:
            # Import here to avoid import errors if Firebase is not available
            from firebase_admin import db
            
            self.predictions_ref = db.reference(f'predictions/{self.user_id}')
            self.alerts_ref = db.reference(f'alerts/{self.user_id}')
            self.users_ref = db.reference(f'users/{self.user_id}')
            self.user_status_ref = db.reference(f'user_status/{self.user_id}')
            self.db_initialized = True
            logger.info(f"Firebase database initialized for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error initializing Firebase database: {e}")
            self._init_local_db()
    
    def _init_local_db(self):
        """Initialize local database for testing and offline operation"""
        self.local_db = {
            'predictions': {},
            'alerts': {},
            'user_status': {},
            'user_profile': {}
        }
        self.db_initialized = True
        logger.info(f"Local database initialized for user {self.user_id}")
    
    def save_prediction(self, model_name, prediction, timestamp=None):
        """Save a single model prediction to the database.
        
        Args:
            model_name (str): The name of the model (e.g., 'attention', 'emotion').
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
                key = model_ref.push().key
                model_ref.child(key).set(data)
                
                # Also update the latest prediction
                self.user_status_ref.child('latest_predictions').child(model_name).set({
                    **data,
                    'prediction_id': key
                })
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
            
            return key
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return None
    
    def save_alert(self, alert_type, message, level='warning', data=None, timestamp=None):
        """Save an alert to the database.
        
        Args:
            alert_type (str): The type of alert (e.g., 'attention', 'absence').
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
                key = self.alerts_ref.push().key
                self.alerts_ref.child(key).set(alert_data)
                
                # Update latest alert
                self.user_status_ref.child('latest_alert').set({
                    **alert_data,
                    'alert_id': key
                })
            else:
                # Local DB operation
                key = f"{int(time.time())}-{id(alert_data)}"
                self.local_db['alerts'][key] = alert_data
                
                # Update latest alert
                self.local_db['user_status']['latest_alert'] = {
                    **alert_data,
                    'alert_id': key
                }
            
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
                # Query alerts ordered by timestamp
                query = self.alerts_ref.order_by_child('timestamp').limit_to_last(limit).get()
                
                if query:
                    # Convert to list and add ID
                    alerts = [{'id': key, **value} for key, value in query.items()]
                    # Sort by timestamp (newest first)
                    alerts.sort(key=lambda a: a.get('timestamp', 0), reverse=True)
                    return alerts
                return []
            else:
                # Local DB operation
                alerts = [{'id': key, **value} for key, value in self.local_db['alerts'].items()]
                alerts.sort(key=lambda a: a.get('timestamp', 0), reverse=True)
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
                # Query predictions
                model_ref = self.predictions_ref.child(model_name)
                # Firebase queries are limited, so we'll query by limit and filter in Python
                query = model_ref.order_by_child('timestamp').limit_to_last(limit).get()
                
                # Filter to only include predictions within the time window
                if query:
                    recent_predictions = [
                        {**prediction, 'id': key} 
                        for key, prediction in query.items() 
                        if prediction.get('timestamp', 0) >= cutoff_time
                    ]
                    return recent_predictions
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
            # Extract and average values based on model type
            if model_name == 'face_count':
                # Average number of faces detected
                face_counts = [p['prediction'].get('face_count', 0) for p in predictions]
                return {
                    'average_face_count': sum(face_counts) / len(face_counts),
                    'samples': len(predictions)
                }
                
            elif model_name == 'emotion':
                # For emotion, average the emotion probabilities
                emotion_sums = {}
                emotion_counts = {}
                
                for pred in predictions:
                    emotions = pred.get('prediction', {}).get('emotion', {})
                    for emotion, value in emotions.items():
                        if emotion not in emotion_sums:
                            emotion_sums[emotion] = 0
                            emotion_counts[emotion] = 0
                        emotion_sums[emotion] += float(value)
                        emotion_counts[emotion] += 1
                
                # Calculate averages
                avg_emotions = {
                    emotion: (emotion_sums[emotion] / emotion_counts[emotion]) 
                    for emotion in emotion_sums
                    if emotion_counts[emotion] > 0
                }
                
                return {
                    'average_emotions': avg_emotions,
                    'samples': len(predictions)
                }
                
            elif model_name == 'attention':
                # Average attention scores
                attention_values = [
                    float(p.get('prediction', {}).get('attention', 0)) 
                    for p in predictions
                ]
                
                if not attention_values:
                    return None
                    
                return {
                    'average_attention': sum(attention_values) / len(attention_values),
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
            else:
                self.local_db['user_status'].update(status_data)
                
            logger.debug(f"Updated monitoring status for user {self.user_id}: {is_monitoring}")
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
                return profile if profile else {}
            else:
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
            else:
                self.local_db['user_profile'] = profile_data
                
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
            else:
                self.local_db['user_profile'].update(update_data)
                
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False 