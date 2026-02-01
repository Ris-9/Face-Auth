"""
Database module for Face Authentication System.
Handles user storage with facial embeddings using SQLite.
"""

import sqlite3
import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple


class Database:
    """SQLite database handler for face authentication system."""
    
    def __init__(self, db_path: str = "face_auth.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = Path(db_path)
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Create database and tables if they don't exist."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index on username for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_username ON users(username)
        ''')
        
        self.conn.commit()
    
    def _serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """Convert numpy array to bytes for storage."""
        return embedding.tobytes()
    
    def _deserialize_embedding(self, data: bytes) -> np.ndarray:
        """Convert bytes back to numpy array."""
        return np.frombuffer(data, dtype=np.float32)
    
    def add_user(self, username: str, embedding: np.ndarray) -> Tuple[bool, str]:
        """
        Add a new user with their facial embedding.
        
        Args:
            username: Unique username for the user
            embedding: 512-dimensional facial embedding vector
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            cursor = self.conn.cursor()
            embedding_bytes = self._serialize_embedding(embedding.astype(np.float32))
            
            cursor.execute(
                'INSERT INTO users (username, embedding) VALUES (?, ?)',
                (username, embedding_bytes)
            )
            self.conn.commit()
            return True, f"User '{username}' registered successfully"
            
        except sqlite3.IntegrityError:
            return False, f"Username '{username}' already exists"
        except Exception as e:
            return False, f"Error registering user: {str(e)}"
    
    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user data by username."""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, username, embedding, created_at FROM users WHERE username = ?',
            (username,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'embedding': self._deserialize_embedding(row[2]),
                'created_at': row[3]
            }
        return None
    
    def get_all_users(self) -> List[dict]:
        """Get all users with their embeddings."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, username, embedding, created_at FROM users')
        rows = cursor.fetchall()
        
        users = []
        for row in rows:
            users.append({
                'id': row[0],
                'username': row[1],
                'embedding': self._deserialize_embedding(row[2]),
                'created_at': row[3]
            })
        return users
    
    def get_all_embeddings(self) -> List[Tuple[int, str, np.ndarray]]:
        """Get all user IDs, usernames and embeddings for matching."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, username, embedding FROM users')
        rows = cursor.fetchall()
        
        return [
            (row[0], row[1], self._deserialize_embedding(row[2]))
            for row in rows
        ]
    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Delete a user by ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            if cursor.rowcount > 0:
                self.conn.commit()
                return True, "User deleted successfully"
            else:
                return False, "User not found"
                
        except Exception as e:
            return False, f"Error deleting user: {str(e)}"
    
    def delete_user_by_username(self, username: str) -> Tuple[bool, str]:
        """Delete a user by username."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            
            if cursor.rowcount > 0:
                self.conn.commit()
                return True, f"User '{username}' deleted successfully"
            else:
                return False, f"User '{username}' not found"
                
        except Exception as e:
            return False, f"Error deleting user: {str(e)}"
    
    def update_embedding(self, username: str, embedding: np.ndarray) -> Tuple[bool, str]:
        """Update a user's facial embedding."""
        try:
            cursor = self.conn.cursor()
            embedding_bytes = self._serialize_embedding(embedding.astype(np.float32))
            
            cursor.execute(
                '''UPDATE users 
                   SET embedding = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE username = ?''',
                (embedding_bytes, username)
            )
            
            if cursor.rowcount > 0:
                self.conn.commit()
                return True, f"Embedding updated for '{username}'"
            else:
                return False, f"User '{username}' not found"
                
        except Exception as e:
            return False, f"Error updating embedding: {str(e)}"
    
    def user_count(self) -> int:
        """Get total number of registered users."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
