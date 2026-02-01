"""
Flask REST API for Face Authentication System.
Provides endpoints for user registration, authentication, and management.
"""

import os
import sys
import base64
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from io import BytesIO
from PIL import Image
import cv2

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from face_recognition_module import FaceRecognition
from liveness_detection import LivenessDetector

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize components
db = Database(os.path.join(os.path.dirname(__file__), 'face_auth.db'))
face_recognition = None  # Lazy initialization
liveness_detector = LivenessDetector()


def get_face_recognition():
    """Lazy initialization of face recognition model."""
    global face_recognition
    if face_recognition is None:
        print("Loading face recognition model...")
        face_recognition = FaceRecognition(similarity_threshold=0.7)
        print("Model loaded successfully!")
    return face_recognition


def decode_base64_image(image_data: str) -> np.ndarray:
    """
    Decode base64 image string to numpy array.
    
    Args:
        image_data: Base64 encoded image string
        
    Returns:
        BGR numpy array
    """
    # Remove data URL prefix if present
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    # Decode base64
    image_bytes = base64.b64decode(image_data)
    
    # Convert to PIL Image
    pil_image = Image.open(BytesIO(image_bytes))
    
    # Convert to numpy array (RGB)
    rgb_array = np.array(pil_image)
    
    # Convert RGB to BGR for OpenCV
    if len(rgb_array.shape) == 3 and rgb_array.shape[2] == 3:
        bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    else:
        bgr_array = rgb_array
    
    return bgr_array


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Face Authentication API is running',
        'users_registered': db.user_count()
    })


@app.route('/api/register', methods=['POST'])
def register_user():
    """
    Register a new user with facial embedding.
    
    Expected JSON body:
    {
        "username": "string",
        "image": "base64_encoded_image"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        image_data = data.get('image', '')
        
        if not username:
            return jsonify({'success': False, 'message': 'Username is required'}), 400
        
        if not image_data:
            return jsonify({'success': False, 'message': 'Image is required'}), 400
        
        # Check if username already exists
        existing_user = db.get_user_by_username(username)
        if existing_user:
            return jsonify({
                'success': False, 
                'message': f"Username '{username}' already exists"
            }), 409
        
        # Decode image
        try:
            image = decode_base64_image(image_data)
        except Exception as e:
            return jsonify({
                'success': False, 
                'message': f'Invalid image data: {str(e)}'
            }), 400
        
        # Get face recognition model
        fr = get_face_recognition()
        
        # Detect face and get bounding box
        face_tensor, face_box = fr.detect_face(image)
        
        if face_tensor is None:
            return jsonify({
                'success': False, 
                'message': 'No face detected in image. Please ensure your face is clearly visible.'
            }), 400
        
        # Check liveness
        if face_box is not None:
            is_live, liveness_results = liveness_detector.check_liveness(image, face_box)
            
            # For registration, we're more lenient with liveness
            # Just check texture to ensure it's not a printed photo
            if not liveness_results['texture_real']:
                return jsonify({
                    'success': False,
                    'message': 'Liveness check failed. Please use a real camera, not a photo.',
                    'liveness_details': liveness_results
                }), 400
        
        # Extract embedding
        embedding = fr.get_embedding_from_tensor(face_tensor)
        
        # Save to database
        success, message = db.add_user(username, embedding)
        
        if success:
            return jsonify({
                'success': True,
                'message': f"User '{username}' registered successfully",
                'user_id': db.get_user_by_username(username)['id']
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Registration failed: {str(e)}'
        }), 500


@app.route('/api/authenticate', methods=['POST'])
def authenticate_user():
    """
    Authenticate a user using facial recognition.
    
    Expected JSON body:
    {
        "image": "base64_encoded_image"
    }
    
    Optional:
    {
        "username": "string"  # For 1:1 verification instead of 1:N identification
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        image_data = data.get('image', '')
        target_username = data.get('username')  # Optional
        
        if not image_data:
            return jsonify({'success': False, 'message': 'Image is required'}), 400
        
        # Decode image
        try:
            image = decode_base64_image(image_data)
        except Exception as e:
            return jsonify({
                'success': False, 
                'message': f'Invalid image data: {str(e)}'
            }), 400
        
        # Get face recognition model
        fr = get_face_recognition()
        
        # Detect face
        face_tensor, face_box = fr.detect_face(image)
        
        if face_tensor is None:
            return jsonify({
                'success': False, 
                'message': 'No face detected. Please position your face in front of the camera.',
                'authenticated': False
            }), 400
        
        # Check liveness (strict for authentication)
        if face_box is not None:
            is_live, liveness_results = liveness_detector.check_liveness(image, face_box)
            
            if not is_live:
                return jsonify({
                    'success': False,
                    'message': f"Liveness check failed: {liveness_results['message']}",
                    'authenticated': False,
                    'liveness_details': liveness_results
                }), 401
        
        # Extract embedding
        query_embedding = fr.get_embedding_from_tensor(face_tensor)
        
        # 1:1 Verification (if username provided)
        if target_username:
            target_user = db.get_user_by_username(target_username)
            if not target_user:
                return jsonify({
                    'success': False,
                    'message': f"User '{target_username}' not found",
                    'authenticated': False
                }), 404
            
            is_match, similarity = fr.verify_face(query_embedding, target_user['embedding'])
            
            if is_match:
                return jsonify({
                    'success': True,
                    'message': f"User '{target_username}' verified successfully",
                    'authenticated': True,
                    'user': {
                        'id': target_user['id'],
                        'username': target_user['username'],
                        'similarity': float(similarity)
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Face does not match the registered user',
                    'authenticated': False,
                    'similarity': float(similarity)
                }), 401
        
        # 1:N Identification
        stored_embeddings = db.get_all_embeddings()
        
        if not stored_embeddings:
            return jsonify({
                'success': False,
                'message': 'No registered users found',
                'authenticated': False
            }), 404
        
        matched_user, similarity = fr.find_match(query_embedding, stored_embeddings)
        
        if matched_user:
            return jsonify({
                'success': True,
                'message': f"User '{matched_user['username']}' authenticated successfully",
                'authenticated': True,
                'user': {
                    'id': matched_user['id'],
                    'username': matched_user['username'],
                    'similarity': float(similarity)
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Face not recognized. User not registered.',
                'authenticated': False,
                'best_similarity': float(similarity) if similarity else 0.0
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Authentication failed: {str(e)}',
            'authenticated': False
        }), 500


@app.route('/api/users', methods=['GET'])
def list_users():
    """List all registered users (without embeddings)."""
    try:
        users = db.get_all_users()
        
        # Remove embeddings from response
        user_list = [
            {
                'id': user['id'],
                'username': user['username'],
                'created_at': user['created_at']
            }
            for user in users
        ]
        
        return jsonify({
            'success': True,
            'users': user_list,
            'count': len(user_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Failed to list users: {str(e)}'
        }), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    """Delete a user by ID."""
    try:
        success, message = db.delete_user(user_id)
        
        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'message': message}), 404
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Failed to delete user: {str(e)}'
        }), 500


@app.route('/api/users/username/<username>', methods=['DELETE'])
def delete_user_by_username(username: str):
    """Delete a user by username."""
    try:
        success, message = db.delete_user_by_username(username)
        
        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'message': message}), 404
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Failed to delete user: {str(e)}'
        }), 500


@app.route('/api/detect', methods=['POST'])
def detect_face():
    """
    Detect faces in an image without authentication.
    Useful for UI feedback.
    
    Expected JSON body:
    {
        "image": "base64_encoded_image"
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('image'):
            return jsonify({'success': False, 'message': 'Image is required'}), 400
        
        # Decode image
        image = decode_base64_image(data['image'])
        
        # Get face recognition model
        fr = get_face_recognition()
        
        # Detect face
        face_tensor, face_box = fr.detect_face(image)
        
        if face_tensor is not None:
            # Check liveness
            is_live, liveness_results = liveness_detector.check_liveness(image, face_box)
            
            return jsonify({
                'success': True,
                'face_detected': True,
                'bounding_box': face_box.tolist() if face_box is not None else None,
                'liveness': {
                    'is_live': is_live,
                    'details': liveness_results
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'face_detected': False,
                'bounding_box': None,
                'liveness': None
            }), 200
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Detection failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Face Authentication API Server")
    print("=" * 50)
    print(f"Registered users: {db.user_count()}")
    print("Starting server on http://localhost:5000")
    print("=" * 50)
    
    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=True)
