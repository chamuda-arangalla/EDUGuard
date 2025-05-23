from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Import local modules
from utils.database import DatabaseManager

# Import the posture API blueprint
from posture_api import posture_bp

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EDUGuard-Backend')

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register the posture API blueprint
app.register_blueprint(posture_bp)

def get_user_id_from_request():
    """Get the user ID from the request headers or parameters"""
    # Debug log the headers
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Try to get from query params first
    user_id = request.args.get('userId')
    if user_id:
        logger.debug(f"Using user ID from query params: {user_id}")
        return user_id
    
    # Try to get from headers
    user_id = request.headers.get('X-User-ID') or request.headers.get('X-User-Id') or request.headers.get('x-user-id')
    if user_id:
        logger.debug(f"Using user ID from header: {user_id}")
        return user_id
    
    logger.warning("No user ID found in request")
    return None

# User Authentication and Profile Management Routes

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Email and password required'}), 400
    
    try:
        from firebase_admin import auth
        
        # Create Firebase user
        user = auth.create_user(
            email=data['email'],
            password=data['password']
        )
        
        # Create user profile in database
        user_data = {
            'email': data['email'],
            'createdAt': datetime.now().isoformat(),
            'displayName': data.get('displayName', data['email'].split('@')[0]),
            'lastLogin': datetime.now().isoformat(),
        }
        
        # Create user profile document
        db_manager = DatabaseManager(user.uid)
        db_manager.create_user_profile(user_data)
        
        logger.info(f"✅ User registered successfully: {user.uid}")
        return jsonify({'status': 'success', 'uid': user.uid, 'user': user_data})
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    """Login a user and update profile"""
    user_id = get_user_id_from_request()
    
    if not user_id:
        return jsonify({'status': 'error', 'message': 'User ID is required'}), 400
    
    try:
        # Get or create user profile
        db_manager = DatabaseManager(user_id)
        user_data = db_manager.get_user_profile()
        
        if not user_data:
            # Create a basic profile if it doesn't exist
            user_data = {
                'uid': user_id,
                'email': f"user-{user_id[:8]}@eduguard.com",
                'displayName': f"User-{user_id[:8]}",
                'createdAt': datetime.now().isoformat(),
                'lastLogin': datetime.now().isoformat()
            }
            db_manager.create_user_profile(user_data)
            logger.info(f"✅ Created new user profile for: {user_id}")
        else:
            # Update last login time
            update_data = {'lastLogin': datetime.now().isoformat()}
            db_manager.update_user_profile(update_data)
            user_data.update(update_data)
            logger.info(f"✅ User login updated: {user_id}")
        
        return jsonify({
            'status': 'success',
            'uid': user_id,
            'user': user_data
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get a user's profile"""
    user_id = get_user_id_from_request()
    logger.info(f"GET /api/user/profile - User ID: {user_id}")
    
    if not user_id:
        logger.error("Profile request missing user ID")
        return jsonify({'status': 'error', 'message': 'User ID is required'}), 400
    
    try:
        db_manager = DatabaseManager(user_id)
        profile = db_manager.get_user_profile()
        logger.info(f"Retrieved profile for user {user_id}: {profile}")
        
        if not profile:
            logger.warning(f"No profile found for user {user_id}")
            # Return minimal profile rather than 404 to prevent frontend errors
            minimal_profile = {
                'uid': user_id,
                'email': f"user-{user_id[:6]}@eduguard.com",
                'displayName': f"User-{user_id[:6]}",
                'createdAt': datetime.now().isoformat()
            }
            # Return both formats for backward compatibility
            return jsonify({
                'status': 'success',
                'profile': minimal_profile,
                'user': minimal_profile
            })
        
        # Return both formats for backward compatibility
        return jsonify({
            'status': 'success',
            'profile': profile,
            'user': profile
        })
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/user/profile', methods=['PUT'])
def update_user_profile():
    """Update a user's profile"""
    user_id = get_user_id_from_request()
    logger.info(f"PUT /api/user/profile - User ID: {user_id}")
    
    if not user_id:
        logger.error("Profile update missing user ID")
        return jsonify({'status': 'error', 'message': 'User ID is required'}), 400
    
    data = request.json
    if not data:
        logger.error(f"No data provided in profile update for user {user_id}")
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    logger.info(f"Updating profile for user {user_id} with data: {data}")
    
    try:
        # Add last updated timestamp
        data['lastUpdated'] = int(datetime.now().timestamp() * 1000)
        
        db_manager = DatabaseManager(user_id)
        db_manager.update_user_profile(data)
        
        # Get the updated profile to return
        updated_profile = db_manager.get_user_profile()
        
        return jsonify({
            'status': 'success', 
            'message': 'Profile updated successfully',
            'profile': updated_profile,
            'user': updated_profile
        })
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'EDUGuard Backend',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Initialize Firebase
    try:
        import firebase_config
        logger.info("Firebase configuration loaded")
    except Exception as e:
        logger.error(f"Error loading Firebase configuration: {e}")
    
    # Start the Flask server
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Starting Flask server on {host}:{port} (Debug mode: {debug_mode})")
    app.run(host=host, port=port, debug=debug_mode, threaded=True) 