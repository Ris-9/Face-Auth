# Face Authentication System

A desktop application for face-based secure authentication using FaceNet embeddings and liveness detection.

## Features

- **Face Registration**: Register users with their facial embeddings
- **Face Authentication**: Authenticate users via facial recognition with 1:N identification
- **Liveness Detection**: Anti-spoofing protection using texture analysis, movement detection
- **Multi-User Support**: SQLite database stores embeddings by username/ID
- **Cosine Similarity Matching**: 512-dimensional FaceNet embeddings with configurable threshold

## Technology Stack

- **Backend**: Python, Flask, SQLite
- **Face Recognition**: FaceNet (InceptionResnetV1) via facenet-pytorch
- **Face Detection**: MTCNN
- **Desktop App**: PyQt6
- **Camera**: OpenCV

## Quick Start

### 1. Activate Conda Environment

```bash
conda activate face_auth
```

### 2. Start Backend Server

```bash
python run_backend.py
```

Or double-click `start_backend.bat`

The server will start at `http://localhost:5000`

### 3. Start Desktop App

In a new terminal:

```bash
conda activate face_auth
python run_app.py
```

Or double-click `start_app.bat`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/register` | POST | Register new user |
| `/api/authenticate` | POST | Authenticate user |
| `/api/users` | GET | List all users |
| `/api/users/<id>` | DELETE | Delete user by ID |
| `/api/detect` | POST | Detect face in image |

## Project Structure

```
face_auth_project/
├── backend/
│   ├── __init__.py
│   ├── app.py                    # Flask REST API
│   ├── database.py               # SQLite database handler
│   ├── face_recognition_module.py # FaceNet embeddings
│   └── liveness_detection.py     # Anti-spoofing
├── desktop_app/
│   ├── __init__.py
│   ├── main.py                   # Main application window
│   ├── camera_widget.py          # Camera capture widget
│   ├── registration_screen.py    # User registration
│   └── authentication_screen.py  # Face authentication
├── requirements.txt
├── environment.yml
├── run_backend.py
├── run_app.py
├── start_backend.bat
├── start_app.bat
└── README.md
```

## Configuration

### Similarity Threshold

Default: `0.7` (70% match required)

Edit in `backend/face_recognition_module.py`:
```python
FaceRecognition(similarity_threshold=0.7)
```

### Liveness Detection Thresholds

Edit in `backend/liveness_detection.py`:
```python
LivenessDetector(
    texture_threshold=100.0,  # Minimum texture detail
    movement_threshold=5.0    # Minimum head movement
)
```

## Usage

### Registering a User

1. Open the desktop app
2. Click "Register"
3. Enter a unique username
4. Position your face in the camera frame
5. Click "Register Face"

### Authenticating

1. Open the desktop app
2. Click "Authenticate"
3. Position your face in the camera frame
4. Click "Authenticate"
5. The system will identify you from registered users

## License

MIT License
