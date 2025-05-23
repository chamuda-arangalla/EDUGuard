# Enhanced Posture Monitoring Setup Guide

## Overview

This guide will help you set up the enhanced posture monitoring system that integrates real-time posture detection with Firebase database and smart alerting.

## Prerequisites

### 1. Python Dependencies

Make sure you have all required Python packages installed:

```bash
cd backend
pip install -r requirements.txt

# Additional packages for enhanced posture monitoring
pip install opencv-python
pip install mediapipe
pip install numpy
pip install joblib
pip install scikit-learn
```

### 2. Firebase Setup

1. **Firebase Configuration**: Ensure `firebase_config.py` is properly configured
2. **Service Account Key**: Place your `serviceAccountKey.json` in the `backend/` directory
3. **Firebase Realtime Database**: Make sure your Firebase project has Realtime Database enabled

### 3. Required Model Files

Ensure the posture classification model is available:
- `backend/modelScrpits/models/posture_classifier.pkl`

If this file is missing, the system will still run but posture detection may not work correctly.

## Frontend Integration

### 1. Enhanced ScriptRunner Component

The `ScriptRunner.tsx` component has been enhanced with:
- Real-time posture monitoring controls
- Live posture data dashboard
- Alert notifications
- Automatic status checking

### 2. New API Service

The `api.ts` service now includes `postureService` with endpoints for:
- Starting/stopping monitoring
- Getting real-time posture data
- Retrieving alerts
- Checking monitoring status

## Backend Integration

### 1. New API Endpoints

The system adds these new endpoints under `/api/posture/`:

- `POST /api/posture/start` - Start posture monitoring
- `POST /api/posture/stop` - Stop posture monitoring
- `GET /api/posture/status` - Get monitoring status
- `GET /api/posture/data/recent` - Get recent posture data
- `GET /api/posture/alerts/recent` - Get recent alerts
- `POST /api/posture/check-alerts` - Trigger alert check

### 2. Enhanced Database Integration

- Real-time data saving to Firebase
- 5-minute rolling window analysis
- Automatic alert generation when bad posture > 60%
- Background monitoring threads

## Usage

### 1. Starting the Backend

```bash
cd backend
python app.py
```

The backend will automatically:
- Initialize Firebase connection
- Set up the enhanced posture monitoring endpoints
- Start the Flask server on port 5000

### 2. Starting the Frontend

```bash
cd frontend
npm start
```

### 3. Using the Enhanced Posture Monitoring

1. **Login** to the application with your credentials
2. **Navigate** to the Dashboard
3. **Click** on "Enhanced Posture Checking" in the Health Monitoring Tools section
4. **Allow** camera access when prompted
5. **Monitor** your posture in real-time through the dashboard

### 4. Features Available

#### Real-time Monitoring
- Continuous posture detection using MediaPipe
- Data saved every 3 seconds to Firebase
- Background alert checking every 30 seconds

#### Smart Alerts
- Automatic notifications when bad posture > 60% over 5 minutes
- Alert cooldown periods to prevent spam
- Real-time alert display in the UI

#### Dashboard Features
- Live posture percentage display
- Recent alerts history
- Expandable detailed view
- Status indicators

## Troubleshooting

### Common Issues

#### 1. Camera Not Working
- **Check**: Camera permissions in browser
- **Verify**: No other applications are using the camera
- **Ensure**: Webcam server is running properly

#### 2. Backend Connection Errors
- **Verify**: Backend server is running on port 5000
- **Check**: CORS settings allow frontend domain
- **Confirm**: All required dependencies are installed

#### 3. Firebase Errors
- **Validate**: `serviceAccountKey.json` is present and valid
- **Check**: Firebase Realtime Database is enabled
- **Verify**: Database rules allow read/write access

#### 4. Model Not Found
- **Location**: Ensure `posture_classifier.pkl` is in `backend/modelScrpits/models/`
- **Alternative**: System will log warnings but continue running
- **Training**: You may need to train a new model if none exists

### Debug Mode

Enable debug logging in the backend:

```python
# In app.py, change logging level
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

Check these log files for debugging:
- Backend console output
- `backend/modelScrpits/posture_service.log` (when using background service)
- Browser console for frontend errors

## Architecture

### Data Flow

```
User Camera → Webcam Server → Enhanced Posture Detection → Firebase Realtime DB
                                        ↓
Frontend API Service ← Flask API ← Background Monitoring Thread
                                        ↓
                              Alert System (if bad posture > 60%)
```

### Database Structure

```json
{
  "predictions": {
    "user_id": {
      "posture": {
        "prediction_key": {
          "model": "posture",
          "prediction": {
            "posture": "Good Posture",
            "timestamp": 1640995200000
          },
          "timestamp": 1640995200000,
          "created_at": "2021-12-31T23:59:59"
        }
      }
    }
  },
  "alerts": {
    "user_id": {
      "alert_key": {
        "type": "posture",
        "message": "Poor posture detected!",
        "level": "warning",
        "timestamp": 1640995200000,
        "read": false
      }
    }
  }
}
```

## Security Considerations

1. **User Authentication**: Ensure proper user authentication is in place
2. **Camera Permissions**: Request explicit camera permissions
3. **Data Privacy**: Consider implementing data retention policies
4. **Firebase Rules**: Configure appropriate Firebase security rules

## Performance Optimization

1. **Reduce Polling Frequency**: Adjust polling intervals for better performance
2. **Limit Data Retention**: Implement automatic data cleanup
3. **Optimize Model**: Use lighter models for faster inference
4. **Batch Operations**: Group database operations when possible

## Support

For issues or questions:
1. Check the log files for error details
2. Verify all dependencies are correctly installed
3. Ensure Firebase configuration is correct
4. Test individual components separately

## Future Enhancements

Planned features:
- Multiple user monitoring
- Advanced analytics dashboard
- Mobile app integration
- Customizable alert thresholds
- Export functionality for reports 