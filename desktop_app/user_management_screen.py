"""
User Management Screen for Face Authentication Desktop App.
Allows users to view and delete registered users.
Features a simple, professional UI design.
"""

import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class UserCard(QFrame):
    """Simple user card."""
    
    delete_clicked = pyqtSignal(int, str)  # user_id, username
    
    def __init__(self, user_id: int, username: str, created_at: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.username = username
        self._init_ui(created_at)
    
    def _init_ui(self, created_at: str):
        """Initialize the card UI."""
        self.setFixedHeight(70)
        self.setStyleSheet("""
            UserCard {
                background-color: #334155;
                border: 1px solid #475569;
                border-radius: 6px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # User info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        username_label = QLabel(self.username)
        username_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        username_label.setStyleSheet("color: #f1f5f9; border: none; background: transparent;")
        info_layout.addWidget(username_label)
        
        date_label = QLabel(f"Registered: {created_at[:10] if created_at else 'N/A'}")
        date_label.setFont(QFont("Segoe UI", 9))
        date_label.setStyleSheet("color: #94a3b8; border: none; background: transparent;")
        info_layout.addWidget(date_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setFont(QFont("Segoe UI", 10))
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setFixedSize(80, 30)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:pressed {
                background-color: #b91c1c;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.user_id, self.username))
        layout.addWidget(delete_btn)


class UserManagementScreen(QWidget):
    """User management screen."""
    
    back_requested = pyqtSignal()
    user_deleted = pyqtSignal(str)  # username
    
    def __init__(self, parent=None, api_url: str = "http://localhost:5000"):
        super().__init__(parent)
        self.api_url = api_url
        self.user_cards = []
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Back button
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
        
        # Title
        title = QLabel("User Management")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #f1f5f9;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFont(QFont("Segoe UI", 10))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setFixedSize(80, 32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        refresh_btn.clicked.connect(self.load_users)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Total users label
        self.total_users_label = QLabel("Total Users: 0")
        self.total_users_label.setFont(QFont("Segoe UI", 11))
        self.total_users_label.setStyleSheet("color: #94a3b8;")
        self.total_users_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.total_users_label)
        
        # Users list container
        self.users_container = QWidget()
        self.users_layout = QVBoxLayout(self.users_container)
        self.users_layout.setSpacing(10)
        self.users_layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(self.users_container, stretch=1)
        
        # Empty state label
        self.empty_label = QLabel("No users found")
        self.empty_label.setFont(QFont("Segoe UI", 12))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #64748b;")
        self.empty_label.hide()
        layout.addWidget(self.empty_label)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #94a3b8;")
        layout.addWidget(self.status_label)
    
    def load_users(self):
        """Load users from the API."""
        self.status_label.setText("Loading...")
        
        # Clear existing cards
        for card in self.user_cards:
            card.deleteLater()
        self.user_cards.clear()
        
        try:
            response = requests.get(f"{self.api_url}/api/users", timeout=10)
            data = response.json()
            
            if data.get('success'):
                users = data.get('users', [])
                self.total_users_label.setText(f"Total Users: {len(users)}")
                
                if users:
                    self.empty_label.hide()
                    for user in users:
                        card = UserCard(
                            user['id'],
                            user['username'],
                            user.get('created_at', ''),
                            self.users_container
                        )
                        card.delete_clicked.connect(self._on_delete_user)
                        self.users_layout.addWidget(card)
                        self.user_cards.append(card)
                    
                    self.users_layout.addStretch()
                    self.status_label.setText("")
                else:
                    self.empty_label.show()
                    self.status_label.setText("")
            else:
                self.status_label.setText(f"Error: {data.get('message')}")
                
        except Exception as e:
            self.status_label.setText("Connection error")
            self.empty_label.show()
    
    def _on_delete_user(self, user_id: int, username: str):
        """Handle delete user request."""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete user '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            response = requests.delete(f"{self.api_url}/api/users/{user_id}", timeout=10)
            if response.json().get('success'):
                self.user_deleted.emit(username)
                self.load_users()
            else:
                self.status_label.setText("Failed to delete user")
        except Exception:
            self.status_label.setText("Error deleting user")
    
    def _on_back_clicked(self):
        self.back_requested.emit()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_users()
