"""
Hydration Monitoring API

This module provides Flask endpoints for hydration monitoring functionality,
including starting/stopping monitoring, retrieving data, and managing alerts.
"""

from flask import Flask, request, jsonify, Blueprint
import os
import sys
import time
import threading
import logging
import json
import traceback
from datetime import datetime

# Import local modules
from utils.database import DatabaseManager
from utils.alert_manager import AlertManager
from utils.script_manager import script_manager

# Configure logging with more detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hydration_api.log'))
    ]
)
logger = logging.getLogger('HydrationAPI')
logger.info("Hydration API module initialized")

# Create blueprint for hydration-related endpoints
hydration_bp = Blueprint('hydration', __name__, url_prefix='/api/hydration')

# Global lock for thread safety
monitoring_lock = threading.Lock()


def get_user_id_from_request():
    """
    Get the user ID from the request
    
    Returns:
        str or None: User ID if found, None otherwise
    """
    # Try query params first
    user_id = request.args.get('userId')
    if user_id:
        logger.debug(f"Found user ID in query params: {user_id}")
        return user_id
    
    # Try headers
    user_id = request.headers.get('X-User-ID') or request.headers.get('x-user-id')
    if user_id:
        logger.debug(f"Found user ID in headers: {user_id}")
        return user_id
    
    # Try JSON body
    if request.is_json and request.json:
        user_id = request.json.get('userId')
        if user_id:
            logger.debug(f"Found user ID in JSON body: {user_id}")
            return user_id
    
    logger.warning("No user ID found in request")
    return None


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@hydration_bp.route('/start', methods=['POST'])
def start_hydration_monitoring():
    """Start enhanced hydration monitoring for a user"""
    try:
        logger.info("Received request to start hydration monitoring")
        logger.debug(f"Request headers: {request.headers}")
        logger.debug(f"Request body: {request.get_json(silent=True)}")
        
        user_id = get_user_id_from_request()
        if not user_id:
            logger.error("No user ID provided in request")
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        logger.info(f"Starting hydration monitoring for user: {user_id}")
        
        # Generate a progress report ID (could be passed from frontend)
        progress_report_id = request.json.get('progressReportId') if request.is_json else None
        if not progress_report_id:
            progress_report_id = f"hydration_report_{user_id}_{int(time.time())}"
            logger.debug(f"Generated progress report ID: {progress_report_id}")
        
        with monitoring_lock:
            # Check if webcam server is already running by checking any monitoring status
            # This works because all monitoring types share the same webcam server
            posture_status = script_manager.get_monitoring_status('posture', user_id)
            stress_status = script_manager.get_monitoring_status('stress', user_id)
            cvs_status = script_manager.get_monitoring_status('cvs', user_id)
            hydration_status = script_manager.get_monitoring_status('hydration', user_id)
            
            webcam_server_active = (
                posture_status.get('webcam_server_active', False) or
                stress_status.get('webcam_server_active', False) or
                cvs_status.get('webcam_server_active', False) or
                hydration_status.get('webcam_server_active', False)
            )
            
            logger.info(f"Webcam server status check: {webcam_server_active}")
            
            # Use socket connection check to verify webcam server status
            webcam_running = script_manager._check_webcam_server_running()
            logger.info(f"Socket connection check for webcam server: {webcam_running}")
            
            # If the status says it's not active but socket check says it is, update our understanding
            if not webcam_server_active and webcam_running:
                webcam_server_active = True
                logger.info("Webcam server is actually running according to socket check")
            
            # Only start webcam server if it's not already running
            if not webcam_server_active and not webcam_running:
                logger.info("Webcam server not running, starting it first")
                webcam_success, webcam_message = script_manager.start_webcam_server()
                if not webcam_success:
                    logger.error(f"Failed to start webcam server: {webcam_message}")
                    return jsonify({
                        'status': 'error',
                        'message': f"Failed to start webcam server: {webcam_message}",
                        'user_id': user_id,
                        'monitoring': False
                    }), 500
                logger.info("Webcam server started successfully")
                # Wait a moment for webcam server to initialize
                time.sleep(2)
            else:
                logger.info("Webcam server is already running, skipping startup")
            
            logger.info("Starting hydration monitoring process")
            success, message = script_manager.start_monitoring('hydration', user_id, progress_report_id)
            
            if success:
                logger.info(f"Hydration monitoring started successfully for user {user_id}")
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'user_id': user_id,
                    'progress_report_id': progress_report_id,
                    'monitoring': True
                })
            else:
                logger.error(f"Failed to start hydration monitoring: {message}")
                return jsonify({
                    'status': 'error',
                    'message': message,
                    'user_id': user_id,
                    'monitoring': False
                }), 500
                
    except Exception as e:
        logger.error(f"Error in start_hydration_monitoring: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@hydration_bp.route('/stop', methods=['POST'])
def stop_hydration_monitoring():
    """Stop hydration monitoring for a user"""
    try:
        logger.info("Received request to stop hydration monitoring")
        
        user_id = get_user_id_from_request()
        if not user_id:
            logger.error("No user ID provided in request")
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        logger.info(f"Stopping hydration monitoring for user: {user_id}")
        
        with monitoring_lock:
            success, message = script_manager.stop_monitoring('hydration', user_id)
            
            if success:
                logger.info(f"Hydration monitoring stopped successfully for user {user_id}")
            else:
                logger.warning(f"Issue stopping hydration monitoring: {message}")
                
            return jsonify({
                'status': 'success' if success else 'error',
                'message': message,
                'user_id': user_id,
                'monitoring': False
            })
            
    except Exception as e:
        logger.error(f"Error in stop_hydration_monitoring: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@hydration_bp.route('/status', methods=['GET'])
def get_hydration_monitoring_status():
    """Get current hydration monitoring status for a user"""
    try:
        logger.info("Received request to get hydration monitoring status")
        
        user_id = get_user_id_from_request()
        if not user_id:
            logger.error("No user ID provided in request")
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        logger.info(f"Getting hydration monitoring status for user: {user_id}")
        
        status = script_manager.get_monitoring_status('hydration', user_id)
        logger.debug(f"Status: {status}")
        
        return jsonify({
            'status': 'success',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Error in get_hydration_monitoring_status: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@hydration_bp.route('/data/recent', methods=['GET'])
def get_recent_hydration_data():
    """Get recent hydration data for a user"""
    try:
        logger.info("Received request to get recent hydration data")
        
        user_id = get_user_id_from_request()
        if not user_id:
            logger.error("No user ID provided in request")
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        # Get query parameters
        minutes = int(request.args.get('minutes', '5'))
        include_average = request.args.get('includeAverage', 'true').lower() == 'true'
        
        logger.info(f"Getting hydration data for user {user_id}, minutes={minutes}, includeAverage={include_average}")
        
        # Initialize database manager
        db_manager = DatabaseManager(user_id)
        
        # Get recent predictions
        predictions = db_manager.get_recent_predictions('hydration', minutes=minutes)
        
        # Get average if requested
        avg_data = None
        if include_average:
            raw_average = db_manager.calculate_prediction_average('hydration', minutes=minutes)
            
            # Check if we have data and format it according to frontend expectations
            if raw_average and isinstance(raw_average, dict):
                # Get values or provide defaults
                dry_percentage = raw_average.get('dry_lips_percentage', 0)
                normal_percentage = raw_average.get('normal_lips_percentage', 100)
                total_samples = raw_average.get('total_samples', 0)
                
                # Calculate count values based on percentages (if available)
                dry_count = int(dry_percentage * total_samples / 100) if total_samples > 0 else 0
                normal_count = int(normal_percentage * total_samples / 100) if total_samples > 0 else 1
                
                # Create the expected format
                avg_data = {
                    'dry_lips_count': dry_count,
                    'normal_lips_count': normal_count,
                    'dry_lips_percentage': dry_percentage,
                    'normal_lips_percentage': normal_percentage,
                    'avg_dryness_score': raw_average.get('avg_dryness_score', 0.1),
                    'total_samples': total_samples,
                    'samples': total_samples
                }
            else:
                # Provide default values if no data available
                avg_data = {
                    'dry_lips_count': 0,
                    'normal_lips_count': 1,
                    'dry_lips_percentage': 0.0,
                    'normal_lips_percentage': 100.0,
                    'avg_dryness_score': 0.1,
                    'total_samples': 0,
                    'samples': 0
                }
        
        logger.debug(f"Retrieved {len(predictions)} predictions, average: {avg_data}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'predictions': predictions,
                'average': avg_data,
                'minutes': minutes,
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_recent_hydration_data: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@hydration_bp.route('/alerts/recent', methods=['GET'])
def get_recent_hydration_alerts():
    """Get recent hydration-related alerts for a user"""
    try:
        logger.info("Received request to get recent hydration alerts")
        
        user_id = get_user_id_from_request()
        if not user_id:
            logger.error("No user ID provided in request")
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        limit = int(request.args.get('limit', '20'))
        logger.info(f"Getting hydration alerts for user {user_id}, limit={limit}")
        
        # Initialize database manager
        db_manager = DatabaseManager(user_id)
        
        # Get recent alerts
        all_alerts = db_manager.get_recent_alerts(limit)
        
        # Filter for hydration-related alerts
        hydration_alerts = [alert for alert in all_alerts if alert.get('type') == 'hydration']
        
        logger.debug(f"Retrieved {len(hydration_alerts)} hydration alerts")
        
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
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@hydration_bp.route('/check-alerts', methods=['POST'])
def trigger_hydration_alert_check():
    """Manually trigger a hydration alert check for a user"""
    try:
        logger.info("Received request to trigger hydration alert check")
        
        user_id = get_user_id_from_request()
        if not user_id:
            logger.error("No user ID provided in request")
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
        
        logger.info(f"Triggering hydration alert check for user: {user_id}")
        
        # Initialize managers
        db_manager = DatabaseManager(user_id)
        alert_manager = AlertManager(db_manager)
        
        # Check for hydration alerts
        alert_manager.check_hydration_alert()
        
        # Get the latest hydration data
        raw_average = db_manager.calculate_prediction_average('hydration', minutes=5)
        
        # Format the average data in the expected structure
        avg_data = None
        if raw_average and isinstance(raw_average, dict):
            # Get values or provide defaults
            dry_percentage = raw_average.get('dry_lips_percentage', 0)
            normal_percentage = raw_average.get('normal_lips_percentage', 100)
            total_samples = raw_average.get('total_samples', 0)
            
            # Calculate count values based on percentages (if available)
            dry_count = int(dry_percentage * total_samples / 100) if total_samples > 0 else 0
            normal_count = int(normal_percentage * total_samples / 100) if total_samples > 0 else 1
            
            # Create the expected format
            avg_data = {
                'dry_lips_count': dry_count,
                'normal_lips_count': normal_count,
                'dry_lips_percentage': dry_percentage,
                'normal_lips_percentage': normal_percentage,
                'avg_dryness_score': raw_average.get('avg_dryness_score', 0.1),
                'total_samples': total_samples,
                'samples': total_samples
            }
        else:
            # Provide default values if no data available
            avg_data = {
                'dry_lips_count': 0,
                'normal_lips_count': 1,
                'dry_lips_percentage': 0.0,
                'normal_lips_percentage': 100.0,
                'avg_dryness_score': 0.1,
                'total_samples': 0,
                'samples': 0
            }
        
        logger.debug(f"Hydration average: {avg_data}")
        
        return jsonify({
            'status': 'success',
            'message': 'Alert check completed',
            'data': {
                'hydration_average': avg_data,
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in trigger_hydration_alert_check: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@hydration_bp.route('/webcam/start', methods=['POST'])
def start_webcam_server():
    """Start only the webcam server without hydration monitoring"""
    try:
        logger.info("Received request to start webcam server")
        
        with monitoring_lock:
            success, message = script_manager.start_webcam_server()
            
            if success:
                logger.info("Webcam server started successfully")
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'webcam_server_active': True
                })
            else:
                logger.error(f"Failed to start webcam server: {message}")
                return jsonify({
                    'status': 'error',
                    'message': message,
                    'webcam_server_active': False
                }), 500
                
    except Exception as e:
        logger.error(f"Error in start_webcam_server: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e),
            'webcam_server_active': False
        }), 500


@hydration_bp.route('/webcam/stop', methods=['POST'])
def stop_webcam_server():
    """Stop the webcam server"""
    try:
        logger.info("Received request to stop webcam server")
        
        with monitoring_lock:
            success, message = script_manager.stop_webcam_server()
            
            if success:
                logger.info("Webcam server stopped successfully")
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'webcam_server_active': False
                })
            else:
                logger.error(f"Failed to stop webcam server: {message}")
                return jsonify({
                    'status': 'error',
                    'message': message,
                    'webcam_server_active': True
                }), 500
                
    except Exception as e:
        logger.error(f"Error in stop_webcam_server: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Define monitoring_manager for backward compatibility with main.py
class HydrationMonitoringManager:
    """Legacy wrapper around script_manager for backward compatibility"""
    
    def cleanup(self):
        """Clean up hydration monitoring processes"""
        # This is now handled by script_manager
        logger.info("Cleaning up hydration monitoring processes via script_manager")
        pass

# Create instance for backward compatibility
monitoring_manager = HydrationMonitoringManager() 