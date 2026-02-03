"""
Registration Screen for Face Authentication Desktop App.
Allows users to register with username and facial capture.
Features a simple, professional UI design.
"""

import base64
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import cv2
import numpy as np

from .camera_widget import CameraWidget


class RegistrationScreen(QWidget):
    """Registration screen."""
    
    registration_success = pyqtSignal(str, int)
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None, api_url: str = "http://localhost:5000"):
        super().__init__(parent)
        self.api_url = api_url
        self.face_detected = False
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
        
        title = QLabel("Register User")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #f1f5f9;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        # Spacer to balance back button
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
        
        # Right: Form
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: #334155;
                border: 1px solid #475569;
                border-radius: 8px;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)
        form_layout.setContentsMargins(30, 30, 30, 30)
        
        # Username
        username_label = QLabel("Username")
        username_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        username_label.setStyleSheet("color: #f1f5f9; background: transparent; border: none;")
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
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
        form_layout.addWidget(self.username_input)
        
        # Status
        self.status_label = QLabel("Position face in camera")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("color: #94a3b8; background: transparent; border: none;")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(self.status_label)
        
        form_layout.addStretch()
        
        # Register Button
        self.register_btn = QPushButton("Register")
        self.register_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_btn.setMinimumHeight(45)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #475569;
                color: #94a3b8;
            }
        """)
        self.register_btn.clicked.connect(self._on_register_clicked)
        form_layout.addWidget(self.register_btn)
        
        content_layout.addWidget(form_container, stretch=2)
        
        layout.addLayout(content_layout)
    
    def _on_face_detected(self, detected: bool, box):
        self.face_detected = detected
        
        # Don't overwrite status if locked (showing result)
        if hasattr(self, 'status_locked') and self.status_locked:
            return
            
        if detected:
            self.status_label.setText("Face detected")
            self.status_label.setStyleSheet("color: #4ade80; background: transparent; border: none;")
        else:
            self.status_label.setText("No face detected")
            self.status_label.setStyleSheet("color: #fbbf24; background: transparent; border: none;")
    
    def _on_register_clicked(self):
        username = self.username_input.text().strip()
        
        if not username:
            self.status_label.setText("Username required")
            self.status_label.setStyleSheet("color: #ef4444; background: transparent; border: none;")
            return
            
        if not self.face_detected:
            self.status_label.setText("Face not detected")
            self.status_label.setStyleSheet("color: #ef4444; background: transparent; border: none;")
            return
        
        self.register_btn.setEnabled(False)
        self.register_btn.setText("Processing...")
        
        # Lock status updates
        self.status_locked = True
        
        frame = self.camera_widget.get_current_frame()
        if frame is None:
            self.status_label.setText("Camera error")
            self.status_locked = False
            self.register_btn.setEnabled(True)
            self.register_btn.setText("Register")
            return

        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        try:
            response = requests.post(
                f"{self.api_url}/api/register",
                json={"username": username, "image": image_base64},
                timeout=30
            )
            data = response.json()
            
            if response.status_code == 201:
                self.status_label.setText("Registration Successful")
                self.status_label.setStyleSheet("color: #4ade80; background: transparent; border: none;")
                self.registration_success.emit(username, data.get('user_id', 0))
                self.username_input.clear()
            else:
                print(f"Registration error: {data.get('message', 'Unknown error')}")
                self.status_label.setText("Registration Failed")
                self.status_label.setStyleSheet("color: #ef4444; background: transparent; border: none;")
                
        except Exception as e:
            print(f"Registration exception: {str(e)}")
            self.status_label.setText("Registration Failed")
            self.status_label.setStyleSheet("color: #ef4444; background: transparent; border: none;")
        finally:
            self.register_btn.setEnabled(True)
            self.register_btn.setText("Register")
            
            # Unlock after 3 seconds
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, self._unlock_status)

    def _unlock_status(self):
        self.status_locked = False
        # Immediately update status based on current face state
        if self.face_detected:
            self.status_label.setText("Face detected")
            self.status_label.setStyleSheet("color: #4ade80; background: transparent; border: none;")
        else:
            self.status_label.setText("No face detected")
            self.status_label.setStyleSheet("color: #fbbf24; background: transparent; border: none;")

    def _on_back_clicked(self):
        self.back_requested.emit()
    
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
