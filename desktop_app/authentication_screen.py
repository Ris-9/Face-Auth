"""
Authentication Screen for Face Authentication Desktop App.
Allows users to authenticate using facial recognition.
"""

import base64
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import cv2

from .camera_widget import CameraWidget


class AuthenticationScreen(QWidget):
    """Authentication screen with real-time face recognition."""
    
    # Signals
    authentication_success = pyqtSignal(dict)  # user data
    authentication_failed = pyqtSignal(str)  # error message
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None, api_url: str = "http://localhost:5000"):
        super().__init__(parent)
        self.api_url = api_url
        self.face_detected = False
        self.is_authenticating = False
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 20, 40, 20)
        
        # Header
        header = QLabel("Face Authentication")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #00ff88;")
        layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Look at the camera to authenticate")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        # Camera container
        camera_container = QFrame()
        camera_container.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 15px;
                padding: 15px;
            }
        """)
        camera_layout = QVBoxLayout(camera_container)
        
        self.camera_widget = CameraWidget(show_face_box=True, mirror=True)
        self.camera_widget.face_detected.connect(self._on_face_detected)
        camera_layout.addWidget(self.camera_widget)
        
        # Liveness indicator
        self.liveness_label = QLabel("🔄 Checking liveness...")
        self.liveness_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.liveness_label.setFont(QFont("Segoe UI", 11))
        self.liveness_label.setStyleSheet("color: #888; padding: 10px;")
        camera_layout.addWidget(self.liveness_label)
        
        content_layout.addWidget(camera_container, stretch=2)
        
        # Right side - Status and controls
        control_container = QFrame()
        control_container.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 15px;
                padding: 25px;
            }
        """)
        control_layout = QVBoxLayout(control_container)
        control_layout.setSpacing(20)
        
        # Optional username for 1:1 verification
        username_label = QLabel("Username (optional)")
        username_label.setFont(QFont("Segoe UI", 11))
        username_label.setStyleSheet("color: #aaa;")
        control_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Leave empty for 1:N identification")
        self.username_input.setFont(QFont("Segoe UI", 12))
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f3460;
                border: 2px solid #1a1a2e;
                border-radius: 8px;
                padding: 12px;
                color: #fff;
            }
            QLineEdit:focus {
                border-color: #00ff88;
            }
        """)
        control_layout.addWidget(self.username_input)
        
        control_layout.addSpacing(10)
        
        # Status display
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: #0f3460;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        status_layout = QVBoxLayout(self.status_frame)
        
        self.status_icon = QLabel("🔒")
        self.status_icon.setFont(QFont("Segoe UI", 48))
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_icon)
        
        self.status_label = QLabel("Position your face and click Authenticate")
        self.status_label.setFont(QFont("Segoe UI", 12))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self.status_label)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_info_label.setStyleSheet("color: #00ff88;")
        self.user_info_label.hide()
        status_layout.addWidget(self.user_info_label)
        
        self.similarity_label = QLabel("")
        self.similarity_label.setFont(QFont("Segoe UI", 10))
        self.similarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.similarity_label.setStyleSheet("color: #888;")
        self.similarity_label.hide()
        status_layout.addWidget(self.similarity_label)
        
        control_layout.addWidget(self.status_frame)
        
        control_layout.addStretch()
        
        # Authenticate button
        self.auth_btn = QPushButton("🔓 Authenticate")
        self.auth_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.auth_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auth_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88, stop:1 #00cc6e);
                color: #1a1a2e;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #33ff99, stop:1 #33dd88);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00dd77, stop:1 #00bb5e);
            }
            QPushButton:disabled {
                background: #444;
                color: #888;
            }
        """)
        self.auth_btn.clicked.connect(self._on_authenticate_clicked)
        control_layout.addWidget(self.auth_btn)
        
        content_layout.addWidget(control_container, stretch=1)
        
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
            self.liveness_label.setText("✅ Face detected - Ready to authenticate")
            self.liveness_label.setStyleSheet("color: #00ff88; padding: 10px;")
        else:
            self.liveness_label.setText("⚠️ Position your face in the frame")
            self.liveness_label.setStyleSheet("color: #ffa500; padding: 10px;")
    
    def _on_authenticate_clicked(self):
        """Handle authenticate button click."""
        if not self.face_detected:
            self._show_status("No face detected", "⚠️", error=True)
            return
        
        if self.is_authenticating:
            return
        
        self.is_authenticating = True
        self.auth_btn.setEnabled(False)
        self._show_status("Authenticating...", "🔄", error=False)
        
        # Get current frame
        frame = self.camera_widget.get_current_frame()
        if frame is None:
            self._show_status("Failed to capture image", "❌", error=True)
            self.is_authenticating = False
            self.auth_btn.setEnabled(True)
            return
        
        # Convert frame to base64
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Prepare request data
        request_data = {"image": image_base64}
        
        # Add username if provided (1:1 verification)
        username = self.username_input.text().strip()
        if username:
            request_data["username"] = username
        
        # Send authentication request
        try:
            response = requests.post(
                f"{self.api_url}/api/authenticate",
                json=request_data,
                timeout=30
            )
            
            data = response.json()
            
            if data.get('authenticated'):
                user = data.get('user', {})
                self._show_success(user)
                self.authentication_success.emit(user)
            else:
                message = data.get('message', 'Authentication failed')
                self._show_status(message, "❌", error=True)
                self.authentication_failed.emit(message)
                
        except requests.exceptions.ConnectionError:
            self._show_status("Cannot connect to server", "❌", error=True)
        except Exception as e:
            self._show_status(f"Error: {str(e)}", "❌", error=True)
        finally:
            self.is_authenticating = False
            self.auth_btn.setEnabled(True)
    
    def _show_status(self, message: str, icon: str = "🔒", error: bool = False):
        """Show status message."""
        self.status_icon.setText(icon)
        self.status_label.setText(message)
        self.user_info_label.hide()
        self.similarity_label.hide()
        
        if error:
            self.status_label.setStyleSheet("color: #ff4444;")
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 68, 68, 0.1);
                    border: 1px solid #ff4444;
                    border-radius: 10px;
                    padding: 15px;
                }
            """)
        else:
            self.status_label.setStyleSheet("color: #888;")
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: #0f3460;
                    border-radius: 10px;
                    padding: 15px;
                }
            """)
    
    def _show_success(self, user: dict):
        """Show successful authentication."""
        self.status_icon.setText("✅")
        self.status_label.setText("Authentication Successful!")
        self.status_label.setStyleSheet("color: #00ff88;")
        
        username = user.get('username', 'Unknown')
        similarity = user.get('similarity', 0)
        
        self.user_info_label.setText(f"Welcome, {username}!")
        self.user_info_label.show()
        
        self.similarity_label.setText(f"Match confidence: {similarity*100:.1f}%")
        self.similarity_label.show()
        
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 255, 136, 0.1);
                border: 2px solid #00ff88;
                border-radius: 10px;
                padding: 15px;
            }
        """)
    
    def _on_back_clicked(self):
        """Handle back button click."""
        self._reset_status()
        self.back_requested.emit()
    
    def _reset_status(self):
        """Reset the status display."""
        self._show_status("Position your face and click Authenticate", "🔒", error=False)
        self.username_input.clear()
    
    def start_camera(self):
        """Start the camera."""
        self.camera_widget.start_camera()
    
    def stop_camera(self):
        """Stop the camera."""
        self.camera_widget.stop_camera()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self._reset_status()
        self.start_camera()
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        self.stop_camera()
