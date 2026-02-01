"""
Face Recognition module using FaceNet (InceptionResnetV1).
Handles face detection, embedding extraction, and similarity matching.
"""

import numpy as np
from PIL import Image
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine
from typing import Optional, Tuple, List
import cv2


class FaceRecognition:
    """FaceNet-based face recognition with MTCNN detection."""
    
    def __init__(self, device: str = None, similarity_threshold: float = 0.7):
        """
        Initialize face recognition models.
        
        Args:
            device: 'cuda' or 'cpu', auto-detected if None
            similarity_threshold: Minimum cosine similarity for match (0-1)
        """
        # Auto-detect device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        self.similarity_threshold = similarity_threshold
        
        # Initialize MTCNN for face detection
        self.mtcnn = MTCNN(
            image_size=160,
            margin=20,
            min_face_size=40,
            thresholds=[0.6, 0.7, 0.7],
            factor=0.709,
            post_process=True,
            device=self.device,
            keep_all=False  # Only keep the largest face
        )
        
        # Initialize InceptionResnetV1 for embeddings
        # Using 'vggface2' pretrained weights for better accuracy
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        
        print(f"Face recognition initialized on {self.device}")
    
    def detect_face(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Detect face in image and return cropped face with bounding box.
        
        Args:
            image: BGR image from OpenCV (or RGB)
            
        Returns:
            Tuple of (face_tensor, bounding_box) or (None, None) if no face
        """
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_image)
        
        # Detect face and get bounding box
        try:
            face_tensor, prob = self.mtcnn(pil_image, return_prob=True)
            boxes, _ = self.mtcnn.detect(pil_image)
            
            if face_tensor is not None and prob > 0.9:
                return face_tensor, boxes[0] if boxes is not None else None
            return None, None
        except Exception as e:
            print(f"Face detection error: {e}")
            return None, None
    
    def get_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract 512-dimensional embedding from face in image.
        
        Args:
            image: BGR image from OpenCV
            
        Returns:
            512-dimensional numpy array or None if no face detected
        """
        face_tensor, _ = self.detect_face(image)
        
        if face_tensor is None:
            return None
        
        # Add batch dimension and move to device
        face_tensor = face_tensor.unsqueeze(0).to(self.device)
        
        # Get embedding
        with torch.no_grad():
            embedding = self.resnet(face_tensor)
        
        return embedding.cpu().numpy().flatten()
    
    def get_embedding_from_tensor(self, face_tensor: torch.Tensor) -> np.ndarray:
        """
        Get embedding from pre-detected face tensor.
        
        Args:
            face_tensor: Face tensor from MTCNN
            
        Returns:
            512-dimensional numpy array
        """
        if face_tensor.dim() == 3:
            face_tensor = face_tensor.unsqueeze(0)
        
        face_tensor = face_tensor.to(self.device)
        
        with torch.no_grad():
            embedding = self.resnet(face_tensor)
        
        return embedding.cpu().numpy().flatten()
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First 512-d embedding
            embedding2: Second 512-d embedding
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Cosine distance is 1 - cosine_similarity
        # So we return 1 - cosine_distance = cosine_similarity
        return 1 - cosine(embedding1, embedding2)
    
    def find_match(
        self, 
        query_embedding: np.ndarray, 
        stored_embeddings: List[Tuple[int, str, np.ndarray]]
    ) -> Tuple[Optional[dict], float]:
        """
        Find the best matching user for a query embedding.
        
        Args:
            query_embedding: 512-d embedding of the query face
            stored_embeddings: List of (user_id, username, embedding) tuples
            
        Returns:
            Tuple of (matched_user_dict, similarity_score) or (None, 0)
        """
        if not stored_embeddings:
            return None, 0.0
        
        best_match = None
        best_similarity = 0.0
        
        for user_id, username, stored_embedding in stored_embeddings:
            similarity = self.calculate_similarity(query_embedding, stored_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'id': user_id,
                    'username': username,
                    'similarity': similarity
                }
        
        # Only return match if above threshold
        if best_match and best_similarity >= self.similarity_threshold:
            return best_match, best_similarity
        
        return None, best_similarity
    
    def verify_face(
        self, 
        query_embedding: np.ndarray, 
        target_embedding: np.ndarray
    ) -> Tuple[bool, float]:
        """
        Verify if two face embeddings belong to the same person.
        
        Args:
            query_embedding: Query face embedding
            target_embedding: Target face embedding to compare against
            
        Returns:
            Tuple of (is_match, similarity_score)
        """
        similarity = self.calculate_similarity(query_embedding, target_embedding)
        return similarity >= self.similarity_threshold, similarity
    
    def detect_multiple_faces(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Detect all faces in an image and return their bounding boxes.
        
        Args:
            image: BGR image from OpenCV
            
        Returns:
            List of bounding boxes [x1, y1, x2, y2]
        """
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        # Detect all faces
        boxes, probs = self.mtcnn.detect(pil_image)
        
        if boxes is None:
            return []
        
        # Filter by probability
        valid_boxes = []
        for box, prob in zip(boxes, probs):
            if prob > 0.9:
                valid_boxes.append(box)
        
        return valid_boxes
    
    def draw_face_boxes(
        self, 
        image: np.ndarray, 
        boxes: List[np.ndarray], 
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw bounding boxes around detected faces.
        
        Args:
            image: BGR image from OpenCV
            boxes: List of bounding boxes
            color: BGR color for boxes
            thickness: Line thickness
            
        Returns:
            Image with drawn boxes
        """
        result = image.copy()
        
        for box in boxes:
            x1, y1, x2, y2 = [int(b) for b in box]
            cv2.rectangle(result, (x1, y1), (x2, y2), color, thickness)
        
        return result
