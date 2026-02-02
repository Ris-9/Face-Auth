"""
Registration Screen for Face Authentication Desktop App.
Allows users to register with username and facial capture.
Features modern UI with glassmorphism and gradient effects.
"""

import base64
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor
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
        layout.setSpacing(25)
        layout.setContentsMargins(50, 30, 50, 30)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Back button (top left)
        back_btn = self._create_back_button()
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Title with icon
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.setSpacing(15)
        
        title_icon = QLabel("📝")
        title_icon.setFont(QFont("Segoe UI Emoji", 36))
        title_layout.addWidget(title_icon)
        
        title = QLabel("User Registration")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #00d4ff;")
        title_layout.addWidget(title)
        
        layout.addWidget(title_container)
        
        # Subtitle
        subtitle = QLabel("Create your secure identity with facial recognition")
        subtitle.setFont(QFont("Segoe UI", 13))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        layout.addWidget(subtitle)
        
        layout.addSpacing(15)
        
        # Main content container
        content_layout = QHBoxLayout()
        content_layout.setSpacing(35)
        
        # Left side - Camera
        camera_container = self._create_camera_section()
        content_layout.addWidget(camera_container, stretch=3)
        
        # Right side - Form
        form_container = self._create_form_section()
        content_layout.addWidget(form_container, stretch=2)
        
        layout.addLayout(content_layout)
    
    def _create_back_button(self) -> QPushButton:
        """Create styled back button."""
        back_btn = QPushButton("← Back to Home")
        back_btn.setFont(QFont("Segoe UI", 11))
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setFixedWidth(150)
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        back_btn.clicked.connect(self._on_back_clicked)
        return back_btn
    
    def _create_camera_section(self) -> QFrame:
        """Create camera section with styling."""
        camera_container = QFrame()
        camera_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(22, 33, 62, 0.9), stop:1 rgba(15, 52, 96, 0.9));
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 20px;
            }
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        camera_container.setGraphicsEffect(shadow)
        
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(20, 20, 20, 20)
        camera_layout.setSpacing(15)
        
        # Camera widget
        self.camera_widget = CameraWidget(show_face_box=True, mirror=True)
        self.camera_widget.face_detected.connect(self._on_face_detected)
        self.camera_widget.setMinimumHeight(400)
        camera_layout.addWidget(self.camera_widget)
        
        # Face status indicator
        self.face_status_frame = QFrame()
        self.face_status_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 165, 0, 0.1);
                border: 1px solid rgba(255, 165, 0, 0.3);
                border-radius: 10px;
                padding: 5px;
            }
        """)
        status_layout = QHBoxLayout(self.face_status_frame)
        status_layout.setContentsMargins(15, 10, 15, 10)
        
        self.face_status_icon = QLabel("⚠️")
        self.face_status_icon.setFont(QFont("Segoe UI Emoji", 16))
        status_layout.addWidget(self.face_status_icon)
        
        self.face_status_label = QLabel("Position your face in the frame")
        self.face_status_label.setFont(QFont("Segoe UI", 12))
        self.face_status_label.setStyleSheet("color: #ffa500; background: transparent;")
        status_layout.addWidget(self.face_status_label)
        status_layout.addStretch()
        
        camera_layout.addWidget(self.face_status_frame)
        
        return camera_container
    
    def _create_form_section(self) -> QFrame:
        """Create form section with styling."""
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(22, 33, 62, 0.9), stop:1 rgba(15, 52, 96, 0.9));
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 20px;
            }
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        form_container.setGraphicsEffect(shadow)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)
        form_layout.setContentsMargins(30, 30, 30, 30)
        
        # Username section
        username_label = QLabel("👤 Username")
        username_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        username_label.setStyleSheet("color: #fff; background: transparent;")
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter unique username")
        self.username_input.setFont(QFont("Segoe UI", 13))
        self.username_input.setMinimumHeight(50)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(15, 52, 96, 0.8);
                border: 2px solid rgba(0, 212, 255, 0.2);
                border-radius: 12px;
                padding: 12px 18px;
                color: #fff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #00d4ff;
                background-color: rgba(15, 52, 96, 1);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        form_layout.addWidget(self.username_input)
        
        form_layout.addSpacing(10)
        
        # Instructions card
        instructions_frame = QFrame()
        instructions_frame.setStyleSheet("""
            QFrame {
                background: rgba(0, 212, 255, 0.05);
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-radius: 12px;
                padding: 10px;
            }
        """)
        instructions_layout = QVBoxLayout(instructions_frame)
        instructions_layout.setSpacing(8)
        
        instructions_title = QLabel("📋 Instructions")
        instructions_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        instructions_title.setStyleSheet("color: #00d4ff; background: transparent;")
        instructions_layout.addWidget(instructions_title)
        
        steps = [
            "Enter a unique username (min 3 chars)",
            "Position your face in the camera frame",
            "Ensure good lighting on your face",
            "Click 'Register Face' when ready"
        ]
        
        for i, step in enumerate(steps, 1):
            step_label = QLabel(f"{i}. {step}")
            step_label.setFont(QFont("Segoe UI", 10))
            step_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); background: transparent;")
            instructions_layout.addWidget(step_label)
        
        form_layout.addWidget(instructions_frame)
        
        form_layout.addStretch()
        
        # Register button
        self.register_btn = QPushButton("📸 Register Face")
        self.register_btn.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_btn.setMinimumHeight(55)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #0099cc);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #33ddff, stop:1 #00aadd);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00b3cc, stop:1 #0088bb);
            }
            QPushButton:disabled {
                background: rgba(68, 68, 68, 0.5);
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.register_btn.clicked.connect(self._on_register_clicked)
        form_layout.addWidget(self.register_btn)
        
        # Status message
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("background: transparent; border: none;")
        self.status_frame.setMinimumHeight(50)
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #888; background: transparent;")
        status_layout.addWidget(self.status_label)
        
        form_layout.addWidget(self.status_frame)
        
        return form_container
    
    def _on_face_detected(self, detected: bool, box):
        """Handle face detection status."""
        self.face_detected = detected
        
        if detected:
            self.face_status_icon.setText("✅")
            self.face_status_label.setText("Face detected - Ready to capture")
            self.face_status_label.setStyleSheet("color: #00ff88; background: transparent;")
            self.face_status_frame.setStyleSheet("""
                QFrame {
                    background: rgba(0, 255, 136, 0.1);
                    border: 1px solid rgba(0, 255, 136, 0.3);
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
        else:
            self.face_status_icon.setText("⚠️")
            self.face_status_label.setText("Position your face in the frame")
            self.face_status_label.setStyleSheet("color: #ffa500; background: transparent;")
            self.face_status_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 165, 0, 0.1);
                    border: 1px solid rgba(255, 165, 0, 0.3);
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
    
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
        self.register_btn.setText("⏳ Registering...")
        self._show_status("Processing facial data...", error=False)
        
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
            self.register_btn.setText("📸 Register Face")
    
    def _show_status(self, message: str, error: bool = False):
        """Show status message."""
        self.status_label.setText(message)
        if error:
            self.status_label.setStyleSheet("color: #ff4444; background: transparent;")
        else:
            self.status_label.setStyleSheet("color: #00ff88; background: transparent;")
    
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
