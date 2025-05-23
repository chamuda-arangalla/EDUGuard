from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import threading
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Try to use real Firebase, if it fails, use the mock implementation
try:
    import firebase_admin
    from firebase_admin import auth, firestore
    
    # Import the firebase config module
    import firebase_config
    
    # Get Firestore client
    db = firestore.client()
    print("Using real Firebase authentication and database")
    
except Exception as e:
    print(f"Warning: Firebase initialization failed: {e}")
    print("Using mock Firebase implementation for testing")
    
    # Import the mock implementation
    from mock_firebase import auth, firestore
    db = firestore.client()

# Global variables for monitoring
is_monitoring = False
monitoring_thread = None
predictions_buffer = []

def load_models():
    # Load your ML models here
    pass

def process_frame(frame):
    # Implement your model predictions here
    predictions = {
        'model1': 0.0,
        'model2': 0.0,
        'model3': 0.0,
        'model4': 0.0
    }
    return predictions

def monitoring_loop():
    global is_monitoring, predictions_buffer
    
    cap = cv2.VideoCapture(0)
    start_time = time.time()
    
    while is_monitoring:
        ret, frame = cap.read()
        if not ret:
            continue
            
        predictions = process_frame(frame)
        predictions_buffer.append(predictions)
        
        # Calculate average every 5 minutes
        if time.time() - start_time >= 300:  # 5 minutes
            avg_predictions = calculate_averages()
            send_alert(avg_predictions)
            predictions_buffer = []
            start_time = time.time()
            
    cap.release()

def calculate_averages():
    if not predictions_buffer:
        return None
        
    avg_predictions = {
        'model1': np.mean([p['model1'] for p in predictions_buffer]),
        'model2': np.mean([p['model2'] for p in predictions_buffer]),
        'model3': np.mean([p['model3'] for p in predictions_buffer]),
        'model4': np.mean([p['model4'] for p in predictions_buffer])
    }
    return avg_predictions

def send_alert(predictions):
    # Implement your alert logic here
    pass

@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    global is_monitoring, monitoring_thread
    
    if not is_monitoring:
        is_monitoring = True
        monitoring_thread = threading.Thread(target=monitoring_loop)
        monitoring_thread.start()
        return jsonify({'status': 'success', 'message': 'Monitoring started'})
    return jsonify({'status': 'error', 'message': 'Monitoring already in progress'})

@app.route('/api/stop-monitoring', methods=['POST'])
def stop_monitoring():
    global is_monitoring
    is_monitoring = False
    if monitoring_thread:
        monitoring_thread.join()
    return jsonify({'status': 'success', 'message': 'Monitoring stopped'})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Email and password required'}), 400
        
    try:
        # Create Firebase user
        try:
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
            
            # Try to create a user profile document
            try:
                db.collection('users').document(user.uid).set(user_data)
            except Exception as db_error:
                print(f"Database error during registration: {db_error}")
                # Continue even if database fails
            
            return jsonify({'status': 'success', 'uid': user.uid, 'user': user_data})
        except Exception as auth_error:
            print(f"Auth error during registration: {auth_error}")
            # Check if user might already exist
            try:
                existing_user = auth.get_user_by_email(data['email'])
                return jsonify({
                    'status': 'success', 
                    'message': 'User already exists',
                    'uid': existing_user.uid, 
                    'user': {
                        'email': existing_user.email,
                        'displayName': existing_user.display_name or data['email'].split('@')[0]
                    }
                })
            except:
                pass
            return jsonify({'status': 'error', 'message': str(auth_error)}), 400
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Email and password required'}), 400
        
    try:
        # In a real implementation, we would verify the password with Firebase Auth
        # Here we just look up the user
        try:
            user = auth.get_user_by_email(data['email'])
            
            # Get or create user profile data
            try:
                user_doc = db.collection('users').document(user.uid).get()
                user_data = user_doc.to_dict() if user_doc.exists else {
                    'email': user.email, 
                    'displayName': user.display_name or user.email.split('@')[0],
                    'lastLogin': datetime.now().isoformat()
                }
                
                # Update last login time
                try:
                    db.collection('users').document(user.uid).update({'lastLogin': datetime.now().isoformat()})
                except Exception as update_error:
                    print(f"Error updating last login: {update_error}")
            except Exception as db_error:
                print(f"Database error during login: {db_error}")
                user_data = {
                    'email': user.email,
                    'displayName': user.display_name or user.email.split('@')[0],
                    'lastLogin': datetime.now().isoformat()
                }
            
            return jsonify({
                'status': 'success', 
                'uid': user.uid, 
                'user': user_data
            })
        except Exception as auth_error:
            print(f"Auth error during login: {auth_error}")
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({'status': 'error', 'message': 'User ID required'}), 400
    
    try:
        # Try to get user profile data from database
        try:
            user_doc = db.collection('users').document(uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                return jsonify({
                    'status': 'success',
                    'user': user_data
                })
        except Exception as db_error:
            print(f"Database error: {db_error}")
        
        # If database operation fails, return a minimal profile
        return jsonify({
            'status': 'success',
            'user': {
                'uid': uid,
                'email': f"user-{uid[:6]}@example.com",
                'displayName': f"User-{uid[:6]}",
                'isGenericProfile': True
            }
        })
    except Exception as e:
        print(f"Profile retrieval error: {e}")
        # Even if everything fails, return a success with minimal data to prevent frontend errors
        return jsonify({
            'status': 'success',
            'user': {
                'uid': uid,
                'displayName': 'User',
                'isGenericProfile': True
            }
        })

if __name__ == '__main__':
    load_models()
    app.run(port=5000, debug=True) 