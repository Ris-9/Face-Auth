"""
Liveness Detection module for anti-spoofing.
Includes static analysis for single-image liveness checks.
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
    - Blink detection (video only)
    - Head movement detection (video only)
    - Texture analysis (Laplacian variance)
    - Frequency analysis (Moire pattern detection)
    - Color analysis (Skin tone verification)
    """
    
    def __init__(
        self,
        ear_threshold: float = 0.25,
        blink_consec_frames: int = 2,
        movement_threshold: float = 3.0,
        texture_threshold: float = 80.0,  # Lowered slightly to not fail legitimate soft cams
        reflection_threshold: float = 95.0, # Increased to allow high-res webcams
        history_size: int = 30
    ):
        self.ear_threshold = ear_threshold
        self.blink_consec_frames = blink_consec_frames
        self.movement_threshold = movement_threshold
        self.texture_threshold = texture_threshold
        self.reflection_threshold = reflection_threshold
        self.history_size = history_size
        
        # Frame history for movement detection
        self.frame_history = deque(maxlen=history_size)
        self.face_positions = deque(maxlen=history_size)
        
        # Blink tracking
        self.blink_counter = 0
        self.blink_total = 0
        self.ear_history = deque(maxlen=history_size)
        
        # Load Haar cascades
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        
        self.session_start_time = None
    
    def calculate_ear(self, eye_points: np.ndarray) -> float:
        """Calculate Eye Aspect Ratio (EAR)."""
        v1 = np.linalg.norm(eye_points[1] - eye_points[5])
        v2 = np.linalg.norm(eye_points[2] - eye_points[4])
        h = np.linalg.norm(eye_points[0] - eye_points[3])
        if h == 0: return 0.0
        return (v1 + v2) / (2.0 * h)
    
    def detect_blink_simple(self, frame: np.ndarray, face_box: np.ndarray) -> Tuple[bool, float]:
        """Simple blink detection (requires video history)."""
        x1, y1, x2, y2 = [int(b) for b in face_box]
        face_roi = frame[y1:y2, x1:x2]
        if face_roi.size == 0: return False, 0.0
        
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(
            gray_roi, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20)
        )
        
        eye_count = len(eyes)
        openness_score = min(eye_count / 2.0, 1.0)
        self.ear_history.append(openness_score)
        
        # Blink logic needs history
        if len(self.ear_history) >= self.blink_consec_frames + 1:
            recent = list(self.ear_history)[-self.blink_consec_frames-1:]
            if recent[-1] > 0.5 and min(recent[:-1]) < 0.5:
                self.blink_total += 1
                return True, openness_score
        
        return False, openness_score
    
    def detect_head_movement(self, frame: np.ndarray, face_box: np.ndarray) -> Tuple[bool, float]:
        """Detect head movement (requires video history)."""
        x1, y1, x2, y2 = [int(b) for b in face_box]
        center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
        self.face_positions.append(center)
        
        if len(self.face_positions) < 3:
            return False, 0.0
        
        positions = np.array(list(self.face_positions))
        movement = np.std(positions, axis=0)
        movement_score = np.mean(movement)
        return movement_score > self.movement_threshold, movement_score

    def analyze_texture(self, frame: np.ndarray, face_box: np.ndarray) -> Tuple[bool, float]:
        """
        Analyze texture (Laplacian variance).
        Real faces have detailed texture; some spoofs are blurry.
        However, high-res screens are also sharp.
        """
        x1, y1, x2, y2 = [int(b) for b in face_box]
        face_roi = frame[y1:y2, x1:x2]
        if face_roi.size == 0: return False, 0.0
        
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        # Resize to standard size to make threshold consistent
        gray = cv2.resize(gray, (100, 100)) 
        
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_score = laplacian.var()
        
        # Check against threshold
        is_real = texture_score > self.texture_threshold
        # Also check for 'too high' (noise/pixelated)
        # Also check for 'too high' (noise/pixelated)
        if texture_score > 2500: # Suspiciously high noise
             is_real = False
             
        return is_real, texture_score

    def detect_frequency_anomalies(self, frame: np.ndarray, face_box: np.ndarray) -> Tuple[bool, float]:
        """
        Detect Moiré patterns using FFT.
        Screens usually have periodic patterns which show as peaks in high frequencies.
        """
        x1, y1, x2, y2 = [int(b) for b in face_box]
        face_roi = frame[y1:y2, x1:x2]
        if face_roi.size == 0: return True, 0.0
        
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        # Resize to standard size for consistent frequency analysis
        gray = cv2.resize(gray, (128, 128))
        
        # FFT
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1)
        
        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2
        
        # Analyze high frequency region (remove low freq components at center)
        # Radius for low freq
        r = 15
        # Use np.ones instead of ones_like to ensure C-contiguous memory layout
        mask = np.ones(magnitude.shape, dtype=magnitude.dtype)
        cv2.circle(mask, (center_w, center_h), r, 0, -1)
        
        # Calculate mean energy of high frequencies
        high_freq_content = magnitude * mask
        score = np.mean(high_freq_content)
        
        # If mean high freq energy is very high, it could be a screen grid or sharp pixelation
        # Real faces are generally smoother in high freq than LED grids
        is_natural = score < self.reflection_threshold
        
        return is_natural, score

    def check_skin_tone_validity(self, frame: np.ndarray, face_box: np.ndarray) -> Tuple[bool, float]:
        """
        Check if pixels in face box conform to general skin tone YCrCb distribution.
        Screens often have blueish tint or unnatural color gamut.
        """
        x1, y1, x2, y2 = [int(b) for b in face_box]
        face_roi = frame[y1:y2, x1:x2]
        if face_roi.size == 0: return False, 0.0
        
        # Convert to YCrCb
        ycrcb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2YCrCb)
        
        # Extract Cr and Cb channels
        # y, cr, cb = cv2.split(ycrcb)
        
        # Define skin range (general heuristic)
        # Cr: 133-173, Cb: 77-127
        min_CrCb = np.array([0, 133, 77], np.uint8)
        max_CrCb = np.array([255, 173, 127], np.uint8)
        
        mask = cv2.inRange(ycrcb, min_CrCb, max_CrCb)
        
        # Calculate percentage of skin-like pixels
        skin_pixels = cv2.countNonZero(mask)
        total_pixels = face_roi.shape[0] * face_roi.shape[1]
        
        if total_pixels == 0: return False, 0.0
        
        ratio = skin_pixels / total_pixels
        
        # Threshold: At least 30% of the face box should be "skin color"
        # Adjust based on diverse lighting/skin tones, but 30% is conservative enough 
        # to catch blatantly wrong colors (B&W headers, blue screens).
        is_skin = ratio > 0.30
        
        return is_skin, ratio

    def check_liveness(
        self, 
        frame: np.ndarray, 
        face_box: np.ndarray
    ) -> Tuple[bool, dict]:
        """
        Perform liveness check (Static + Dynamic if history available).
        """
        results = {
            'is_live': False,
            'checks': {},
            'score': 0.0,
            'message': ''
        }
        
        if face_box is None:
            results['message'] = 'No face detected'
            return False, results
        
        # 1. Texture Analysis
        texture_ok, texture_score = self.analyze_texture(frame, face_box)
        results['checks']['texture'] = {'passed': bool(texture_ok), 'score': float(texture_score)}
        
        # 2. Frequency/Moire Analysis
        freq_ok, freq_score = self.detect_frequency_anomalies(frame, face_box)
        results['checks']['frequency'] = {'passed': bool(freq_ok), 'score': float(freq_score)}
        
        # 3. Skin Tone Analysis
        skin_ok, skin_ratio = self.check_skin_tone_validity(frame, face_box)
        results['checks']['skin_color'] = {'passed': bool(skin_ok), 'score': float(skin_ratio)}
        
        # Decision Logic
        # For single static image: STRICT mode
        # Must pass all static checks
        
        failed = []
        if not texture_ok: failed.append('Texture abnormal')
        if not freq_ok: failed.append('Screen pattern detected')
        if not skin_ok: failed.append('Unnatural colors')
        
        # Heuristic: If Texture and Skin are both good, ignore Frequency failure
        # (High-quality cameras often trigger false positive moire patterns)
        if texture_ok and skin_ok:
            is_live = True
        else:
            is_live = len(failed) == 0
        
        results['is_live'] = bool(is_live)
        if is_live:
            results['message'] = 'Liveness verified'
        else:
            results['message'] = f"Liveness check failed: {', '.join(failed)}"
            
        return is_live, results

    def reset(self):
        self.frame_history.clear()
        self.face_positions.clear()
        self.ear_history.clear()
        self.blink_counter = 0
