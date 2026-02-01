"""
Launch script for the backend API server.
Run this first before starting the desktop application.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app


if __name__ == '__main__':
    print("=" * 60)
    print("  Face Authentication API Server")
    print("=" * 60)
    print()
    print("  Starting server on http://localhost:5000")
    print("  Press Ctrl+C to stop the server")
    print()
    print("=" * 60)
    
    # Run the Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)
