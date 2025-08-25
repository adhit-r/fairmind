"""
Database initialization script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db_manager
from database.models import Base

def init_database():
    """Initialize the database"""
    print("Initializing database...")
    
    # Test connection
    if not db_manager.test_connection():
        print("ERROR: Database connection failed!")
        return False
    
    # Create tables
    try:
        db_manager.create_tables()
        print("Database tables created successfully!")
        return True
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    init_database()


