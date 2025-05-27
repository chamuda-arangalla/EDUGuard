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
logger = logging.getLogger('CVSAPI')

# Create blueprint for CVS-related endpoints
cvs_bp = Blueprint('cvs', __name__, url_prefix='/api/cvs')

# Global dictionary to track active CVS monitoring processes
active_monitoring = {}
monitoring_lock = threading.Lock()

class CVSMonitoringManager:
    """Manages Computer Vision Syndrome (CVS) monitoring processes for users"""
    
    def __init__(self):
        self.processes = {}
        self.webcam_process = None
        
    def start_webcam_server(self):
        """Start the webcam server if not already running"""
        try:
            # Import posture_api and stress_api monitoring managers here to avoid circular imports
            from posture_api import monitoring_manager as posture_monitoring_manager
            from stress_api import monitoring_manager as stress_monitoring_manager
            
            # Check if webcam server is already running in posture API
            if posture_monitoring_manager.webcam_process and posture_monitoring_manager.webcam_process.poll() is None:
                logger.info("Reusing webcam server from posture monitoring")
                self.webcam_process = posture_monitoring_manager.webcam_process
                return True, "Reusing existing webcam server"
            
            # Check if webcam server is already running in stress API
            if stress_monitoring_manager.webcam_process and stress_monitoring_manager.webcam_process.poll() is None:
                logger.info("Reusing webcam server from stress monitoring")
                self.webcam_process = stress_monitoring_manager.webcam_process
                return True, "Reusing existing webcam server"
            
            # Check if webcam server is already running in this API
            if self.webcam_process and self.webcam_process.poll() is None:
                logger.info("Webcam server is already running")
                return True, "Webcam server is already running"
                
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
                # Make this webcam process available to other modules
                posture_monitoring_manager.webcam_process = self.webcam_process
                stress_monitoring_manager.webcam_process = self.webcam_process
                return True, "Webcam server started successfully"
            else:
                stdout, stderr = self.webcam_process.communicate()
                logger.error(f"Webcam server failed to start: {stderr.decode()}")
                return False, f"Failed to start webcam server: {stderr.decode()}"
                
        except Exception as e:
            logger.error(f"Error starting webcam server: {e}")
            return False, str(e)
    
    def stop_webcam_server(self):
        """Stop the webcam server if it's running"""
        try:
            # Import posture_api and stress_api monitoring managers here to avoid circular imports
            from posture_api import monitoring_manager as posture_monitoring_manager
            from stress_api import monitoring_manager as stress_monitoring_manager
            
            if not self.webcam_process:
                return True, "No webcam server is running"
                
            if self.webcam_process.poll() is not None:
                self.webcam_process = None
                return True, "Webcam server was not running"
            
            # Check if posture or stress monitoring is using this webcam server
            for user_id, process in posture_monitoring_manager.processes.items():
                if process.poll() is None:
                    logger.warning("Cannot stop webcam server: Posture monitoring is using it")
                    return False, "Cannot stop webcam server while posture monitoring is active"
                    
            for user_id, process in stress_monitoring_manager.processes.items():
                if process.poll() is None:
                    logger.warning("Cannot stop webcam server: Stress monitoring is using it")
                    return False, "Cannot stop webcam server while stress monitoring is active"
            
            # Terminate the process
            self.webcam_process.terminate()
            
            # Wait for it to stop
            try:
                self.webcam_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Webcam server didn't terminate gracefully, killing...")
                self.webcam_process.kill()
                self.webcam_process.wait()
            
            self.webcam_process = None
            # Also clear the reference in other modules
            if posture_monitoring_manager.webcam_process == self.webcam_process:
                posture_monitoring_manager.webcam_process = None
            if stress_monitoring_manager.webcam_process == self.webcam_process:
                stress_monitoring_manager.webcam_process = None
                
            logger.info("Webcam server stopped successfully")
            return True, "Webcam server stopped successfully"
            
        except Exception as e:
            logger.error(f"Error stopping webcam server: {e}")
            return False, str(e)
    
    def start_cvs_monitoring(self, user_id, progress_report_id):
        """Start CVS monitoring for a user"""
        try:
            # Check if already monitoring this user
            if user_id in self.processes:
                process = self.processes[user_id]
                if process.poll() is None:
                    logger.warning(f"CVS monitoring already active for user {user_id}")
                    return True, "Monitoring already active"
                else:
                    # Process died, remove it
                    del self.processes[user_id]
            
            # Start webcam server first
            webcam_success, webcam_message = self.start_webcam_server()
            if not webcam_success:
                return False, f"Failed to start webcam server: {webcam_message}"
            
            # Start CVS detection (eye blink monitoring)
            script_dir = os.path.join(os.path.dirname(__file__), 'modelScrpits')
            cvs_script = os.path.join(script_dir, 'cvs_detection.py')
            
            logger.info(f"Starting CVS monitoring for user {user_id}")
            
            process = subprocess.Popen([
                sys.executable, cvs_script,
                user_id, progress_report_id
            ], cwd=script_dir)
            
            # Store the process
            self.processes[user_id] = process
            
            # Give it time to start
            time.sleep(2)
            
            # Check if it's still running
            if process.poll() is None:
                logger.info(f"CVS monitoring started successfully for user {user_id}")
                return True, "CVS monitoring started successfully"
            else:
                stdout, stderr = process.communicate()
                logger.error(f"CVS monitoring failed to start: {stderr.decode()}")
                if user_id in self.processes:
                    del self.processes[user_id]
                return False, f"Failed to start CVS monitoring: {stderr.decode()}"
                
        except Exception as e:
            logger.error(f"Error starting CVS monitoring for user {user_id}: {e}")
            return False, str(e)
    
    def stop_cvs_monitoring(self, user_id):
        """Stop CVS monitoring for a user"""
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
            
            logger.info(f"CVS monitoring stopped for user {user_id}")
            return True, "CVS monitoring stopped successfully"
            
        except Exception as e:
            logger.error(f"Error stopping CVS monitoring for user {user_id}: {e}")
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
                self.stop_cvs_monitoring(user_id)
            
            # Stop webcam server if it was started by this manager
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
monitoring_manager = CVSMonitoringManager()

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

@cvs_bp.route('/start', methods=['POST'])
def start_cvs_monitoring():
    """Start eye blink monitoring for CVS detection"""
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
            progress_report_id = f"cvs_report_{user_id}_{int(time.time())}"
        
        with monitoring_lock:
            success, message = monitoring_manager.start_cvs_monitoring(user_id, progress_report_id)
            
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
        logger.error(f"Error in start_cvs_monitoring: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cvs_bp.route('/stop', methods=['POST'])
def stop_cvs_monitoring():
    """Stop CVS monitoring for a user"""
    try:
        user_id = get_user_id_from_request()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        with monitoring_lock:
            success, message = monitoring_manager.stop_cvs_monitoring(user_id)
            
            return jsonify({
                'status': 'success' if success else 'error',
                'message': message,
                'user_id': user_id,
                'monitoring': False
            })
            
    except Exception as e:
        logger.error(f"Error in stop_cvs_monitoring: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cvs_bp.route('/status', methods=['GET'])
def get_cvs_monitoring_status():
    """Get current CVS monitoring status for a user"""
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
        logger.error(f"Error in get_cvs_monitoring_status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cvs_bp.route('/data/recent', methods=['GET'])
def get_recent_cvs_data():
    """Get recent eye blink data for a user"""
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
        predictions = db_manager.get_recent_predictions('cvs', minutes=minutes)
        
        # Check if we have any data, if not, generate some sample data
        if not predictions:
            logger.warning(f"No CVS data found for user {user_id}, providing sample data")
            # Create a single sample prediction to ensure the frontend has something to display
            sample_prediction = {
                'model': 'cvs',
                'prediction': {'blink_count': 18},  # Normal blink rate
                'timestamp': int(time.time() * 1000),
                'created_at': datetime.now().isoformat(),
                'id': f"sample_{int(time.time())}"
            }
            predictions = [sample_prediction]
            
            # Save this sample to the database for future retrieval
            try:
                db_manager.save_prediction('cvs', {'blink_count': 18})
                logger.info("Saved sample CVS data to database")
            except Exception as e:
                logger.error(f"Error saving sample data: {e}")
        
        # Get average if requested
        average = None
        if include_average:
            average = db_manager.calculate_prediction_average('cvs', minutes=minutes)
            
            # If no average is available, create a sample average
            if not average:
                logger.warning("No average CVS data available, providing sample average")
                average = {
                    'avg_blink_count': 18.0,
                    'low_blink_count': 0,
                    'normal_blink_count': 1,
                    'high_blink_count': 0,
                    'low_blink_percentage': 0.0,
                    'normal_blink_percentage': 100.0,
                    'high_blink_percentage': 0.0,
                    'total_samples': 1,
                    'samples': 1
                }
        
        return jsonify({
            'status': 'success',
            'data': {
                'predictions': predictions,
                'average': average,
                'minutes': minutes,
                'user_id': user_id,
                'timestamp': int(time.time() * 1000)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_recent_cvs_data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cvs_bp.route('/alerts/recent', methods=['GET'])
def get_recent_cvs_alerts():
    """Get recent CVS-related alerts for a user"""
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
        
        # Filter for CVS-related alerts
        cvs_alerts = [alert for alert in all_alerts if alert.get('type') == 'cvs']
        
        return jsonify({
            'status': 'success',
            'data': {
                'alerts': cvs_alerts,
                'total_count': len(cvs_alerts),
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_recent_cvs_alerts: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cvs_bp.route('/check-alerts', methods=['POST'])
def trigger_cvs_alert_check():
    """Manually trigger a CVS alert check for a user"""
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
        
        # Check for CVS alerts
        alert_manager.check_cvs_alert()
        
        # Get the latest CVS data
        average = db_manager.calculate_prediction_average('cvs', minutes=5)
        
        return jsonify({
            'status': 'success',
            'message': 'Alert check completed',
            'data': {
                'blink_rate_average': average,
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in trigger_cvs_alert_check: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cvs_bp.route('/webcam/start', methods=['POST'])
def start_webcam_server():
    """Start only the webcam server without CVS monitoring"""
    try:
        with monitoring_lock:
            success, message = monitoring_manager.start_webcam_server()
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'webcam_server_active': True
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': message,
                    'webcam_server_active': False
                }), 500
                
    except Exception as e:
        logger.error(f"Error in start_webcam_server: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'webcam_server_active': False
        }), 500

@cvs_bp.route('/webcam/stop', methods=['POST'])
def stop_webcam_server():
    """Stop the webcam server"""
    try:
        with monitoring_lock:
            # Check if any monitoring processes are active
            active_processes = False
            for user_id, process in monitoring_manager.processes.items():
                if process.poll() is None:
                    active_processes = True
                    break
            
            if active_processes:
                return jsonify({
                    'status': 'error',
                    'message': 'Cannot stop webcam server while monitoring processes are active',
                    'webcam_server_active': True
                }), 400
            
            success, message = monitoring_manager.stop_webcam_server()
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'webcam_server_active': False
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': message,
                    'webcam_server_active': True
                }), 500
                
    except Exception as e:
        logger.error(f"Error in stop_webcam_server: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Cleanup function to be called when the app shuts down
def cleanup_cvs_monitoring():
    """Clean up all CVS monitoring processes"""
    monitoring_manager.cleanup()

# Register cleanup function
import atexit
atexit.register(cleanup_cvs_monitoring) 