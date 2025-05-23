import time
import datetime
import numpy as np
from ..firebase_config import get_db_reference

class DatabaseManager:
    """Manager for Firebase Realtime Database operations."""
    
    def __init__(self, user_id):
        """Initialize the database manager for a specific user.
        
        Args:
            user_id (str): The ID of the user.
        """
        self.user_id = user_id
        self.predictions_ref = get_db_reference(f'predictions/{user_id}')
        self.alerts_ref = get_db_reference(f'alerts/{user_id}')
        self.user_status_ref = get_db_reference(f'user_status/{user_id}')
    
    def save_prediction(self, model_name, prediction, timestamp=None):
        """Save a single model prediction to the database.
        
        Args:
            model_name (str): The name of the model (e.g., 'face_recognition', 'emotion').
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
            'created_at': datetime.datetime.now().isoformat()
        }
        
        # Push data to predictions/{user_id}/{model_name}
        model_ref = self.predictions_ref.child(model_name)
        key = model_ref.push().key
        model_ref.child(key).set(data)
        
        # Also update the latest prediction
        self.update_latest_prediction(model_name, prediction, timestamp)
        
        return key
    
    def update_latest_prediction(self, model_name, prediction, timestamp):
        """Update the latest prediction for a model.
        
        Args:
            model_name (str): The name of the model.
            prediction (dict): The prediction data.
            timestamp (int): The timestamp of the prediction.
        """
        latest_data = {
            'model': model_name,
            'prediction': prediction,
            'timestamp': timestamp,
            'updated_at': datetime.datetime.now().isoformat()
        }
        
        # Update latest prediction for the model
        self.user_status_ref.child('latest_predictions').child(model_name).set(latest_data)
    
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
            'created_at': datetime.datetime.now().isoformat(),
            'read': False
        }
        
        # Push alert to alerts/{user_id}
        key = self.alerts_ref.push().key
        self.alerts_ref.child(key).set(alert_data)
        
        # Also update the latest alert
        self.user_status_ref.child('latest_alert').set({
            **alert_data,
            'alert_id': key
        })
        
        return key
    
    def get_recent_predictions(self, model_name, minutes=5, limit=100):
        """Get recent predictions for a specific model.
        
        Args:
            model_name (str): The name of the model.
            minutes (int, optional): Time window in minutes. Defaults to 5.
            limit (int, optional): Maximum number of predictions to retrieve. Defaults to 100.
            
        Returns:
            list: List of recent predictions.
        """
        # Calculate the cutoff timestamp
        cutoff_time = int((time.time() - (minutes * 60)) * 1000)  # milliseconds
        
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
        
        # Extract prediction values based on model type
        if model_name == 'face_recognition':
            # For face recognition, calculate average presence
            presence_values = [p['prediction'].get('present', False) for p in predictions]
            return {
                'average_presence': sum(presence_values) / len(presence_values),
                'samples': len(predictions)
            }
            
        elif model_name == 'emotion':
            # For emotion, average the emotion scores
            emotions = {}
            for pred in predictions:
                for emotion, score in pred['prediction'].get('emotions', {}).items():
                    if emotion not in emotions:
                        emotions[emotion] = []
                    emotions[emotion].append(float(score))
            
            return {
                'average_emotions': {
                    emotion: np.mean(scores) for emotion, scores in emotions.items()
                },
                'samples': len(predictions)
            }
            
        elif model_name == 'attention':
            # For attention, average the attention score
            attention_values = [float(p['prediction'].get('attention_score', 0)) for p in predictions]
            return {
                'average_attention': np.mean(attention_values),
                'samples': len(predictions)
            }
            
        elif model_name == 'posture':
            # For posture, average the posture score
            posture_values = [float(p['prediction'].get('posture_score', 0)) for p in predictions]
            return {
                'average_posture': np.mean(posture_values),
                'samples': len(predictions)
            }
            
        return None
    
    def update_user_monitoring_status(self, is_monitoring):
        """Update the user's monitoring status.
        
        Args:
            is_monitoring (bool): Whether the user is currently being monitored.
        """
        status_data = {
            'is_monitoring': is_monitoring,
            'last_updated': int(time.time() * 1000),
            'last_updated_iso': datetime.datetime.now().isoformat()
        }
        
        self.user_status_ref.update(status_data)
        
    def get_user_monitoring_status(self):
        """Get the user's current monitoring status.
        
        Returns:
            dict: The user's monitoring status.
        """
        return self.user_status_ref.get() 