import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Check if we have a service account key file
SERVICE_ACCOUNT_KEY_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 'serviceAccountKey.json')

def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        # Check if app is already initialized
        if not firebase_admin._apps:
            # If we have a service account key file
            if os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
                cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            # Otherwise use the environment variable
            else:
                # Try to load the service account from environment variable
                service_account_info = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
                if service_account_info:
                    service_account_dict = json.loads(service_account_info)
                    cred = credentials.Certificate(service_account_dict)
                else:
                    raise ValueError("No Firebase credentials found. Please provide either a service account key file or environment variable.")
            
            # Firebase database URL
            firebase_db_url = os.getenv('FIREBASE_DATABASE_URL', 'https://eduguard-db-default-rtdb.firebaseio.com')
            
            # Initialize the app
            firebase_admin.initialize_app(cred, {
                'databaseURL': firebase_db_url
            })
            print("Firebase initialized successfully.")
        else:
            print("Firebase already initialized.")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise

def get_db_reference(path):
    """Get a reference to a specific path in the Firebase Realtime Database."""
    return db.reference(path)

# Initialize Firebase when the module is imported
try:
    initialize_firebase()
except Exception as e:
    print(f"Warning: Firebase initialization failed: {e}")
    print("Some functions may not work correctly.") 