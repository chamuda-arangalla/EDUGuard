"""
Mock Firebase implementation for testing without real Firebase credentials.
This allows the app to run for testing the frontend-backend connection.
"""

class MockAuth:
    """Mock implementation of Firebase Auth."""
    
    def create_user(self, email, password):
        """Mock user creation."""
        print(f"Mock: Creating user with email {email}")
        return MockUser(email=email)
    
    def get_user_by_email(self, email):
        """Mock get user by email."""
        print(f"Mock: Getting user with email {email}")
        return MockUser(email=email)

class MockUser:
    """Mock user object."""
    
    def __init__(self, email):
        self.email = email
        self.uid = f"mock-uid-{hash(email) % 10000}"

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
        self._documents = {}
    
    def document(self, doc_id):
        """Get a document reference."""
        if doc_id not in self._documents:
            self._documents[doc_id] = {}
        return MockDocument(doc_id, self._documents[doc_id])

class MockDocument:
    """Mock document reference."""
    
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
    
    def set(self, data):
        """Set document data."""
        self._data.update(data)
        print(f"Mock: Document {self.id} set with data: {data}")
        return True
    
    def get(self):
        """Get document snapshot."""
        return MockDocumentSnapshot(self.id, self._data)

class MockDocumentSnapshot:
    """Mock document snapshot."""
    
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
    
    def to_dict(self):
        """Convert to dictionary."""
        return self._data

# Create mock instances
auth = MockAuth()
firestore = MockFirestore() 