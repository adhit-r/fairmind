"""
Startup script with database initialization
"""

import asyncio
import uvicorn
from database.connection import db_manager
from scripts.init_database import init_database

async def startup():
    """Application startup"""
    print("Starting FairMind Backend with Database...")
    
    # Initialize database
    if not init_database():
        print("Failed to initialize database. Exiting...")
        return False
    
    print("Database initialized successfully!")
    return True

def main():
    """Main function"""
    # Run startup
    success = asyncio.run(startup())
    
    if success:
        # Start the server
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    else:
        print("Failed to start application")

if __name__ == "__main__":
    main()


