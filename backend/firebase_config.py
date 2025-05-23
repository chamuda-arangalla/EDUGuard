import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def initialize_firebase():
    """Initialize Firebase Admin SDK for EDUGuard application."""
    try:
        # Check if app is already initialized
        if firebase_admin._apps:
            print("Firebase already initialized.")
            return True
            
        # Service account key path
        SERVICE_ACCOUNT_KEY_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 'serviceAccountKey.json')
        
        # Try to initialize with service account key file
        if os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            print(f"Using Firebase service account key: {SERVICE_ACCOUNT_KEY_PATH}")
            
            # Extract project ID for database URL
            with open(SERVICE_ACCOUNT_KEY_PATH, 'r') as f:
                service_account = json.load(f)
                project_id = service_account.get('project_id', 'eduguard-db')
            
            firebase_db_url = f"https://{project_id}-default-rtdb.firebaseio.com"
            print(f"Database URL: {firebase_db_url}")
            
        # Try environment variable if file doesn't exist
        else:
            service_account_info = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            if service_account_info:
                service_account_dict = json.loads(service_account_info)
                cred = credentials.Certificate(service_account_dict)
                project_id = service_account_dict.get('project_id', 'eduguard-db')
                firebase_db_url = f"https://{project_id}-default-rtdb.firebaseio.com"
                print("Using Firebase service account from environment variable")
            else:
                raise ValueError("No Firebase credentials found. Please provide either a service account key file or environment variable.")
        
        # Initialize the Firebase app
        firebase_admin.initialize_app(cred, {
            'databaseURL': firebase_db_url
        })
        
        print("✅ Firebase initialized successfully for EDUGuard")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")
        return False

def get_db_reference(path):
    """Get a reference to a specific path in the Firebase Realtime Database.
    
    Args:
        path (str): Database path (e.g., 'users/123' or 'predictions')
        
    Returns:
        firebase_admin.db.Reference: Database reference object
    """
    try:
        return db.reference(path)
    except Exception as e:
        print(f"Error getting database reference for path '{path}': {e}")
        return None

# Initialize Firebase when module is imported
firebase_available = False
if __name__ != "__main__":
    try:
        firebase_available = initialize_firebase()
        if firebase_available:
            print("🔥 Firebase is ready for EDUGuard operations")
        else:
            print("⚠️ Firebase initialization failed - using local fallback")
    except Exception as e:
        print(f"Warning: Firebase initialization failed: {e}")
        print("System will use local database for testing.")
        firebase_available = False 