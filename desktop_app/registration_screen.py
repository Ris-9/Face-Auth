"""
Registration Screen for Face Authentication Desktop App.
Allows users to register with username and facial capture.
"""

import base64
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import cv2
import numpy as np

from .camera_widget import CameraWidget


class RegistrationScreen(QWidget):
    """Registration screen with camera capture and username input."""
    
    # Signals
    registration_success = pyqtSignal(str, int)  # username, user_id
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None, api_url: str = "http://localhost:5000"):
        super().__init__(parent)
        self.api_url = api_url
        self.face_detected = False
        self.capture_countdown = 0
        self.countdown_timer = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 20, 40, 20)
        
        # Header
        header = QLabel("User Registration")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #00d4ff;")
        layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Register your face for secure authentication")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Main content container
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        # Left side - Camera
        camera_container = QFrame()
        camera_container.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 15px;
                padding: 10px;
            }
        """)
        camera_layout = QVBoxLayout(camera_container)
        
        self.camera_widget = CameraWidget(show_face_box=True, mirror=True)
        self.camera_widget.face_detected.connect(self._on_face_detected)
        camera_layout.addWidget(self.camera_widget)
        
        # Face status indicator
        self.face_status_label = QLabel("Position your face in the frame")
        self.face_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.face_status_label.setFont(QFont("Segoe UI", 11))
        self.face_status_label.setStyleSheet("color: #ffa500; padding: 10px;")
        camera_layout.addWidget(self.face_status_label)
        
        content_layout.addWidget(camera_container, stretch=2)
        
        # Right side - Form
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15)
        
        # Username input
        username_label = QLabel("Username")
        username_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        username_label.setStyleSheet("color: #fff;")
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter unique username")
        self.username_input.setFont(QFont("Segoe UI", 12))
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f3460;
                border: 2px solid #1a1a2e;
                border-radius: 8px;
                padding: 12px;
                color: #fff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #00d4ff;
            }
        """)
        form_layout.addWidget(self.username_input)
        
        form_layout.addSpacing(20)
        
        # Instructions
        instructions = QLabel(
            "Instructions:\n"
            "1. Enter a unique username\n"
            "2. Position your face in the camera frame\n"
            "3. Ensure good lighting\n"
            "4. Click 'Register' when ready"
        )
        instructions.setFont(QFont("Segoe UI", 10))
        instructions.setStyleSheet("color: #aaa; line-height: 1.5;")
        instructions.setWordWrap(True)
        form_layout.addWidget(instructions)
        
        form_layout.addStretch()
        
        # Register button
        self.register_btn = QPushButton("📸 Register Face")
        self.register_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #0099cc);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00e5ff, stop:1 #00aadd);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00b3cc, stop:1 #0088bb);
            }
            QPushButton:disabled {
                background: #444;
                color: #888;
            }
        """)
        self.register_btn.clicked.connect(self._on_register_clicked)
        form_layout.addWidget(self.register_btn)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #888; padding: 10px;")
        form_layout.addWidget(self.status_label)
        
        content_layout.addWidget(form_container, stretch=1)
        
        layout.addLayout(content_layout)
        
        # Back button
        back_btn = QPushButton("← Back to Home")
        back_btn.setFont(QFont("Segoe UI", 11))
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                color: #fff;
                border-color: #666;
            }
        """)
        back_btn.clicked.connect(self._on_back_clicked)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
    
    def _on_face_detected(self, detected: bool, box):
        """Handle face detection status."""
        self.face_detected = detected
        
        if detected:
            self.face_status_label.setText("✅ Face detected - Ready to capture")
            self.face_status_label.setStyleSheet("color: #00ff88; padding: 10px;")
        else:
            self.face_status_label.setText("⚠️ Position your face in the frame")
            self.face_status_label.setStyleSheet("color: #ffa500; padding: 10px;")
    
    def _on_register_clicked(self):
        """Handle register button click."""
        username = self.username_input.text().strip()
        
        if not username:
            self._show_status("Please enter a username", error=True)
            return
        
        if len(username) < 3:
            self._show_status("Username must be at least 3 characters", error=True)
            return
        
        if not self.face_detected:
            self._show_status("No face detected. Please position your face in the frame.", error=True)
            return
        
        # Get current frame
        frame = self.camera_widget.get_current_frame()
        if frame is None:
            self._show_status("Failed to capture image", error=True)
            return
        
        # Disable button during registration
        self.register_btn.setEnabled(False)
        self._show_status("Registering...", error=False)
        
        # Convert frame to base64
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Send registration request
        try:
            response = requests.post(
                f"{self.api_url}/api/register",
                json={
                    "username": username,
                    "image": image_base64
                },
                timeout=30
            )
            
            data = response.json()
            
            if response.status_code == 201 and data.get('success'):
                self._show_status(f"✅ {data['message']}", error=False)
                self.registration_success.emit(username, data.get('user_id', 0))
                
                # Clear form
                self.username_input.clear()
            else:
                self._show_status(f"❌ {data.get('message', 'Registration failed')}", error=True)
                
        except requests.exceptions.ConnectionError:
            self._show_status("❌ Cannot connect to server. Make sure the backend is running.", error=True)
        except Exception as e:
            self._show_status(f"❌ Error: {str(e)}", error=True)
        finally:
            self.register_btn.setEnabled(True)
    
    def _show_status(self, message: str, error: bool = False):
        """Show status message."""
        self.status_label.setText(message)
        if error:
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
        else:
            self.status_label.setStyleSheet("color: #00ff88; padding: 10px;")
    
    def _on_back_clicked(self):
        """Handle back button click."""
        self.back_requested.emit()
    
    def start_camera(self):
        """Start the camera."""
        self.camera_widget.start_camera()
    
    def stop_camera(self):
        """Stop the camera."""
        self.camera_widget.stop_camera()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.start_camera()
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        self.stop_camera()
