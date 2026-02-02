"""
Authentication Screen for Face Authentication Desktop App.
Allows users to authenticate using facial recognition.
Features modern UI with glassmorphism and gradient effects.
"""

import base64
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor
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
        
        title_icon = QLabel("🔓")
        title_icon.setFont(QFont("Segoe UI Emoji", 36))
        title_layout.addWidget(title_icon)
        
        title = QLabel("Face Authentication")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #00ff88;")
        title_layout.addWidget(title)
        
        layout.addWidget(title_container)
        
        # Subtitle
        subtitle = QLabel("Verify your identity with a quick face scan")
        subtitle.setFont(QFont("Segoe UI", 13))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        layout.addWidget(subtitle)
        
        layout.addSpacing(15)
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(35)
        
        # Left side - Camera
        camera_container = self._create_camera_section()
        content_layout.addWidget(camera_container, stretch=3)
        
        # Right side - Status and controls
        control_container = self._create_control_section()
        content_layout.addWidget(control_container, stretch=2)
        
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
                border: 1px solid rgba(0, 255, 136, 0.2);
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
        
        # Liveness indicator
        self.liveness_frame = QFrame()
        self.liveness_frame.setStyleSheet("""
            QFrame {
                background: rgba(136, 136, 136, 0.1);
                border: 1px solid rgba(136, 136, 136, 0.3);
                border-radius: 10px;
                padding: 5px;
            }
        """)
        liveness_layout = QHBoxLayout(self.liveness_frame)
        liveness_layout.setContentsMargins(15, 10, 15, 10)
        
        self.liveness_icon = QLabel("🔄")
        self.liveness_icon.setFont(QFont("Segoe UI Emoji", 16))
        liveness_layout.addWidget(self.liveness_icon)
        
        self.liveness_label = QLabel("Position your face in the frame")
        self.liveness_label.setFont(QFont("Segoe UI", 12))
        self.liveness_label.setStyleSheet("color: #888; background: transparent;")
        liveness_layout.addWidget(self.liveness_label)
        liveness_layout.addStretch()
        
        camera_layout.addWidget(self.liveness_frame)
        
        return camera_container
    
    def _create_control_section(self) -> QFrame:
        """Create control section with styling."""
        control_container = QFrame()
        control_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(22, 33, 62, 0.9), stop:1 rgba(15, 52, 96, 0.9));
                border: 1px solid rgba(0, 255, 136, 0.2);
                border-radius: 20px;
            }
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        control_container.setGraphicsEffect(shadow)
        
        control_layout = QVBoxLayout(control_container)
        control_layout.setSpacing(20)
        control_layout.setContentsMargins(30, 30, 30, 30)
        
        # Optional username input
        username_label = QLabel("👤 Username (Optional)")
        username_label.setFont(QFont("Segoe UI", 12))
        username_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background: transparent;")
        control_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Leave empty for 1:N identification")
        self.username_input.setFont(QFont("Segoe UI", 12))
        self.username_input.setMinimumHeight(45)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(15, 52, 96, 0.8);
                border: 2px solid rgba(0, 255, 136, 0.2);
                border-radius: 10px;
                padding: 10px 15px;
                color: #fff;
            }
            QLineEdit:focus {
                border-color: #00ff88;
                background-color: rgba(15, 52, 96, 1);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        control_layout.addWidget(self.username_input)
        
        control_layout.addSpacing(10)
        
        # Status display card
        self.status_frame = QFrame()
        self.status_frame.setMinimumHeight(180)
        self.status_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 52, 96, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 15px;
            }
        """)
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setSpacing(10)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_icon = QLabel("🔒")
        self.status_icon.setFont(QFont("Segoe UI Emoji", 52))
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_icon.setStyleSheet("background: transparent;")
        status_layout.addWidget(self.status_icon)
        
        self.status_label = QLabel("Position your face and click Authenticate")
        self.status_label.setFont(QFont("Segoe UI", 12))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent;")
        status_layout.addWidget(self.status_label)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_info_label.setStyleSheet("color: #00ff88; background: transparent;")
        self.user_info_label.hide()
        status_layout.addWidget(self.user_info_label)
        
        self.similarity_label = QLabel("")
        self.similarity_label.setFont(QFont("Segoe UI", 11))
        self.similarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.similarity_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); background: transparent;")
        self.similarity_label.hide()
        status_layout.addWidget(self.similarity_label)
        
        control_layout.addWidget(self.status_frame)
        
        control_layout.addStretch()
        
        # Authenticate button
        self.auth_btn = QPushButton("🔓 Authenticate")
        self.auth_btn.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.auth_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auth_btn.setMinimumHeight(55)
        self.auth_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88, stop:1 #00cc6e);
                color: #0d1117;
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-weight: bold;
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
                background: rgba(68, 68, 68, 0.5);
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.auth_btn.clicked.connect(self._on_authenticate_clicked)
        control_layout.addWidget(self.auth_btn)
        
        # Quick tips
        tips_label = QLabel("💡 Tip: For faster verification, enter your username")
        tips_label.setFont(QFont("Segoe UI", 10))
        tips_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tips_label.setStyleSheet("color: rgba(255, 255, 255, 0.4); background: transparent;")
        control_layout.addWidget(tips_label)
        
        return control_container
    
    def _on_face_detected(self, detected: bool, box):
        """Handle face detection status."""
        self.face_detected = detected
        
        if detected:
            self.liveness_icon.setText("✅")
            self.liveness_label.setText("Face detected - Ready to authenticate")
            self.liveness_label.setStyleSheet("color: #00ff88; background: transparent;")
            self.liveness_frame.setStyleSheet("""
                QFrame {
                    background: rgba(0, 255, 136, 0.1);
                    border: 1px solid rgba(0, 255, 136, 0.3);
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
        else:
            self.liveness_icon.setText("⚠️")
            self.liveness_label.setText("Position your face in the frame")
            self.liveness_label.setStyleSheet("color: #ffa500; background: transparent;")
            self.liveness_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 165, 0, 0.1);
                    border: 1px solid rgba(255, 165, 0, 0.3);
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
    
    def _on_authenticate_clicked(self):
        """Handle authenticate button click."""
        if not self.face_detected:
            self._show_status("No face detected", "⚠️", error=True)
            return
        
        if self.is_authenticating:
            return
        
        self.is_authenticating = True
        self.auth_btn.setEnabled(False)
        self.auth_btn.setText("⏳ Authenticating...")
        self._show_status("Verifying identity...", "🔄", error=False)
        
        # Get current frame
        frame = self.camera_widget.get_current_frame()
        if frame is None:
            self._show_status("Failed to capture image", "❌", error=True)
            self.is_authenticating = False
            self.auth_btn.setEnabled(True)
            self.auth_btn.setText("🔓 Authenticate")
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
            self.auth_btn.setText("🔓 Authenticate")
    
    def _show_status(self, message: str, icon: str = "🔒", error: bool = False):
        """Show status message."""
        self.status_icon.setText(icon)
        self.status_label.setText(message)
        self.user_info_label.hide()
        self.similarity_label.hide()
        
        if error:
            self.status_label.setStyleSheet("color: #ff4444; background: transparent;")
            self.status_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 68, 68, 0.1);
                    border: 2px solid rgba(255, 68, 68, 0.5);
                    border-radius: 15px;
                }
            """)
        else:
            self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent;")
            self.status_frame.setStyleSheet("""
                QFrame {
                    background: rgba(15, 52, 96, 0.8);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                }
            """)
    
    def _show_success(self, user: dict):
        """Show successful authentication."""
        self.status_icon.setText("✅")
        self.status_label.setText("Authentication Successful!")
        self.status_label.setStyleSheet("color: #00ff88; background: transparent;")
        
        username = user.get('username', 'Unknown')
        similarity = user.get('similarity', 0)
        
        self.user_info_label.setText(f"Welcome, {username}!")
        self.user_info_label.show()
        
        self.similarity_label.setText(f"Match confidence: {similarity*100:.1f}%")
        self.similarity_label.show()
        
        self.status_frame.setStyleSheet("""
            QFrame {
                background: rgba(0, 255, 136, 0.15);
                border: 2px solid rgba(0, 255, 136, 0.6);
                border-radius: 15px;
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
