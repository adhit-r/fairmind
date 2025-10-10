#!/usr/bin/env python3
"""
Production startup script for FairMind backend.
Runs migrations and starts the server.
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path
import logging

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migrations():
    """Run database migrations."""
    logger.info("Running database migrations...")
    
    try:
        # Import and run migrations
        from scripts.migrate import run_migrations
        await run_migrations()
        logger.info("Migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if settings.is_production:
            sys.exit(1)
        else:
            logger.warning("Continuing without migrations in development mode")


def start_server():
    """Start the FastAPI server."""
    logger.info(f"Starting FairMind API server in {settings.environment} mode")
    
    if settings.is_production:
        # Use Gunicorn for production
        cmd = [
            "gunicorn",
            "api.main:app",
            "-w", "4",  # 4 worker processes
            "-k", "uvicorn.workers.UvicornWorker",
            "--bind", f"0.0.0.0:{settings.api_port}",
            "--timeout", "120",
            "--keep-alive", "5",
            "--max-requests", "1000",
            "--max-requests-jitter", "100",
            "--preload",
            "--access-logfile", "-",
            "--error-logfile", "-",
            "--log-level", settings.log_level.lower(),
        ]
    else:
        # Use Uvicorn for development
        cmd = [
            "uvicorn",
            "api.main:app",
            "--host", "0.0.0.0",
            "--port", str(settings.api_port),
            "--reload",
            "--log-level", settings.log_level.lower(),
        ]
    
    logger.info(f"Starting server with command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, cwd=backend_dir)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


async def main():
    """Main startup function."""
    logger.info("FairMind Backend Starting Up...")
    
    # Run migrations first
    await run_migrations()
    
    # Start the server
    start_server()


if __name__ == "__main__":
    asyncio.run(main())