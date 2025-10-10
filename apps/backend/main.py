#!/usr/bin/env python3
"""
FairMind Backend - Main Entry Point

This is the main entry point for the FairMind backend application.
It properly handles the import structure and can be run directly.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Now we can import the FastAPI app
from api.main import app

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8001
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting FairMind Backend on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )