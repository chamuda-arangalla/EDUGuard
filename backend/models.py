import cv2
import logging
import os
import time
from datetime import datetime

logger = logging.getLogger('EDUGuard.ModelManager')

class ModelManager:
    """Manages detection and prediction models for EDUGuard"""
    
    def __init__(self, emotion_model_path=None):
        """Initialize model manager with paths to model files
        
        Args:
            emotion_model_path (str, optional): Path to emotion detection model
        """
        self.models = {}
        self.face_cascade = None
        self.emotion_model = None
        
        # Initialize models
        self.load_models(emotion_model_path)
        
    def load_models(self, emotion_model_path=None):
        """Load all required models
        
        Args:
            emotion_model_path (str, optional): Path to emotion detection model
        """
        try:
            # Load face detection cascade
            face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
            
            # Check if cascade loaded successfully
            if self.face_cascade.empty():
                logger.warning("Failed to load face cascade classifier")
            else:
                logger.info("Face detection model loaded successfully")
            
            # Load emotion detection model if path provided
            if emotion_model_path and os.path.exists(emotion_model_path):
                # Here you would load your specific model
                # Example: self.emotion_model = tf.keras.models.load_model(emotion_model_path)
                logger.info(f"Loaded emotion model from {emotion_model_path}")
            else:
                logger.warning("No emotion model loaded - using mock predictions")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def process_frame(self, frame):
        """Process a video frame through all models
        
        Args:
            frame: Video frame to process
            
        Returns:
            dict: Dictionary with predictions from each model
        """
        if frame is None:
            return {}
            
        try:
            # Create a dictionary to store all predictions
            predictions = {}
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            ) if self.face_cascade else []
            
            # Store face detection results
            predictions['face_count'] = len(faces)
            
            # Process each face for emotion if faces detected
            if len(faces) > 0:
                # Get the largest face
                largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
                x, y, w, h = largest_face
                
                # For demo purposes, generate mock emotion predictions
                # In a real implementation, you would use your loaded models
                predictions['attention'] = self._generate_mock_attention_score()
                predictions['emotion'] = self._generate_mock_emotion_prediction()
                
                # Add timestamp
                predictions['timestamp'] = datetime.now().isoformat()
                
            return predictions
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return {}
    
    def _generate_mock_attention_score(self):
        """Generate a mock attention score for demonstration
        
        Returns:
            float: A value between 0 and 1 representing attention
        """
        import random
        # Generate a value that tends to be higher (biased to show attention)
        return min(1.0, max(0.0, random.betavariate(5, 2)))
    
    def _generate_mock_emotion_prediction(self):
        """Generate mock emotion predictions for demonstration
        
        Returns:
            dict: Emotion probabilities
        """
        import random
        
        # List of emotions
        emotions = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'fearful', 'disgusted']
        
        # Generate random probabilities
        probs = [random.random() for _ in range(len(emotions))]
        
        # Normalize to sum to 1
        total = sum(probs)
        probs = [p / total for p in probs]
        
        # Return as dictionary
        return dict(zip(emotions, probs)) 