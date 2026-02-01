"""
Main Application Window for Face Authentication System.
Provides navigation between registration and authentication screens.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from .registration_screen import RegistrationScreen
from .authentication_screen import AuthenticationScreen


class HomeScreen(QWidget):
    """Home screen with navigation to registration and authentication."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(60, 40, 60, 40)
        
        # Spacer at top
        layout.addStretch(1)
        
        # Logo/Icon
        logo_label = QLabel("🔐")
        logo_label.setFont(QFont("Segoe UI", 72))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        # Title
        title = QLabel("Face Authentication System")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00d4ff, stop:1 #00ff88);
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Secure biometric authentication using facial recognition")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(40)
        
        # Buttons container
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setSpacing(30)
        
        # Register button
        self.register_btn = self._create_feature_button(
            "📝 Register",
            "Create a new user account",
            "#00d4ff",
            "#0099cc"
        )
        btn_layout.addWidget(self.register_btn)
        
        # Authenticate button
        self.auth_btn = self._create_feature_button(
            "🔓 Authenticate",
            "Verify your identity",
            "#00ff88",
            "#00cc6e"
        )
        btn_layout.addWidget(self.auth_btn)
        
        layout.addWidget(btn_container)
        
        # Spacer at bottom
        layout.addStretch(2)
        
        # Footer
        footer = QLabel("Powered by FaceNet • PyQt6 • OpenCV")
        footer.setFont(QFont("Segoe UI", 10))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #555;")
        layout.addWidget(footer)
    
    def _create_feature_button(
        self, 
        title: str, 
        description: str, 
        color1: str, 
        color2: str
    ) -> QPushButton:
        """Create a styled feature button."""
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumSize(250, 150)
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color1}, stop:1 {color2});
                color: white;
                border: none;
                border-radius: 15px;
                padding: 20px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color1}, stop:0.5 {color2}, stop:1 {color1});
            }}
            QPushButton:pressed {{
                background: {color2};
            }}
        """)
        
        # Create custom content
        btn_layout = QVBoxLayout(btn)
        btn_layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        btn_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 11))
        desc_label.setStyleSheet("color: rgba(255,255,255,0.8); background: transparent;")
        desc_label.setWordWrap(True)
        btn_layout.addWidget(desc_label)
        
        btn_layout.addStretch()
        
        return btn


class MainWindow(QMainWindow):
    """Main application window with screen navigation."""
    
    def __init__(self, api_url: str = "http://localhost:5000"):
        super().__init__()
        self.api_url = api_url
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the main window UI."""
        self.setWindowTitle("Face Authentication System")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget {
                background-color: #1a1a2e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
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
        
        # Add screens to stack
        self.stack.addWidget(self.home_screen)  # Index 0
        self.stack.addWidget(self.registration_screen)  # Index 1
        self.stack.addWidget(self.authentication_screen)  # Index 2
        
        layout.addWidget(self.stack)
    
    def _connect_signals(self):
        """Connect screen signals."""
        # Home screen
        self.home_screen.register_btn.clicked.connect(
            lambda: self.stack.setCurrentIndex(1)
        )
        self.home_screen.auth_btn.clicked.connect(
            lambda: self.stack.setCurrentIndex(2)
        )
        
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
    
    def _on_registration_success(self, username: str, user_id: int):
        """Handle successful registration."""
        print(f"User registered: {username} (ID: {user_id})")
    
    def _on_authentication_success(self, user_data: dict):
        """Handle successful authentication."""
        print(f"User authenticated: {user_data}")
    
    def closeEvent(self, event):
        """Handle window close."""
        # Stop cameras
        self.registration_screen.stop_camera()
        self.authentication_screen.stop_camera()
        super().closeEvent(event)


def main():
    """Main entry point for the desktop application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Face Authentication System")
    app.setOrganizationName("FaceAuth")
    
    # Set global style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow(api_url="http://localhost:5000")
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
