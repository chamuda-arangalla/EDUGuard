# EDUGuard Posture Monitoring System

## Overview
The posture monitoring system uses computer vision and machine learning to analyze user posture in real-time and provide alerts for poor posture habits.

## Components

### 1. Webcam Server (`webcam_server.py`)
- Captures video frames from the user's webcam
- Streams frames to the posture detection client via socket connection
- Runs on port 9999

### 2. Posture Detection (`simple_posture_detection.py`)
- Connects to the webcam server to receive video frames
- Uses MediaPipe for pose landmark detection
- Applies machine learning model to classify posture as "Good" or "Bad"
- Saves results to Firebase database every 3 seconds
- Generates automatic alerts for poor posture

### 3. Machine Learning Model (`models/posture_classifier.pkl`)
- Trained model that classifies posture based on angle calculations
- Uses shoulder and nose positions to determine posture quality
- Binary classification: Good Posture (1) vs Bad Posture (0)

## How It Works

1. **Start Monitoring**: Frontend calls `/api/posture/start`
2. **Webcam Server**: Starts capturing and streaming video frames
3. **Posture Detection**: Analyzes frames and saves predictions to Firebase
4. **Alert System**: Monitors posture trends and generates warnings
5. **Data Visualization**: Frontend displays real-time posture statistics

## Key Features

- ✅ Real-time posture analysis
- ✅ Firebase database integration
- ✅ Automatic poor posture alerts
- ✅ Visual feedback with camera window
- ✅ RESTful API endpoints
- ✅ Proper error handling and logging

## API Endpoints

- `POST /api/posture/start` - Start posture monitoring
- `POST /api/posture/stop` - Stop posture monitoring
- `GET /api/posture/status` - Get monitoring status
- `GET /api/posture/data/recent` - Get recent posture data
- `GET /api/posture/alerts/recent` - Get recent posture alerts

## Dependencies

- OpenCV (cv2) - Computer vision
- MediaPipe - Pose detection
- scikit-learn (joblib) - Model loading
- Firebase Admin SDK - Database operations
- NumPy - Mathematical operations

## Usage

The system is automatically managed by the Flask API. Users interact through the frontend interface to start/stop monitoring and view results. 