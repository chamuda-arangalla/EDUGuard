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
import firebase_admin
from firebase_admin import credentials, db

# Configure logging
logger = logging.getLogger('HydrationAPI')

# Create blueprint for hydration-related endpoints
hydration_bp = Blueprint('hydration', __name__, url_prefix='/api/hydration')

# Global dictionary to track active hydration monitoring processes
active_monitoring = {}
monitoring_lock = threading.Lock()

class HydrationMonitoringManager:
    """Manages hydration monitoring processes for users"""
    
    def __init__(self):
        self.processes = {}
        self.webcam_process = None
        
    def start_webcam_server(self):
        """Start the webcam server if not already running"""
        try:
            # Import posture_api monitoring manager here to avoid circular imports
            from posture_api import monitoring_manager as posture_monitoring_manager
            
            # Check if webcam server is already running in posture API
            if posture_monitoring_manager.webcam_process and posture_monitoring_manager.webcam_process.poll() is None:
                logger.info("Reusing webcam server from posture monitoring")
                self.webcam_process = posture_monitoring_manager.webcam_process
                return True, "Reusing existing webcam server"
            
            # Check if webcam server is already running
            if self.webcam_process and self.webcam_process.poll() is None:
                logger.info("Webcam server is already running")
                return True, "Webcam server is already running"
                
            # Start webcam server
            script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modelScrpits')
            webcam_script = os.path.join(script_dir, 'webcam_server.py')
            
            logger.info(f"Starting webcam server: {webcam_script}")
            
            # Get the directory of the backend folder for correct working directory
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            
            self.webcam_process = subprocess.Popen([
                sys.executable, webcam_script
            ], cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it time to start
            time.sleep(3)
            
            # Check if it started successfully
            if self.webcam_process.poll() is None:
                logger.info("Webcam server started successfully")
                # Make this webcam process available to posture monitoring
                posture_monitoring_manager.webcam_process = self.webcam_process
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
            # Import posture_api monitoring manager here to avoid circular imports
            from posture_api import monitoring_manager as posture_monitoring_manager
            
            if not self.webcam_process:
                return True, "No webcam server is running"
                
            if self.webcam_process.poll() is not None:
                self.webcam_process = None
                return True, "Webcam server was not running"
            
            # Check if posture monitoring is using this webcam server
            for user_id, process in posture_monitoring_manager.processes.items():
                if process.poll() is None:
                    logger.warning("Cannot stop webcam server: Posture monitoring is using it")
                    return False, "Cannot stop webcam server while posture monitoring is active"
            
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
            # Also clear the reference in posture monitoring
            if posture_monitoring_manager.webcam_process == self.webcam_process:
                posture_monitoring_manager.webcam_process = None
                
            logger.info("Webcam server stopped successfully")
            return True, "Webcam server stopped successfully"
            
        except Exception as e:
            logger.error(f"Error stopping webcam server: {e}")
            return False, str(e)
    
    def start_hydration_monitoring(self, user_id, progress_report_id):
        """Start hydration monitoring for a user"""
        try:
            # Check if already monitoring this user
            if user_id in self.processes:
                process = self.processes[user_id]
                if process.poll() is None:
                    logger.warning(f"Hydration monitoring already active for user {user_id}")
                    return True, "Monitoring already active"
                else:
                    # Process died, remove it
                    del self.processes[user_id]
            
            # Start webcam server first
            webcam_success, webcam_message = self.start_webcam_server()
            if not webcam_success:
                return False, f"Failed to start webcam server: {webcam_message}"
            
            # Start hydration detection
            script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modelScrpits')
            hydration_script = os.path.join(script_dir, 'hydration_detection.py')
            
            logger.info(f"Starting hydration monitoring for user {user_id} with script: {hydration_script}")
            
            # Get the directory of the backend folder for correct working directory
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            
            process = subprocess.Popen([
                sys.executable, hydration_script,
                user_id, progress_report_id
            ], cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Store the process
            self.processes[user_id] = process
            
            # Give it time to start
            time.sleep(2)
            
            # Check if it's still running
            if process.poll() is None:
                logger.info(f"Hydration monitoring started successfully for user {user_id}")
                return True, "Hydration monitoring started successfully"
            else:
                stdout, stderr = process.communicate()
                error_msg = stderr.decode()
                logger.error(f"Hydration monitoring failed to start: {error_msg}")
                if user_id in self.processes:
                    del self.processes[user_id]
                return False, f"Failed to start hydration monitoring: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error starting hydration monitoring for user {user_id}: {e}")
            return False, str(e)
    
    def stop_hydration_monitoring(self, user_id):
        """Stop hydration monitoring for a user"""
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
            
            logger.info(f"Hydration monitoring stopped for user {user_id}")
            return True, "Hydration monitoring stopped successfully"
            
        except Exception as e:
            logger.error(f"Error stopping hydration monitoring for user {user_id}: {e}")
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
                self.stop_hydration_monitoring(user_id)
            
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
monitoring_manager = HydrationMonitoringManager()

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

@hydration_bp.route('/start', methods=['POST'])
def start_hydration_monitoring():
    """Start enhanced hydration monitoring for a user"""
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
            progress_report_id = f"hydration_report_{user_id}_{int(time.time())}"
        
        with monitoring_lock:
            success, message = monitoring_manager.start_hydration_monitoring(user_id, progress_report_id)
            
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
        logger.error(f"Error in start_hydration_monitoring: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@hydration_bp.route('/stop', methods=['POST'])
def stop_hydration_monitoring():
    """Stop hydration monitoring for a user"""
    try:
        user_id = get_user_id_from_request()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        with monitoring_lock:
            success, message = monitoring_manager.stop_hydration_monitoring(user_id)
            
            return jsonify({
                'status': 'success' if success else 'error',
                'message': message,
                'user_id': user_id,
                'monitoring': False
            })
            
    except Exception as e:
        logger.error(f"Error in stop_hydration_monitoring: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@hydration_bp.route('/status', methods=['GET'])
def get_hydration_monitoring_status():
    """Get current hydration monitoring status for a user"""
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
        logger.error(f"Error in get_hydration_monitoring_status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@hydration_bp.route('/data/recent', methods=['GET'])
def get_recent_hydration_data():
    """Get recent hydration data for a user"""
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
        predictions = db_manager.get_recent_predictions('hydration', minutes=minutes)
        
        # Get average if requested
        average = None
        if include_average:
            average = db_manager.calculate_prediction_average('hydration', minutes=minutes)
        
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
        logger.error(f"Error in get_recent_hydration_data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@hydration_bp.route('/alerts/recent', methods=['GET'])
def get_recent_hydration_alerts():
    """Get recent hydration-related alerts for a user"""
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
        
        # Filter for hydration-related alerts
        hydration_alerts = [alert for alert in all_alerts if alert.get('type') == 'hydration']
        
        return jsonify({
            'status': 'success',
            'data': {
                'alerts': hydration_alerts,
                'total_count': len(hydration_alerts),
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_recent_hydration_alerts: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@hydration_bp.route('/check-alerts', methods=['POST'])
def trigger_hydration_alert_check():
    """Manually trigger a hydration alert check for a user"""
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
        
        # Check for hydration alerts
        alert_manager.check_hydration_alert()
        
        # Get the latest hydration data
        average = db_manager.calculate_prediction_average('hydration', minutes=5)
        
        return jsonify({
            'status': 'success',
            'message': 'Alert check completed',
            'data': {
                'hydration_average': average,
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in trigger_hydration_alert_check: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@hydration_bp.route('/webcam/start', methods=['POST'])
def start_webcam_server():
    """Start only the webcam server without hydration monitoring"""
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

@hydration_bp.route('/webcam/stop', methods=['POST'])
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
def cleanup_hydration_monitoring():
    """Clean up all hydration monitoring processes"""
    monitoring_manager.cleanup()

# Register cleanup function
import atexit
atexit.register(cleanup_hydration_monitoring) 