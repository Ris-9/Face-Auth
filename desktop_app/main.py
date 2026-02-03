"""
Main Application Window for Face Authentication System.
Provides navigation between registration, authentication, and user management screens.
Features a simple, professional UI design.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette

from .registration_screen import RegistrationScreen
from .authentication_screen import AuthenticationScreen
from .user_management_screen import UserManagementScreen


class FeatureCard(QFrame):
    """Simple feature card for navigation."""
    
    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_style()
        self._init_ui(title, description)
    
    def _setup_style(self):
        """Setup the card styling."""
        self.setStyleSheet("""
            FeatureCard {
                background-color: #334155;
                border: 1px solid #475569;
                border-radius: 8px;
            }
            FeatureCard:hover {
                background-color: #475569;
                border: 1px solid #64748b;
            }
        """)
    
    def _init_ui(self, title: str, description: str):
        """Initialize the card UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #f1f5f9; background: transparent;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 11))
        desc_label.setStyleSheet("color: #cbd5e1; background: transparent;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Arrow indicator
        arrow = QLabel(">")
        arrow.setFont(QFont("Segoe UI", 16))
        arrow.setStyleSheet("color: #94a3b8; background: transparent;")
        arrow.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(arrow)
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_signal()
        super().mousePressEvent(event)
    
    def clicked_signal(self):
        """Override this method or connect to handle clicks."""
        pass


class HomeScreen(QWidget):
    """Home screen with navigation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(60, 50, 60, 40)
        
        # Spacer at top
        layout.addStretch(1)
        
        # Title
        title = QLabel("Face Authentication System")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #f1f5f9;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Secure biometric authentication")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(40)
        
        # Feature cards container
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setSpacing(20)
        
        # Register Card
        self.register_card = FeatureCard(
            title="Register",
            description="Create a new user account"
        )
        cards_layout.addWidget(self.register_card)
        
        # Authenticate Card
        self.auth_card = FeatureCard(
            title="Authenticate",
            description="Verify user identity"
        )
        cards_layout.addWidget(self.auth_card)
        
        # Manage Users Card
        self.manage_card = FeatureCard(
            title="Manage Users",
            description="View and delete users"
        )
        cards_layout.addWidget(self.manage_card)
        
        layout.addWidget(cards_container)
        
        # Spacer at bottom
        layout.addStretch(2)
        
        # Footer
        footer = QLabel("Face Authentication System v1.0")
        footer.setFont(QFont("Segoe UI", 10))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #64748b;")
        layout.addWidget(footer)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, api_url: str = "http://localhost:5000"):
        super().__init__()
        self.api_url = api_url
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the main window UI."""
        self.setWindowTitle("Face Authentication System")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)
        
        # Set simple dark theme styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e293b;
            }
            QWidget {
                background-color: #1e293b;
                color: #f1f5f9;
            }
            QMessageBox {
                background-color: #1e293b;
            }
            QMessageBox QLabel {
                color: #f1f5f9;
            }
            QMessageBox QPushButton {
                background-color: #334155;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 6px 15px;
            }
            QMessageBox QPushButton:hover {
                background-color: #475569;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for screen navigation
        self.stack = QStackedWidget()
        
        # Create screens
        self.home_screen = HomeScreen()
        self.registration_screen = RegistrationScreen(api_url=self.api_url)
        self.authentication_screen = AuthenticationScreen(api_url=self.api_url)
        self.user_management_screen = UserManagementScreen(api_url=self.api_url)
        
        # Add screens to stack
        self.stack.addWidget(self.home_screen)  # Index 0
        self.stack.addWidget(self.registration_screen)  # Index 1
        self.stack.addWidget(self.authentication_screen)  # Index 2
        self.stack.addWidget(self.user_management_screen)  # Index 3
        
        layout.addWidget(self.stack)
    
    def _connect_signals(self):
        """Connect screen signals."""
        # Home screen
        self.home_screen.register_card.mousePressEvent = lambda e: self.stack.setCurrentIndex(1)
        self.home_screen.auth_card.mousePressEvent = lambda e: self.stack.setCurrentIndex(2)
        self.home_screen.manage_card.mousePressEvent = lambda e: self.stack.setCurrentIndex(3)
        
        # Registration screen
        self.registration_screen.back_requested.connect(
            lambda: self.stack.setCurrentIndex(0)
        )
        self.registration_screen.registration_success.connect(
            self._on_registration_success
        )
        
        # Authentication screen
        self.authentication_screen.back_requested.connect(
            lambda: self.stack.setCurrentIndex(0)
        )
        self.authentication_screen.authentication_success.connect(
            self._on_authentication_success
        )
        
        # User management screen
        self.user_management_screen.back_requested.connect(
            lambda: self.stack.setCurrentIndex(0)
        )
        self.user_management_screen.user_deleted.connect(
            self._on_user_deleted
        )
    
    def _on_registration_success(self, username: str, user_id: int):
        print(f"User registered: {username}")
    
    def _on_authentication_success(self, user_data: dict):
        print(f"User authenticated: {user_data}")
    
    def _on_user_deleted(self, username: str):
        print(f"User deleted: {username}")
    
    def closeEvent(self, event):
        """Handle window close."""
        self.registration_screen.stop_camera()
        self.authentication_screen.stop_camera()
        super().closeEvent(event)


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    app.setApplicationName("Face Authentication System")
    app.setOrganizationName("FaceIcon")
    app.setStyle("Fusion")
    
    # Simple dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor("#1e293b"))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor("#f1f5f9"))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor("#0f172a"))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1e293b"))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#f1f5f9"))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f1f5f9"))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor("#f1f5f9"))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor("#334155"))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f1f5f9"))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor("#3b82f6"))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor("#3b82f6"))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
    app.setPalette(dark_palette)
    
    window = MainWindow(api_url="http://localhost:5000")
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
