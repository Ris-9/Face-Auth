"""
Backend package for Face Authentication System.
"""

from .database import Database
from .face_recognition_module import FaceRecognition
from .liveness_detection import LivenessDetector

__all__ = ['Database', 'FaceRecognition', 'LivenessDetector']
