from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv
import threading
import time

# Local imports
from main import MonitoringApp

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EDUGuard-Server')

app = Flask(__name__)
CORS(app)

# Global monitoring app instance
monitoring_app = None
monitoring_lock = threading.Lock()

def get_user_id_from_request():
    """Get the user ID from the request or environment."""
    # First try to get from query param
    user_id = request.args.get('userId')
    
    # Then try to get from header
    if not user_id:
        user_id = request.headers.get('X-User-ID')
        
    # Finally, try from env var
    if not user_id:
        user_id = os.getenv('USER_ID')
        
    return user_id

def init_monitoring_app(user_id=None):
    """Initialize the monitoring application if not already initialized."""
    global monitoring_app
    
    with monitoring_lock:
        if monitoring_app is None:
            try:
                monitoring_app = MonitoringApp(user_id=user_id)
                logger.info(f"Monitoring app initialized for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to initialize monitoring app: {e}")
                return False
        return True

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current status of the monitoring application."""
    global monitoring_app
    
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
        
    if not init_monitoring_app(user_id):
        return jsonify({'error': 'Failed to initialize monitoring app'}), 500
        
    status = {
        'running': monitoring_app.running,
        'frameCount': monitoring_app.frame_count,
        'userId': monitoring_app.user_id
    }
    
    return jsonify(status)

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start the monitoring process."""
    global monitoring_app
    
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
        
    if not init_monitoring_app(user_id):
        return jsonify({'error': 'Failed to initialize monitoring app'}), 500
        
    with monitoring_lock:
        if monitoring_app.running:
            return jsonify({'message': 'Monitoring is already running', 'status': 'running'})
            
        try:
            monitoring_app.start()
            return jsonify({'message': 'Monitoring started successfully', 'status': 'running'})
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return jsonify({'error': f'Failed to start monitoring: {str(e)}'}), 500

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop the monitoring process."""
    global monitoring_app
    
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
        
    if monitoring_app is None:
        return jsonify({'message': 'Monitoring is not initialized', 'status': 'stopped'})
        
    with monitoring_lock:
        if not monitoring_app.running:
            return jsonify({'message': 'Monitoring is already stopped', 'status': 'stopped'})
            
        try:
            monitoring_app.stop()
            return jsonify({'message': 'Monitoring stopped successfully', 'status': 'stopped'})
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            return jsonify({'error': f'Failed to stop monitoring: {str(e)}'}), 500

@app.route('/api/alerts/recent', methods=['GET'])
def get_recent_alerts():
    """Get recent alerts for the user."""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    # This endpoint doesn't require the monitoring app to be running
    from utils.database import DatabaseManager
    
    try:
        db_manager = DatabaseManager(user_id)
        # Use the alerts reference to get the most recent alerts (limit to 20)
        alerts_ref = db_manager.alerts_ref.order_by_child('timestamp').limit_to_last(20).get()
        
        if alerts_ref is None:
            alerts = []
        else:
            # Convert to list and add ID
            alerts = [{'id': key, **value} for key, value in alerts_ref.items()]
            # Sort by timestamp (newest first)
            alerts.sort(key=lambda a: a.get('timestamp', 0), reverse=True)
            
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return jsonify({'error': f'Failed to get alerts: {str(e)}'}), 500

@app.route('/api/predictions/recent', methods=['GET'])
def get_recent_predictions():
    """Get recent predictions for a specific model."""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
        
    model_name = request.args.get('model')
    if not model_name:
        return jsonify({'error': 'Model name is required'}), 400
        
    minutes = int(request.args.get('minutes', '5'))
    
    # This endpoint doesn't require the monitoring app to be running
    from utils.database import DatabaseManager
    
    try:
        db_manager = DatabaseManager(user_id)
        predictions = db_manager.get_recent_predictions(model_name, minutes=minutes)
        
        # Also get the average if requested
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

def start_server():
    """Start the Flask server with the configured host and port."""
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == '__main__':
    start_server() 