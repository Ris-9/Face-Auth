"""
Authentication Screen for Face Authentication Desktop App.
Allows users to authenticate using facial recognition.
Features a simple, professional UI design.
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
    """Authentication screen."""
    
    authentication_success = pyqtSignal(dict)
    authentication_failed = pyqtSignal(str)
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
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Header
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("< Back")
        back_btn.setFont(QFont("Segoe UI", 10))
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setFixedSize(80, 32)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        back_btn.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        title = QLabel("Authentication")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #f1f5f9;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        spacer = QWidget()
        spacer.setFixedSize(80, 32)
        header_layout.addWidget(spacer)
        
        layout.addLayout(header_layout)
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        # Left: Camera
        camera_container = QFrame()
        camera_container.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(10, 10, 10, 10)
        
        self.camera_widget = CameraWidget(show_face_box=True, mirror=True)
        self.camera_widget.face_detected.connect(self._on_face_detected)
        self.camera_widget.setMinimumHeight(400)
        camera_layout.addWidget(self.camera_widget)
        
        content_layout.addWidget(camera_container, stretch=3)
        
        # Right: Controls
        control_container = QFrame()
        control_container.setStyleSheet("""
            QFrame {
                background-color: #334155;
                border: 1px solid #475569;
                border-radius: 8px;
            }
        """)
        control_layout = QVBoxLayout(control_container)
        control_layout.setSpacing(20)
        control_layout.setContentsMargins(30, 30, 30, 30)
        
        # Username optional
        username_label = QLabel("Username (Optional)")
        username_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        username_label.setStyleSheet("color: #f1f5f9; background: transparent; border: none;")
        control_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("For 1:1 verification")
        self.username_input.setFont(QFont("Segoe UI", 11))
        self.username_input.setMinimumHeight(40)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 5px 10px;
                color: #f1f5f9;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        control_layout.addWidget(self.username_input)
        
        # Status Card
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 20px;
                min-height: 80px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("Ready to authenticate")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #e2e8f0; background: transparent; border: none;")
        status_layout.addWidget(self.status_label)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_info_label.setStyleSheet("color: #f1f5f9; background: transparent; border: none;")
        self.user_info_label.hide()
        status_layout.addWidget(self.user_info_label)
        
        control_layout.addWidget(status_frame)
        
        control_layout.addStretch()
        
        # Auth Button
        self.auth_btn = QPushButton("Authenticate")
        self.auth_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.auth_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auth_btn.setMinimumHeight(45)
        self.auth_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #475569;
                color: #94a3b8;
            }
        """)
        self.auth_btn.clicked.connect(self._on_authenticate_clicked)
        control_layout.addWidget(self.auth_btn)
        
        content_layout.addWidget(control_container, stretch=2)
        layout.addLayout(content_layout)
    
    def _on_face_detected(self, detected: bool, box):
        self.face_detected = detected
        
        # Don't overwrite status if locked (showing result or authenticating)
        if hasattr(self, 'status_locked') and self.status_locked:
            return
            
        if detected:
            self.status_label.setText("Face detected")
            self.status_label.setStyleSheet("color: #4ade80; background: transparent; border: none;")
        else:
            self.status_label.setText("No face detected")
            self.status_label.setStyleSheet("color: #fbbf24; background: transparent; border: none;")
    
    def _on_authenticate_clicked(self):
        if not self.face_detected:
            self.status_label.setText("No face detected")
            self.status_label.setStyleSheet("color: #ef4444; background: transparent; border: none;")
            return
        
        if self.is_authenticating:
            return
            
        self.is_authenticating = True
        self.status_locked = True  # Lock status updates
        
        self.auth_btn.setEnabled(False)
        self.auth_btn.setText("Verifying...")
        self.status_label.setText("Authenticating...")
        self.status_label.setStyleSheet("color: #94a3b8; background: transparent; border: none;")
        self.user_info_label.hide()
        
        frame = self.camera_widget.get_current_frame()
        if frame is None:
            self.status_label.setText("Camera error")
            self.is_authenticating = False
            self.status_locked = False
            self.auth_btn.setEnabled(True)
            self.auth_btn.setText("Authenticate")
            return
            
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        req_data = {"image": image_base64}
        username = self.username_input.text().strip()
        if username:
            req_data["username"] = username
            
        try:
            response = requests.post(
                f"{self.api_url}/api/authenticate",
                json=req_data,
                timeout=30
            )
            data = response.json()
            
            if data.get('authenticated'):
                user = data.get('user', {})
                self.status_label.setText("Authentication Successful")
                self.status_label.setStyleSheet("color: #4ade80; background: transparent; border: none;")
                self.user_info_label.setText(f"Welcome, {user.get('username')}")
                self.user_info_label.show()
                self.authentication_success.emit(user)
            else:
                print(f"Auth failed: {data.get('message', 'Unknown reason')}")
                self.status_label.setText("Authentication Failed")
                self.status_label.setStyleSheet("color: #ef4444; background: transparent; border: none;")
        except Exception as e:
            print(f"Auth error: {str(e)}")
            self.status_label.setText("Authentication Failed")
            self.status_label.setStyleSheet("color: #ef4444; background: transparent; border: none;")
        finally:
            self.is_authenticating = False
            self.auth_btn.setEnabled(True)
            self.auth_btn.setText("Authenticate")
            
            # Unlock after 3 seconds
            QTimer.singleShot(3000, self._unlock_status)
    
    def _unlock_status(self):
        self.status_locked = False
        # If we have a user info label shown (success state), maybe we should keep it until face is lost?
        # But for now, let's just reset to face detection status to allow re-auth.
        # However, "Welcome, User" is nice to keep.
        # If I unlock, "Face detected" will appear.
        # Maybe I should only unlock if "Authentication Failed"?
        # If "Successful", we might want to stay successful until user leaves?
        # But the user might want to scan another person.
        # Let's clean up user info on unlock if we want to reset.
        
        # Actually, if successful, 'Welcome user' is in a separate label (user_info_label).
        # The status_label says "Authentication Successful".
        # If I unlock, status_label becomes "Face detected".
        # user_info_label remains visible? Yes, until I hide it.
        # When do I hide it? In _on_authenticate_clicked (start of next auth).
        # So it's fine.
        
        if self.face_detected:
            self.status_label.setText("Face detected")
            self.status_label.setStyleSheet("color: #4ade80; background: transparent; border: none;")
        else:
            self.status_label.setText("No face detected")
            self.status_label.setStyleSheet("color: #fbbf24; background: transparent; border: none;")
            
    def _on_back_clicked(self):
        self.back_requested.emit()
        self.status_label.setText("Ready to authenticate")
        self.status_label.setStyleSheet("color: #e2e8f0; background: transparent; border: none;")
        self.user_info_label.hide()
        self.username_input.clear()


        
    def start_camera(self):
        self.camera_widget.start_camera()
    
    def stop_camera(self):
        self.camera_widget.stop_camera()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.start_camera()
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_camera()
