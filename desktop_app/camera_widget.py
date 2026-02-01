"""
Camera Widget for capturing video frames from webcam.
Provides real-time preview with face detection overlay.
"""

import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt6.QtGui import QImage, QPixmap
from typing import Optional, Callable


class CameraThread(QThread):
    """Thread for capturing camera frames."""
    
    frame_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, camera_id: int = 0, fps: int = 30):
        super().__init__()
        self.camera_id = camera_id
        self.fps = fps
        self.running = False
        self.cap = None
    
    def run(self):
        """Capture frames from camera."""
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            self.error_occurred.emit("Failed to open camera")
            return
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        self.running = True
        
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame_ready.emit(frame)
            else:
                self.error_occurred.emit("Failed to read frame")
                break
            
            # Control frame rate
            self.msleep(int(1000 / self.fps))
        
        self.cap.release()
    
    def stop(self):
        """Stop the camera thread."""
        self.running = False
        self.wait()


class CameraWidget(QWidget):
    """Widget for displaying camera feed with face detection overlay."""
    
    # Signals
    frame_captured = pyqtSignal(np.ndarray)
    face_detected = pyqtSignal(bool, object)  # (detected, bounding_box)
    
    def __init__(
        self, 
        parent=None, 
        camera_id: int = 0,
        show_face_box: bool = True,
        mirror: bool = True
    ):
        super().__init__(parent)
        
        self.camera_id = camera_id
        self.show_face_box = show_face_box
        self.mirror = mirror
        self.current_frame = None
        self.face_box = None
        self.face_cascade = None
        self.frame_processor: Optional[Callable] = None
        
        # Initialize UI
        self._init_ui()
        
        # Initialize camera thread
        self.camera_thread = None
        
        # Load face cascade for local detection
        self._load_face_cascade()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video display label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a2e;
                border: 2px solid #16213e;
                border-radius: 10px;
            }
        """)
        
        layout.addWidget(self.video_label)
    
    def _load_face_cascade(self):
        """Load Haar cascade for face detection."""
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        except Exception as e:
            print(f"Failed to load face cascade: {e}")
    
    def start_camera(self):
        """Start the camera capture."""
        if self.camera_thread is not None and self.camera_thread.isRunning():
            return
        
        self.camera_thread = CameraThread(self.camera_id)
        self.camera_thread.frame_ready.connect(self._on_frame_ready)
        self.camera_thread.error_occurred.connect(self._on_error)
        self.camera_thread.start()
    
    def stop_camera(self):
        """Stop the camera capture."""
        if self.camera_thread is not None:
            self.camera_thread.stop()
            self.camera_thread = None
    
    def _on_frame_ready(self, frame: np.ndarray):
        """Handle new frame from camera thread."""
        # Mirror the frame if enabled
        if self.mirror:
            frame = cv2.flip(frame, 1)
        
        self.current_frame = frame.copy()
        
        # Detect face (local detection for UI)
        display_frame = frame.copy()
        self.face_box = self._detect_face_local(frame)
        
        # Draw face box
        if self.show_face_box and self.face_box is not None:
            x, y, w, h = self.face_box
            cv2.rectangle(
                display_frame, 
                (x, y), 
                (x + w, y + h), 
                (0, 255, 0), 
                2
            )
            
            # Draw corner accents
            corner_length = 20
            color = (0, 255, 0)
            thickness = 3
            
            # Top-left
            cv2.line(display_frame, (x, y), (x + corner_length, y), color, thickness)
            cv2.line(display_frame, (x, y), (x, y + corner_length), color, thickness)
            
            # Top-right
            cv2.line(display_frame, (x + w, y), (x + w - corner_length, y), color, thickness)
            cv2.line(display_frame, (x + w, y), (x + w, y + corner_length), color, thickness)
            
            # Bottom-left
            cv2.line(display_frame, (x, y + h), (x + corner_length, y + h), color, thickness)
            cv2.line(display_frame, (x, y + h), (x, y + h - corner_length), color, thickness)
            
            # Bottom-right
            cv2.line(display_frame, (x + w, y + h), (x + w - corner_length, y + h), color, thickness)
            cv2.line(display_frame, (x + w, y + h), (x + w, y + h - corner_length), color, thickness)
        
        # Emit face detected signal
        self.face_detected.emit(self.face_box is not None, self.face_box)
        
        # Custom frame processing
        if self.frame_processor:
            display_frame = self.frame_processor(display_frame, self.face_box)
        
        # Display the frame
        self._display_frame(display_frame)
        
        # Emit frame captured signal
        self.frame_captured.emit(self.current_frame)
    
    def _detect_face_local(self, frame: np.ndarray) -> Optional[tuple]:
        """Detect face using local Haar cascade."""
        if self.face_cascade is None:
            return None
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100)
        )
        
        if len(faces) > 0:
            # Return the largest face
            faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
            return tuple(faces[0])
        
        return None
    
    def _display_frame(self, frame: np.ndarray):
        """Display a frame on the video label."""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create QImage
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(
            rgb_frame.data, 
            w, h, 
            bytes_per_line, 
            QImage.Format.Format_RGB888
        )
        
        # Scale to fit label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
    
    def _on_error(self, error_msg: str):
        """Handle camera errors."""
        print(f"Camera error: {error_msg}")
        self.video_label.setText(f"Camera Error: {error_msg}")
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current frame."""
        return self.current_frame.copy() if self.current_frame is not None else None
    
    def get_face_box(self) -> Optional[tuple]:
        """Get the current face bounding box."""
        return self.face_box
    
    def set_frame_processor(self, processor: Callable):
        """Set a custom frame processor function."""
        self.frame_processor = processor
    
    def closeEvent(self, event):
        """Handle widget close event."""
        self.stop_camera()
        super().closeEvent(event)
