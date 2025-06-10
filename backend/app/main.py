"""Main entry point for the Pileup Buster API."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from app import create_app

def main():
    """Start the FastAPI server."""
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=5000)

def dev():
    """Start the FastAPI server in development mode with auto-reload."""
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)

if __name__ == "__main__":
    main()
