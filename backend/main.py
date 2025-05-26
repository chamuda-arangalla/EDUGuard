"""
EDUGuard Backend Main Entry Point

This module serves as the central entry point for the EDUGuard backend application,
providing a clean, organized structure for all monitoring services.

Usage:
    python main.py [--debug] [--port PORT] [--host HOST]
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Flask and configuration imports
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Import API modules
from posture_api import posture_bp, monitoring_manager as posture_monitoring
from stress_api import stress_bp, monitoring_manager as stress_monitoring
from cvs_api import cvs_bp, monitoring_manager as cvs_monitoring
from hydration_api import hydration_bp, monitoring_manager as hydration_monitoring
from reports_api import reports_bp

# Import utilities
from utils.database import DatabaseManager


def setup_logging(debug=False):
    """Configure application logging"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Create a custom formatter that handles emoji characters properly
    class EmojiSafeFormatter(logging.Formatter):
        def format(self, record):
            try:
                return super().format(record)
            except UnicodeEncodeError:
                # Replace emojis with their text descriptions
                msg = record.getMessage()
                # We've already replaced all emoji characters with text alternatives,
                # so this is just a safety measure for any future emojis
                
                # Create a new record with the sanitized message
                new_record = logging.LogRecord(
                    record.name, record.levelno, record.pathname, record.lineno,
                    msg, record.args, record.exc_info, record.funcName
                )
                return super().format(new_record)
    
    # Create formatter with the standard format
    formatter = EmojiSafeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler with the emoji-safe formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create application logger
    logger = logging.getLogger('EDUGuard-Backend')
    logger.info(f"Logging initialized at level: {logging.getLevelName(log_level)}")
    return logger


def create_app(test_config=None):
    """Create and configure the Flask application"""
    # Load environment variables
    load_dotenv()
    
    # Initialize Flask application
    app = Flask(__name__)
    
    # Enable CORS for all routes and origins with more explicit configuration
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}},
         allow_headers=["Content-Type", "Authorization", "X-User-ID", "X-User-Id", "x-user-id"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         supports_credentials=True)
    
    # Additional CORS handling for preflight requests
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-ID,X-User-Id,x-user-id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # Register API blueprints
    app.register_blueprint(posture_bp)
    app.register_blueprint(stress_bp)
    app.register_blueprint(cvs_bp)
    app.register_blueprint(hydration_bp)
    app.register_blueprint(reports_bp)
    
    # Import routes from app.py
    from app import register_app_routes
    register_app_routes(app)
    
    return app


def initialize_firebase():
    """Initialize Firebase connection"""
    try:
        import firebase_config
        logging.info("Firebase configuration loaded")
        return True
    except Exception as e:
        logging.error(f"Error loading Firebase configuration: {e}")
        return False


def cleanup_resources():
    """Clean up all resources when shutting down"""
    logging.info("Cleaning up resources...")
    
    # Cleanup all monitoring managers
    posture_monitoring.cleanup()
    stress_monitoring.cleanup()
    cvs_monitoring.cleanup()
    hydration_monitoring.cleanup()
    
    logging.info("All resources cleaned up")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='EDUGuard Backend Server')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--port', type=int, default=int(os.getenv('FLASK_PORT', '5000')),
                        help='Port to run the server on')
    parser.add_argument('--host', type=str, default=os.getenv('FLASK_HOST', '0.0.0.0'),
                        help='Host to run the server on')
    return parser.parse_args()


def main():
    """Main entry point for the application"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(args.debug)
    logger.info(f"Starting EDUGuard Backend at {datetime.now().isoformat()}")
    
    # Initialize Firebase
    firebase_initialized = initialize_firebase()
    if not firebase_initialized:
        logger.warning("Firebase initialization failed, some features may not work correctly")
    
    # Create and configure the Flask app
    app = create_app()
    
    # Register cleanup function
    import atexit
    atexit.register(cleanup_resources)
    
    # Start the Flask server
    logger.info(f"Starting Flask server on {args.host}:{args.port} (Debug mode: {args.debug})")
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == '__main__':
    main() 