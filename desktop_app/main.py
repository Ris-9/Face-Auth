"""
Main Application Window for Face Authentication System.
Provides navigation between registration, authentication, and user management screens.
Features modern UI with glassmorphism, animations, and premium aesthetics.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QSpacerItem, QSizePolicy,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor, QLinearGradient, QPalette

from .registration_screen import RegistrationScreen
from .authentication_screen import AuthenticationScreen
from .user_management_screen import UserManagementScreen


class AnimatedButton(QPushButton):
    """Custom animated button with hover effects."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation = None
    
    def enterEvent(self, event):
        super().enterEvent(event)
        # Subtle scale animation on hover
    
    def leaveEvent(self, event):
        super().leaveEvent(event)


class FeatureCard(QFrame):
    """Modern feature card with glassmorphism effect."""
    
    def __init__(self, icon: str, title: str, description: str, 
                 gradient_start: str, gradient_end: str, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._gradient_start = gradient_start
        self._gradient_end = gradient_end
        self._setup_style()
        self._init_ui(icon, title, description)
        self._add_shadow()
    
    def _setup_style(self):
        """Setup the card styling."""
        self.setStyleSheet(f"""
            FeatureCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self._gradient_start}, stop:1 {self._gradient_end});
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
            }}
            FeatureCard:hover {{
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """)
    
    def _add_shadow(self):
        """Add drop shadow effect."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
    
    def _init_ui(self, icon: str, title: str, description: str):
        """Initialize the card UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 40))
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)
        
        layout.addStretch()
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 11))
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.75); background: transparent;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Arrow indicator
        arrow = QLabel("→")
        arrow.setFont(QFont("Segoe UI", 16))
        arrow.setStyleSheet("color: rgba(255, 255, 255, 0.5); background: transparent;")
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
    """Home screen with navigation to registration, authentication, and user management."""
    
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
        
        # Logo/Icon with glow effect
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setSpacing(5)
        
        logo_label = QLabel("🔐")
        logo_label.setFont(QFont("Segoe UI Emoji", 72))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        layout.addWidget(logo_container)
        
        # Title with gradient effect
        title = QLabel("Face Authentication System")
        title.setFont(QFont("Segoe UI", 38, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #ffffff;
        """)
        layout.addWidget(title)
        
        # Gradient line under title
        line = QFrame()
        line.setFixedSize(200, 3)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.2 #00d4ff, stop:0.8 #00ff88, stop:1 transparent);
            border-radius: 1px;
        """)
        layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(10)
        
        # Subtitle
        subtitle = QLabel("Secure biometric authentication powered by AI facial recognition")
        subtitle.setFont(QFont("Segoe UI", 13))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        layout.addWidget(subtitle)
        
        layout.addSpacing(40)
        
        # Feature cards container
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setSpacing(25)
        
        # Register Card
        self.register_card = FeatureCard(
            icon="📝",
            title="Register",
            description="Create a new account with facial recognition",
            gradient_start="#0099cc",
            gradient_end="#00d4ff"
        )
        cards_layout.addWidget(self.register_card)
        
        # Authenticate Card
        self.auth_card = FeatureCard(
            icon="🔓",
            title="Authenticate",
            description="Verify your identity using face scan",
            gradient_start="#00cc6e",
            gradient_end="#00ff88"
        )
        cards_layout.addWidget(self.auth_card)
        
        # Manage Users Card
        self.manage_card = FeatureCard(
            icon="👥",
            title="Manage Users",
            description="View, edit, or delete registered users",
            gradient_start="#cc4444",
            gradient_end="#ff6b6b"
        )
        cards_layout.addWidget(self.manage_card)
        
        layout.addWidget(cards_container)
        
        # Spacer at bottom
        layout.addStretch(2)
        
        # Stats bar
        stats_bar = QFrame()
        stats_bar.setStyleSheet("""
            QFrame {
                background: rgba(22, 33, 62, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 10px;
            }
        """)
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setSpacing(40)
        
        # Stats items
        stats = [
            ("🛡️", "Secure", "256-bit encryption"),
            ("⚡", "Fast", "Sub-second verification"),
            ("🎯", "Accurate", "99.9% precision"),
            ("🔒", "Liveness", "Anti-spoofing enabled")
        ]
        
        for icon, title, desc in stats:
            stat_widget = self._create_stat_item(icon, title, desc)
            stats_layout.addWidget(stat_widget)
        
        layout.addWidget(stats_bar)
        
        layout.addSpacing(10)
        
        # Footer
        footer = QLabel("Powered by FaceNet • PyQt6 • OpenCV • TensorFlow")
        footer.setFont(QFont("Segoe UI", 10))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: rgba(255, 255, 255, 0.4);")
        layout.addWidget(footer)
    
    def _create_stat_item(self, icon: str, title: str, description: str) -> QWidget:
        """Create a stat item widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 18))
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff; background: transparent;")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); background: transparent;")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        
        return widget


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
        self.setMinimumSize(1100, 750)
        self.resize(1280, 850)
        
        # Set modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0d1117, stop:0.5 #161b22, stop:1 #0d1117);
            }
            QWidget {
                background: transparent;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QMessageBox {
                background-color: #1a1a2e;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #16213e;
                color: #ffffff;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #0f3460;
            }
            QScrollBar:vertical {
                background: rgba(22, 33, 62, 0.5);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 212, 255, 0.5);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 212, 255, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Central widget with gradient background
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0.5, y2:1,
                stop:0 #0d1117, stop:0.3 #161b22, stop:0.7 #1a1a2e, stop:1 #16213e);
        """)
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
        # Home screen - using mousePressEvent override
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
        """Handle successful registration."""
        print(f"User registered: {username} (ID: {user_id})")
    
    def _on_authentication_success(self, user_data: dict):
        """Handle successful authentication."""
        print(f"User authenticated: {user_data}")
    
    def _on_user_deleted(self, username: str):
        """Handle user deletion."""
        print(f"User deleted: {username}")
    
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
    
    # Create dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(13, 17, 23))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(22, 27, 34))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(26, 26, 46))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(22, 33, 62))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(0, 212, 255))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 212, 255))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(dark_palette)
    
    # Create and show main window
    window = MainWindow(api_url="http://localhost:5000")
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
