"""
Mock Firebase implementation for testing without real Firebase credentials.
This allows the app to run for testing and development without real Firebase.
"""
import logging
import time
import json
from datetime import datetime

# Configure logger
logger = logging.getLogger('EDUGuard.MockFirebase')

# Global in-memory database for the mock implementation
_mock_database = {
    'users': {},
    'predictions': {},
    'alerts': {},
    'user_status': {}
}

def init_mock_firebase():
    """Initialize the mock Firebase implementation"""
    logger.info("Initializing mock Firebase implementation")
    return True

class MockAuth:
    """Mock implementation of Firebase Auth."""
    
    def create_user(self, email, password, display_name=None, phone_number=None):
        """Mock user creation.
        
        Args:
            email (str): User's email
            password (str): User's password (ignored in mock)
            display_name (str, optional): User's display name
            phone_number (str, optional): User's phone number
            
        Returns:
            MockUser: A mock user object
        """
        logger.info(f"Mock Auth: Creating user with email {email}")
        user = MockUser(email=email, display_name=display_name, phone_number=phone_number)
        
        # Store in mock database
        _mock_database['users'][user.uid] = {
            'email': email,
            'display_name': display_name,
            'created_at': datetime.now().isoformat()
        }
        
        return user
    
    def get_user_by_email(self, email):
        """Mock get user by email.
        
        Args:
            email (str): User's email
            
        Returns:
            MockUser: A mock user object
        """
        logger.info(f"Mock Auth: Getting user with email {email}")
        
        # Check if user already exists
        for uid, user_data in _mock_database['users'].items():
            if user_data.get('email') == email:
                return MockUser(
                    email=email, 
                    uid=uid,
                    display_name=user_data.get('display_name')
                )
        
        # If not found, create a new user
        return MockUser(email=email)

class MockUser:
    """Mock user object."""
    
    def __init__(self, email, uid=None, display_name=None, phone_number=None):
        self.email = email
        self.uid = uid or f"mock-uid-{hash(email) % 10000}"
        self.display_name = display_name
        self.phone_number = phone_number

# Firestore mock implementation
class MockFirestore:
    """Mock implementation of Firestore."""
    
    def client(self):
        """Return a mock client."""
        return MockFirestoreClient()

class MockFirestoreClient:
    """Mock Firestore client."""
    
    def collection(self, name):
        """Return a mock collection."""
        return MockCollection(name)

class MockCollection:
    """Mock Firestore collection."""
    
    def __init__(self, name):
        self.name = name
        
        # Create the collection in the mock database if it doesn't exist
        if self.name not in _mock_database:
            _mock_database[self.name] = {}
    
    def document(self, doc_id):
        """Get a document reference."""
        if doc_id not in _mock_database.get(self.name, {}):
            _mock_database[self.name][doc_id] = {}
        return MockDocument(self.name, doc_id)

class MockDocument:
    """Mock document reference."""
    
    def __init__(self, collection_name, doc_id):
        self.collection = collection_name
        self.id = doc_id
    
    def set(self, data):
        """Set document data."""
        _mock_database[self.collection][self.id] = data
        logger.debug(f"Mock Firestore: Document {self.collection}/{self.id} set")
        return True
    
    def update(self, data):
        """Update document data."""
        if self.id in _mock_database.get(self.collection, {}):
            _mock_database[self.collection][self.id].update(data)
            logger.debug(f"Mock Firestore: Document {self.collection}/{self.id} updated")
        else:
            _mock_database[self.collection][self.id] = data
            logger.debug(f"Mock Firestore: Document {self.collection}/{self.id} created with update")
        return True
    
    def get(self):
        """Get document snapshot."""
        exists = self.id in _mock_database.get(self.collection, {})
        data = _mock_database.get(self.collection, {}).get(self.id, {})
        return MockDocumentSnapshot(self.id, data, exists)

class MockDocumentSnapshot:
    """Mock document snapshot."""
    
    def __init__(self, doc_id, data, exists=True):
        self.id = doc_id
        self._data = data
        self.exists = exists
    
    def to_dict(self):
        """Convert to dictionary."""
        return self._data

# Firebase Realtime Database mock implementation
class MockDatabaseReference:
    """Mock of Firebase Realtime Database reference."""
    
    def __init__(self, path):
        self.path = path
        self._ensure_path_exists(path)
    
    def _ensure_path_exists(self, path):
        """Ensure the path exists in the mock database."""
        parts = path.strip('/').split('/')
        current = _mock_database
        
        for i, part in enumerate(parts):
            if part not in current:
                if i == len(parts) - 1:
                    current[part] = {}
                else:
                    current[part] = {}
            current = current[part]
    
    def _get_value_at_path(self, path=None):
        """Get the value at the specified path."""
        if path is None:
            path = self.path
            
        parts = path.strip('/').split('/')
        current = _mock_database
        
        for part in parts:
            if part not in current:
                return {}
            current = current[part]
            
        return current
    
    def _set_value_at_path(self, value, path=None):
        """Set the value at the specified path."""
        if path is None:
            path = self.path
            
        parts = path.strip('/').split('/')
        current = _mock_database
        
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = value
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]
    
    def child(self, path):
        """Get a reference to a child path."""
        new_path = f"{self.path}/{path}"
        return MockDatabaseReference(new_path)
    
    def push(self):
        """Create a new child with a unique key."""
        key = f"mock-key-{int(time.time())}-{id(self)}"
        return MockDatabaseReference(f"{self.path}/{key}")
    
    def set(self, value):
        """Set the value at this reference."""
        self._set_value_at_path(value)
        logger.debug(f"Mock DB: Set value at {self.path}")
        return True
    
    def update(self, value):
        """Update values at this reference."""
        current = self._get_value_at_path()
        if isinstance(current, dict) and isinstance(value, dict):
            current.update(value)
            self._set_value_at_path(current)
            logger.debug(f"Mock DB: Updated values at {self.path}")
        else:
            self._set_value_at_path(value)
            logger.debug(f"Mock DB: Set value at {self.path} (via update)")
        return True
    
    def get(self):
        """Get the value at this reference."""
        return self._get_value_at_path()
    
    def remove(self):
        """Remove this reference."""
        parts = self.path.strip('/').split('/')
        if len(parts) > 1:
            parent_path = '/'.join(parts[:-1])
            last_part = parts[-1]
            parent_value = self._get_value_at_path(parent_path)
            if isinstance(parent_value, dict) and last_part in parent_value:
                del parent_value[last_part]
                logger.debug(f"Mock DB: Removed value at {self.path}")
        return True
    
    def order_by_child(self, child):
        """Order results by child key (mock implementation)."""
        # Just return self for the mock, we'll sort later
        self._order_by = child
        return self
    
    def limit_to_last(self, limit):
        """Limit to last N results (mock implementation)."""
        # Store the limit for use in get()
        self._limit = limit
        return self

def reference(path):
    """Get a database reference for the specified path."""
    return MockDatabaseReference(path)

# Create module-level instances
auth = MockAuth()
firestore = MockFirestore() 
db = type('MockDatabase', (), {'reference': reference})

# For backward compatibility
def get_db_reference(path):
    """Get a database reference for backwards compatibility."""
    return reference(path) 