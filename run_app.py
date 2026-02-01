"""
Launch script for the desktop application.
Make sure the backend server is running first.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop_app.main import main


if __name__ == '__main__':
    print("=" * 60)
    print("  Face Authentication Desktop App")
    print("=" * 60)
    print()
    print("  Make sure the backend server is running!")
    print("  Run: python run_backend.py")
    print()
    print("=" * 60)
    
    main()
