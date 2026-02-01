"""
Liveness Detection module for anti-spoofing.
Uses blink detection, head movement, and texture analysis.
"""

import numpy as np
import cv2
from typing import Tuple, List, Optional
from collections import deque
import time


class LivenessDetector:
    """
    Multi-factor liveness detection to prevent spoofing attacks.
    
    Implements:
    - Blink detection using Eye Aspect Ratio (EAR)
    - Head movement detection via frame differencing
    - Texture analysis using Laplacian variance (blur detection)
    """
    
    # Eye landmark indices for dlib 68-point model
    LEFT_EYE_INDICES = [36, 37, 38, 39, 40, 41]
    RIGHT_EYE_INDICES = [42, 43, 44, 45, 46, 47]
    
    def __init__(
        self,
        ear_threshold: float = 0.25,
        blink_consec_frames: int = 2,
        movement_threshold: float = 5.0,
        texture_threshold: float = 100.0,
        history_size: int = 30
    ):
        """
        Initialize liveness detector.
        
        Args:
            ear_threshold: EAR below this indicates closed eye
            blink_consec_frames: Consecutive frames for blink detection
            movement_threshold: Minimum movement for liveness
            texture_threshold: Minimum Laplacian variance (higher = more detail)
            history_size: Number of frames to keep in history
        """
        self.ear_threshold = ear_threshold
        self.blink_consec_frames = blink_consec_frames
        self.movement_threshold = movement_threshold
        self.texture_threshold = texture_threshold
        self.history_size = history_size
        
        # Frame history for movement detection
        self.frame_history = deque(maxlen=history_size)
        self.face_positions = deque(maxlen=history_size)
        
        # Blink tracking
        self.blink_counter = 0
        self.blink_total = 0
        self.ear_history = deque(maxlen=history_size)
        
        # Load Haar cascade for face detection (fallback)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        
        # Liveness session tracking
        self.session_start_time = None
        self.challenges_completed = set()
    
    def calculate_ear(self, eye_points: np.ndarray) -> float:
        """
        Calculate Eye Aspect Ratio (EAR).
        
        EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
        
        Args:
            eye_points: 6 landmark points for one eye
            
        Returns:
            EAR value (lower = more closed)
        """
        # Vertical distances
        v1 = np.linalg.norm(eye_points[1] - eye_points[5])
        v2 = np.linalg.norm(eye_points[2] - eye_points[4])
        
        # Horizontal distance
        h = np.linalg.norm(eye_points[0] - eye_points[3])
        
        if h == 0:
            return 0.0
        
        ear = (v1 + v2) / (2.0 * h)
        return ear
    
    def detect_blink_simple(self, frame: np.ndarray, face_box: np.ndarray) -> Tuple[bool, float]:
        """
        Simple blink detection using eye detection within face region.
        
        Args:
            frame: BGR image
            face_box: [x1, y1, x2, y2] face bounding box
            
        Returns:
            Tuple of (blink_detected, eye_openness_score)
        """
        x1, y1, x2, y2 = [int(b) for b in face_box]
        face_roi = frame[y1:y2, x1:x2]
        
        if face_roi.size == 0:
            return False, 0.0
        
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Detect eyes in face region
        eyes = self.eye_cascade.detectMultiScale(
            gray_roi,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20, 20)
        )
        
        # Calculate openness based on number of detected eyes
        eye_count = len(eyes)
        openness_score = min(eye_count / 2.0, 1.0)
        
        self.ear_history.append(openness_score)
        
        # Detect blink: eyes not detected for consecutive frames then detected
        if len(self.ear_history) >= self.blink_consec_frames + 1:
            recent = list(self.ear_history)[-self.blink_consec_frames-1:]
            
            # Check for blink pattern: open -> closed -> open
            if recent[-1] > 0.5 and min(recent[:-1]) < 0.5:
                self.blink_total += 1
                return True, openness_score
        
        return False, openness_score
    
    def detect_head_movement(self, frame: np.ndarray, face_box: np.ndarray) -> Tuple[bool, float]:
        """
        Detect natural head micro-movements.
        
        Args:
            frame: BGR image
            face_box: [x1, y1, x2, y2] face bounding box
            
        Returns:
            Tuple of (movement_detected, movement_score)
        """
        # Store face center position
        x1, y1, x2, y2 = [int(b) for b in face_box]
        center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
        
        self.face_positions.append(center)
        
        if len(self.face_positions) < 5:
            return False, 0.0
        
        # Calculate movement variance over recent frames
        positions = np.array(list(self.face_positions))
        movement = np.std(positions, axis=0)
        movement_score = np.mean(movement)
        
        # Real faces have natural micro-movements
        movement_detected = movement_score > self.movement_threshold
        
        return movement_detected, movement_score
    
    def analyze_texture(self, frame: np.ndarray, face_box: np.ndarray) -> Tuple[bool, float]:
        """
        Analyze face texture using Laplacian variance.
        Photos/screens typically have less texture detail.
        
        Args:
            frame: BGR image
            face_box: [x1, y1, x2, y2] face bounding box
            
        Returns:
            Tuple of (real_texture, texture_score)
        """
        x1, y1, x2, y2 = [int(b) for b in face_box]
        face_roi = frame[y1:y2, x1:x2]
        
        if face_roi.size == 0:
            return False, 0.0
        
        # Convert to grayscale
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Resize for consistent analysis
        gray = cv2.resize(gray, (128, 128))
        
        # Calculate Laplacian variance (focus/texture measure)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_score = laplacian.var()
        
        # Real faces have higher texture variance
        real_texture = texture_score > self.texture_threshold
        
        return real_texture, texture_score
    
    def detect_screen_reflection(self, frame: np.ndarray, face_box: np.ndarray) -> Tuple[bool, float]:
        """
        Detect screen reflections/moiré patterns.
        
        Args:
            frame: BGR image
            face_box: [x1, y1, x2, y2] face bounding box
            
        Returns:
            Tuple of (no_reflection_detected, reflection_score)
        """
        x1, y1, x2, y2 = [int(b) for b in face_box]
        face_roi = frame[y1:y2, x1:x2]
        
        if face_roi.size == 0:
            return True, 0.0
        
        # Convert to grayscale
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Apply FFT to detect screen patterns
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)
        
        # Screens often have periodic patterns in high frequencies
        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2
        
        # Exclude center (low frequencies)
        mask = np.ones_like(magnitude)
        mask[center_h-10:center_h+10, center_w-10:center_w+10] = 0
        
        high_freq = magnitude * mask
        reflection_score = np.mean(high_freq)
        
        # Lower score = less likely to be screen
        no_reflection = reflection_score < 50
        
        return no_reflection, reflection_score
    
    def check_liveness(
        self, 
        frame: np.ndarray, 
        face_box: np.ndarray
    ) -> Tuple[bool, dict]:
        """
        Perform comprehensive liveness check.
        
        Args:
            frame: BGR image
            face_box: [x1, y1, x2, y2] face bounding box
            
        Returns:
            Tuple of (is_live, detailed_results)
        """
        results = {
            'is_live': False,
            'blink_detected': False,
            'movement_detected': False,
            'texture_real': False,
            'no_reflection': True,
            'blink_count': 0,
            'movement_score': 0.0,
            'texture_score': 0.0,
            'overall_score': 0.0,
            'message': ''
        }
        
        if face_box is None:
            results['message'] = 'No face detected'
            return False, results
        
        # Run all checks
        blink_detected, eye_openness = self.detect_blink_simple(frame, face_box)
        movement_detected, movement_score = self.detect_head_movement(frame, face_box)
        texture_real, texture_score = self.analyze_texture(frame, face_box)
        no_reflection, reflection_score = self.detect_screen_reflection(frame, face_box)
        
        # Update results
        results['blink_detected'] = blink_detected
        results['blink_count'] = self.blink_total
        results['movement_detected'] = movement_detected
        results['movement_score'] = movement_score
        results['texture_real'] = texture_real
        results['texture_score'] = texture_score
        results['no_reflection'] = no_reflection
        
        # Calculate overall liveness score
        checks_passed = 0
        total_checks = 3
        
        if texture_real:
            checks_passed += 1
        if movement_detected:
            checks_passed += 1
        if no_reflection:
            checks_passed += 1
        
        results['overall_score'] = checks_passed / total_checks
        
        # Conservative liveness decision
        # Require at least texture + one other check
        is_live = texture_real and (movement_detected or no_reflection)
        results['is_live'] = is_live
        
        if is_live:
            results['message'] = 'Liveness verified'
        else:
            missing = []
            if not texture_real:
                missing.append('texture')
            if not movement_detected:
                missing.append('movement')
            if not no_reflection:
                missing.append('screen detected')
            results['message'] = f"Failed checks: {', '.join(missing)}"
        
        return is_live, results
    
    def reset(self):
        """Reset liveness detector state for new session."""
        self.frame_history.clear()
        self.face_positions.clear()
        self.ear_history.clear()
        self.blink_counter = 0
        self.blink_total = 0
        self.session_start_time = None
        self.challenges_completed.clear()
    
    def start_session(self):
        """Start a new liveness check session."""
        self.reset()
        self.session_start_time = time.time()
    
    def get_session_duration(self) -> float:
        """Get current session duration in seconds."""
        if self.session_start_time is None:
            return 0.0
        return time.time() - self.session_start_time


class InteractiveLivenessChecker:
    """
    Interactive liveness checker with challenge-response.
    Asks user to perform specific actions.
    """
    
    CHALLENGES = [
        'blink',
        'turn_left',
        'turn_right',
        'nod'
    ]
    
    def __init__(self, required_challenges: int = 2):
        """
        Initialize interactive checker.
        
        Args:
            required_challenges: Number of challenges to complete
        """
        self.required_challenges = required_challenges
        self.completed_challenges = set()
        self.current_challenge = None
        self.challenge_start_time = None
        self.challenge_timeout = 5.0  # seconds
        
        self.liveness_detector = LivenessDetector()
        
    def get_next_challenge(self) -> Optional[str]:
        """Get the next challenge for the user."""
        import random
        available = [c for c in self.CHALLENGES if c not in self.completed_challenges]
        
        if not available:
            return None
        
        self.current_challenge = random.choice(available)
        self.challenge_start_time = time.time()
        return self.current_challenge
    
    def check_challenge_completion(
        self, 
        frame: np.ndarray, 
        face_box: np.ndarray,
        prev_frame: np.ndarray = None
    ) -> Tuple[bool, str]:
        """
        Check if the current challenge is completed.
        
        Returns:
            Tuple of (completed, message)
        """
        if self.current_challenge is None:
            return False, "No active challenge"
        
        # Check timeout
        if time.time() - self.challenge_start_time > self.challenge_timeout:
            return False, "Challenge timeout"
        
        completed = False
        message = ""
        
        if self.current_challenge == 'blink':
            blink_detected, _ = self.liveness_detector.detect_blink_simple(frame, face_box)
            if blink_detected:
                completed = True
                message = "Blink detected!"
            else:
                message = "Please blink"
                
        elif self.current_challenge in ['turn_left', 'turn_right', 'nod']:
            movement, score = self.liveness_detector.detect_head_movement(frame, face_box)
            if movement and score > 10:
                completed = True
                message = f"Movement detected!"
            else:
                message = f"Please {self.current_challenge.replace('_', ' ')}"
        
        if completed:
            self.completed_challenges.add(self.current_challenge)
            self.current_challenge = None
        
        return completed, message
    
    def is_verified(self) -> bool:
        """Check if enough challenges have been completed."""
        return len(self.completed_challenges) >= self.required_challenges
    
    def reset(self):
        """Reset for new verification session."""
        self.completed_challenges.clear()
        self.current_challenge = None
        self.challenge_start_time = None
        self.liveness_detector.reset()
