"""
SQLite Database Manager - Entry point
"""
import sys
import os

# Add parent directory to path for importing blacksheep
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from sqlite_manager.app import app


def main():
    """Run the SQLite Database Manager application."""
    print("=" * 60)
    print("SQLite Database Manager")
    print("=" * 60)
    print("Starting server at http://127.0.0.1:8888")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        "sqlite_manager.app:app",
        host="127.0.0.1",
        port=8888,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
