"""
Desktop Application package for Face Authentication System.
"""

from .camera_widget import CameraWidget
from .registration_screen import RegistrationScreen
from .authentication_screen import AuthenticationScreen
from .main import MainWindow, main

__all__ = [
    'CameraWidget',
    'RegistrationScreen', 
    'AuthenticationScreen',
    'MainWindow',
    'main'
]
