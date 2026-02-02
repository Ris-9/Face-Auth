"""
User Management Screen for Face Authentication Desktop App.
Allows users to view and delete registered users.
"""

import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor


class UserCard(QFrame):
    """Individual user card with modern styling."""
    
    delete_clicked = pyqtSignal(int, str)  # user_id, username
    
    def __init__(self, user_id: int, username: str, created_at: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.username = username
        self._init_ui(created_at)
    
    def _init_ui(self, created_at: str):
        """Initialize the card UI."""
        self.setFixedHeight(80)
        self.setStyleSheet("""
            UserCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(22, 33, 62, 0.9), stop:1 rgba(15, 52, 96, 0.9));
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 12px;
            }
            UserCard:hover {
                border: 1px solid rgba(0, 212, 255, 0.5);
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(22, 33, 62, 1), stop:1 rgba(15, 52, 96, 1));
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # User avatar placeholder
        avatar = QLabel("👤")
        avatar.setFont(QFont("Segoe UI", 24))
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #00d4ff, stop:1 #0099cc);
            border-radius: 25px;
        """)
        layout.addWidget(avatar)
        
        # User info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        username_label = QLabel(self.username)
        username_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        username_label.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        info_layout.addWidget(username_label)
        
        date_label = QLabel(f"Registered: {created_at[:10] if created_at else 'N/A'}")
        date_label.setFont(QFont("Segoe UI", 10))
        date_label.setStyleSheet("color: #888888; background: transparent; border: none;")
        info_layout.addWidget(date_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setFont(QFont("Segoe UI", 11))
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setFixedWidth(100)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff4444, stop:1 #cc3333);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff5555, stop:1 #dd4444);
            }
            QPushButton:pressed {
                background: #cc2222;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.user_id, self.username))
        layout.addWidget(delete_btn)


class UserManagementScreen(QWidget):
    """User management screen with list of registered users."""
    
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
        layout.setSpacing(25)
        layout.setContentsMargins(50, 30, 50, 30)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Back button (left side)
        back_btn = QPushButton("← Back")
        back_btn.setFont(QFont("Segoe UI", 11))
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px 15px;
            }
            QPushButton:hover {
                color: #fff;
                border-color: #666;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        back_btn.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        # Title (center)
        title = QLabel("👥 User Management")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff6b6b, stop:1 #ffa500);
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button (right side)
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFont(QFont("Segoe UI", 11))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setFixedWidth(100)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #0099cc);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #33ddff, stop:1 #00aadd);
            }
        """)
        refresh_btn.clicked.connect(self.load_users)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel("Manage registered users and their face data")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)
        
        # Stats container
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(22, 33, 62, 0.8), stop:1 rgba(15, 52, 96, 0.8));
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 15px;
                padding: 15px;
            }
        """)
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setSpacing(40)
        
        # Total users stat
        self.total_users_label = QLabel("0")
        self.total_users_label.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        self.total_users_label.setStyleSheet("color: #00d4ff; background: transparent;")
        
        total_label = QLabel("Total Users")
        total_label.setFont(QFont("Segoe UI", 12))
        total_label.setStyleSheet("color: #888; background: transparent;")
        
        stat1_layout = QVBoxLayout()
        stat1_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stat1_layout.addWidget(self.total_users_label, alignment=Qt.AlignmentFlag.AlignCenter)
        stat1_layout.addWidget(total_label, alignment=Qt.AlignmentFlag.AlignCenter)
        stats_layout.addLayout(stat1_layout)
        
        layout.addWidget(self.stats_frame)
        
        # Users list container
        self.users_container = QFrame()
        self.users_container.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        self.users_layout = QVBoxLayout(self.users_container)
        self.users_layout.setSpacing(12)
        self.users_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area placeholder - we'll just add cards directly for simplicity
        layout.addWidget(self.users_container, stretch=1)
        
        # Empty state label
        self.empty_label = QLabel("No users registered yet.\nGo to Registration to add users.")
        self.empty_label.setFont(QFont("Segoe UI", 14))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #666;")
        self.empty_label.hide()
        layout.addWidget(self.empty_label)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
    
    def load_users(self):
        """Load users from the API."""
        self.status_label.setText("Loading users...")
        self.status_label.setStyleSheet("color: #888;")
        
        # Clear existing cards
        for card in self.user_cards:
            card.deleteLater()
        self.user_cards.clear()
        
        try:
            response = requests.get(f"{self.api_url}/api/users", timeout=10)
            data = response.json()
            
            if data.get('success'):
                users = data.get('users', [])
                self.total_users_label.setText(str(len(users)))
                
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
                    
                    # Add stretch at the end
                    self.users_layout.addStretch()
                    self.status_label.setText(f"Loaded {len(users)} user(s)")
                    self.status_label.setStyleSheet("color: #00ff88;")
                else:
                    self.empty_label.show()
                    self.status_label.setText("No users found")
                    self.status_label.setStyleSheet("color: #888;")
            else:
                self.status_label.setText(f"Error: {data.get('message', 'Failed to load users')}")
                self.status_label.setStyleSheet("color: #ff4444;")
                
        except requests.exceptions.ConnectionError:
            self.status_label.setText("❌ Cannot connect to server. Make sure the backend is running.")
            self.status_label.setStyleSheet("color: #ff4444;")
            self.empty_label.show()
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: #ff4444;")
    
    def _on_delete_user(self, user_id: int, username: str):
        """Handle delete user request."""
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete user '{username}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.status_label.setText(f"Deleting {username}...")
        self.status_label.setStyleSheet("color: #ffa500;")
        
        try:
            response = requests.delete(
                f"{self.api_url}/api/users/{user_id}",
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                self.status_label.setText(f"✅ User '{username}' deleted successfully")
                self.status_label.setStyleSheet("color: #00ff88;")
                self.user_deleted.emit(username)
                # Reload users list
                self.load_users()
            else:
                self.status_label.setText(f"❌ {data.get('message', 'Failed to delete user')}")
                self.status_label.setStyleSheet("color: #ff4444;")
                
        except requests.exceptions.ConnectionError:
            self.status_label.setText("❌ Cannot connect to server")
            self.status_label.setStyleSheet("color: #ff4444;")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: #ff4444;")
    
    def _on_back_clicked(self):
        """Handle back button click."""
        self.back_requested.emit()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.load_users()
