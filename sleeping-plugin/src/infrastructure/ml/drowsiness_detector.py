"""
MediaPipe Drowsiness Detector
Serviço de detecção de sonolência usando MediaPipe
"""
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from typing import Optional

class DrowsinessDetector:
    def __init__(self, model_path: str, ear_threshold: float, consec_frames: int):
        self.ear_threshold = ear_threshold
        self.consec_frames = consec_frames
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
        self.detector = vision.FaceLandmarker.create_from_options(options)
        
        self.left_eye = [362, 385, 387, 263, 373, 380]
        self.right_eye = [33, 160, 158, 133, 153, 144]
    
    def euclidean_distance(self, p1, p2) -> float:
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    
    def calculate_ear(self, eye_landmarks, landmarks) -> float:
        p1, p2, p3, p4, p5, p6 = [landmarks[i] for i in eye_landmarks]
        vertical1 = self.euclidean_distance(p2, p6)
        vertical2 = self.euclidean_distance(p3, p5)
        horizontal = self.euclidean_distance(p1, p4)
        return (vertical1 + vertical2) / (2.0 * horizontal)
    
    def detect(self, frame) -> Optional[float]:
        """
        Detecta EAR em um frame
        Returns: EAR value ou None se não detectar rosto
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self.detector.detect(mp_image)
        
        if results.face_landmarks:
            face_landmarks = results.face_landmarks[0]
            right_ear = self.calculate_ear(self.right_eye, face_landmarks)
            left_ear = self.calculate_ear(self.left_eye, face_landmarks)
            return (right_ear + left_ear) / 2.0
        
        return None
    
    def is_drowsy(self, ear_value: float) -> bool:
        """Verifica se EAR indica sonolência"""
        return ear_value < self.ear_threshold
