#!/usr/bin/env python3
"""
Create database tables from migration files
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import db_manager
from sqlalchemy import text

def create_tables():
    """Create tables from migration SQL file"""
    print("Creating database tables...")
    
    # Read migration file
    migration_file = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    # Test database connection
    if not db_manager.test_connection():
        print("ERROR: Database connection failed!")
        return False
    
    print("Database connection successful")
    
    # Execute SQL
    with db_manager.get_session() as session:
        try:
            # Split SQL by semicolons and execute each statement
            statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
            
            for statement in statements:
                if statement:
                    try:
                        session.execute(text(statement))
                    except Exception as e:
                        # Ignore "table already exists" errors
                        if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                            print(f"  Warning: {e}")
            
            session.commit()
            print("  ✓ Tables created successfully")
            return True
            
        except Exception as e:
            print(f"  ✗ Error creating tables: {e}")
            session.rollback()
            return False

if __name__ == "__main__":
    create_tables()

