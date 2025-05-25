# EDUGuard Backend

This directory contains the backend code for the EDUGuard application, which provides health monitoring tools for students including posture, stress, eye strain, and hydration monitoring.

## Code Structure

The backend follows a modular structure:

```
backend/
├── main.py                # Main entry point for the application
├── app.py                 # Core application routes
├── posture_api.py         # Posture monitoring API endpoints
├── stress_api.py          # Stress monitoring API endpoints
├── cvs_api.py             # Computer Vision Syndrome (eye strain) API endpoints
├── hydration_api.py       # Hydration monitoring API endpoints
├── firebase_config.py     # Firebase configuration
├── modelScrpits/          # Detection scripts and models
│   ├── posture_detection.py
│   ├── stress_detection.py
│   ├── cvs_detection.py
│   ├── hydration_detection.py
│   ├── webcam_server.py
│   └── models/            # ML models and cascade files
├── utils/                 # Utility modules
│   ├── database.py        # Database operations
│   ├── alert_manager.py   # Alert management
│   └── script_manager.py  # Centralized script management
└── requirements.txt       # Python dependencies
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Firebase account with Realtime Database
- Webcam

### Installation

1. Clone the repository
2. Navigate to the backend directory
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up Firebase:
   - Create a Firebase project
   - Set up Realtime Database
   - Download serviceAccountKey.json and place it in the backend directory

### Running the Application

The application can be started using the main entry point:

```bash
python main.py
```

Command line options:
- `--debug`: Enable debug mode
- `--port PORT`: Specify the port (default: 5000)
- `--host HOST`: Specify the host (default: 0.0.0.0)

Example:
```bash
python main.py --debug --port 5001
```

## API Endpoints

### Authentication

- `POST /api/register`: Register a new user
- `POST /api/login`: Login a user
- `GET /api/user/profile`: Get user profile
- `PUT /api/user/profile`: Update user profile

### Posture Monitoring

- `POST /api/posture/start`: Start posture monitoring
- `POST /api/posture/stop`: Stop posture monitoring
- `GET /api/posture/status`: Get posture monitoring status
- `GET /api/posture/data/recent`: Get recent posture data
- `GET /api/posture/alerts/recent`: Get recent posture alerts

### Stress Monitoring

- `POST /api/stress/start`: Start stress monitoring
- `POST /api/stress/stop`: Stop stress monitoring
- `GET /api/stress/status`: Get stress monitoring status
- `GET /api/stress/data/recent`: Get recent stress data
- `GET /api/stress/alerts/recent`: Get recent stress alerts

### Eye Strain Monitoring (CVS)

- `POST /api/cvs/start`: Start eye strain monitoring
- `POST /api/cvs/stop`: Stop eye strain monitoring
- `GET /api/cvs/status`: Get eye strain monitoring status
- `GET /api/cvs/data/recent`: Get recent eye strain data
- `GET /api/cvs/alerts/recent`: Get recent eye strain alerts

### Hydration Monitoring

- `POST /api/hydration/start`: Start hydration monitoring
- `POST /api/hydration/stop`: Stop hydration monitoring
- `GET /api/hydration/status`: Get hydration monitoring status
- `GET /api/hydration/data/recent`: Get recent hydration data
- `GET /api/hydration/alerts/recent`: Get recent hydration alerts

## Architecture

The backend uses a modular architecture with the following components:

1. **Flask API**: Handles HTTP requests and responses
2. **Firebase**: Stores user data, monitoring results, and alerts
3. **Script Manager**: Centralizes management of monitoring scripts
4. **Detection Scripts**: Analyze webcam feed for health monitoring
5. **Webcam Server**: Provides video feed to detection scripts

The `main.py` file serves as the entry point, initializing all components and starting the Flask server. The `script_manager.py` provides a unified interface for managing all monitoring scripts, ensuring proper resource allocation and cleanup.

## Development

### Adding a New Monitoring Feature

To add a new monitoring feature:

1. Create a detection script in the `modelScrpits` directory
2. Create an API file with endpoints for the feature
3. Add the feature to the `script_manager.py` file
4. Register the feature's blueprint in `main.py`

### Testing

To run the backend in development mode:

```bash
python main.py --debug
```

This will enable debug mode and auto-reload when files are changed. 