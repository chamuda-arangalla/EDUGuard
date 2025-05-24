from flask import Flask, request, jsonify, Blueprint
import os
import sys
import subprocess
import signal
import time
import threading
import logging
import json
from datetime import datetime
from utils.database import DatabaseManager
from utils.alert_manager import AlertManager

# Configure logging
logger = logging.getLogger('StressAPI')

# Create blueprint for stress-related endpoints
stress_bp = Blueprint('stress', __name__, url_prefix='/api/stress')

# Global dictionary to track active stress monitoring processes
active_monitoring = {}
monitoring_lock = threading.Lock()

class StressMonitoringManager:
    """Manages stress monitoring processes for users"""
    
    def __init__(self):
        self.processes = {}
        self.webcam_process = None
        
    def start_webcam_server(self):
        """Start the webcam server if not already running"""
        try:
            # Check if webcam server is already running
            if self.webcam_process and self.webcam_process.poll() is None:
                logger.info("Webcam server is already running")
                return True
                
            # Start webcam server
            script_dir = os.path.join(os.path.dirname(__file__), 'modelScrpits')
            webcam_script = os.path.join(script_dir, 'webcam_server.py')
            
            logger.info(f"Starting webcam server: {webcam_script}")
            
            self.webcam_process = subprocess.Popen([
                sys.executable, webcam_script
            ], cwd=script_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it time to start
            time.sleep(3)
            
            # Check if it started successfully
            if self.webcam_process.poll() is None:
                logger.info("Webcam server started successfully")
                return True
            else:
                stdout, stderr = self.webcam_process.communicate()
                logger.error(f"Webcam server failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting webcam server: {e}")
            return False
    
    def start_stress_monitoring(self, user_id, progress_report_id):
        """Start stress monitoring for a user"""
        try:
            # Check if already monitoring this user
            if user_id in self.processes:
                process = self.processes[user_id]
                if process.poll() is None:
                    logger.warning(f"Stress monitoring already active for user {user_id}")
                    return True, "Monitoring already active"
                else:
                    # Process died, remove it
                    del self.processes[user_id]
            
            # Start webcam server first
            if not self.start_webcam_server():
                return False, "Failed to start webcam server"
            
            # Start stress detection
            script_dir = os.path.join(os.path.dirname(__file__), 'modelScrpits')
            stress_script = os.path.join(script_dir, 'stress_detection.py')
            
            logger.info(f"Starting stress monitoring for user {user_id}")
            
            process = subprocess.Popen([
                sys.executable, stress_script,
                user_id, progress_report_id
            ], cwd=script_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Store the process
            self.processes[user_id] = process
            
            # Give it time to start
            time.sleep(2)
            
            # Check if it's still running
            if process.poll() is None:
                logger.info(f"Stress monitoring started successfully for user {user_id}")
                return True, "Stress monitoring started successfully"
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Stress monitoring failed to start: {stderr.decode()}")
                if user_id in self.processes:
                    del self.processes[user_id]
                return False, f"Failed to start stress monitoring: {stderr.decode()}"
                
        except Exception as e:
            logger.error(f"Error starting stress monitoring for user {user_id}: {e}")
            return False, str(e)
    
    def stop_stress_monitoring(self, user_id):
        """Stop stress monitoring for a user"""
        try:
            if user_id not in self.processes:
                return True, "No active monitoring found"
            
            process = self.processes[user_id]
            
            # Terminate the process
            process.terminate()
            
            # Wait for it to stop
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process for user {user_id} didn't terminate gracefully, killing...")
                process.kill()
                process.wait()
            
            # Remove from tracking
            del self.processes[user_id]
            
            logger.info(f"Stress monitoring stopped for user {user_id}")
            return True, "Stress monitoring stopped successfully"
            
        except Exception as e:
            logger.error(f"Error stopping stress monitoring for user {user_id}: {e}")
            return False, str(e)
    
    def get_monitoring_status(self, user_id):
        """Get monitoring status for a user"""
        try:
            is_active = user_id in self.processes and self.processes[user_id].poll() is None
            webcam_active = self.webcam_process is not None and self.webcam_process.poll() is None
            
            return {
                'is_monitoring': is_active,
                'webcam_server_active': webcam_active,
                'user_id': user_id
            }
        except Exception as e:
            logger.error(f"Error getting monitoring status for user {user_id}: {e}")
            return {
                'is_monitoring': False,
                'webcam_server_active': False,
                'user_id': user_id,
                'error': str(e)
            }
    
    def cleanup(self):
        """Clean up all processes"""
        try:
            # Stop all user monitoring processes
            for user_id in list(self.processes.keys()):
                self.stop_stress_monitoring(user_id)
            
            # Stop webcam server
            if self.webcam_process:
                self.webcam_process.terminate()
                try:
                    self.webcam_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.webcam_process.kill()
                    self.webcam_process.wait()
                self.webcam_process = None
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global monitoring manager
monitoring_manager = StressMonitoringManager()

def get_user_id_from_request():
    """Get the user ID from the request"""
    # Try query params first
    user_id = request.args.get('userId')
    if user_id:
        return user_id
    
    # Try headers
    user_id = request.headers.get('X-User-ID') or request.headers.get('x-user-id')
    if user_id:
        return user_id
    
    # Try JSON body
    if request.is_json and request.json:
        user_id = request.json.get('userId')
        if user_id:
            return user_id
    
    return None

@stress_bp.route('/start', methods=['POST'])
def start_stress_monitoring():
    """Start stress monitoring for a user"""
    try:
        user_id = get_user_id_from_request()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        # Generate a progress report ID (could be passed from frontend)
        progress_report_id = request.json.get('progressReportId') if request.is_json else None
        if not progress_report_id:
            progress_report_id = f"stress_report_{user_id}_{int(time.time())}"
        
        with monitoring_lock:
            success, message = monitoring_manager.start_stress_monitoring(user_id, progress_report_id)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'user_id': user_id,
                    'progress_report_id': progress_report_id,
                    'monitoring': True
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': message,
                    'user_id': user_id,
                    'monitoring': False
                }), 500
                
    except Exception as e:
        logger.error(f"Error in start_stress_monitoring: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@stress_bp.route('/stop', methods=['POST'])
def stop_stress_monitoring():
    """Stop stress monitoring for a user"""
    try:
        user_id = get_user_id_from_request()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        with monitoring_lock:
            success, message = monitoring_manager.stop_stress_monitoring(user_id)
            
            return jsonify({
                'status': 'success' if success else 'error',
                'message': message,
                'user_id': user_id,
                'monitoring': False
            })
            
    except Exception as e:
        logger.error(f"Error in stop_stress_monitoring: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@stress_bp.route('/status', methods=['GET'])
def get_stress_monitoring_status():
    """Get current stress monitoring status for a user"""
    try:
        user_id = get_user_id_from_request()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        status = monitoring_manager.get_monitoring_status(user_id)
        
        return jsonify({
            'status': 'success',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Error in get_stress_monitoring_status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@stress_bp.route('/data/recent', methods=['GET'])
def get_recent_stress_data():
    """Get recent stress data for a user"""
    try:
        user_id = get_user_id_from_request()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        # Get query parameters
        minutes = int(request.args.get('minutes', '5'))
        include_average = request.args.get('includeAverage', 'true').lower() == 'true'
        
        # Initialize database manager
        db_manager = DatabaseManager(user_id)
        
        # Get recent predictions
        predictions = db_manager.get_recent_predictions('stress', minutes=minutes)
        
        # Get average if requested
        average = None
        if include_average:
            average = db_manager.calculate_prediction_average('stress', minutes=minutes)
        
        return jsonify({
            'status': 'success',
            'data': {
                'predictions': predictions,
                'average': average,
                'minutes': minutes,
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_recent_stress_data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@stress_bp.route('/alerts/recent', methods=['GET'])
def get_recent_stress_alerts():
    """Get recent stress-related alerts for a user"""
    try:
        user_id = get_user_id_from_request()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        limit = int(request.args.get('limit', '20'))
        
        # Initialize database manager
        db_manager = DatabaseManager(user_id)
        
        # Get recent alerts
        all_alerts = db_manager.get_recent_alerts(limit)
        
        # Filter for stress-related alerts
        stress_alerts = [alert for alert in all_alerts if alert.get('type') == 'stress']
        
        return jsonify({
            'status': 'success',
            'data': {
                'alerts': stress_alerts,
                'total_count': len(stress_alerts),
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_recent_stress_alerts: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@stress_bp.route('/check-alerts', methods=['POST'])
def trigger_stress_alert_check():
    """Manually trigger a stress alert check for a user"""
    try:
        user_id = get_user_id_from_request()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        # Initialize managers
        db_manager = DatabaseManager(user_id)
        alert_manager = AlertManager(db_manager)
        
        # Check for stress alerts
        alert_manager.check_stress_alert()
        
        # Get the latest stress data
        average = db_manager.calculate_prediction_average('stress', minutes=5)
        
        return jsonify({
            'status': 'success',
            'message': 'Alert check completed',
            'data': {
                'stress_average': average,
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in trigger_stress_alert_check: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Cleanup function to be called when the app shuts down
def cleanup_stress_monitoring():
    """Clean up all stress monitoring processes"""
    monitoring_manager.cleanup()

# Register cleanup function
import atexit
atexit.register(cleanup_stress_monitoring) 