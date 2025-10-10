#!/usr/bin/env python3
"""
Database migration script for FairMind backend.
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config.database import db_manager
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration(migration_file: Path):
    """Run a single migration file."""
    logger.info(f"Running migration: {migration_file.name}")
    
    try:
        # Read migration SQL
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        # Execute each statement
        for statement in statements:
            if statement:
                await db_manager.execute(statement)
        
        logger.info(f"Migration {migration_file.name} completed successfully")
        
    except Exception as e:
        logger.error(f"Migration {migration_file.name} failed: {e}")
        raise


async def run_migrations():
    """Run all pending migrations."""
    try:
        # Initialize database connection
        await db_manager.initialize()
        
        # Get migrations directory
        migrations_dir = backend_dir / "migrations"
        
        if not migrations_dir.exists():
            logger.warning("No migrations directory found")
            return
        
        # Get all migration files
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        if not migration_files:
            logger.info("No migration files found")
            return
        
        logger.info(f"Found {len(migration_files)} migration files")
        
        # Run each migration
        for migration_file in migration_files:
            await run_migration(migration_file)
        
        logger.info("All migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    
    finally:
        # Close database connection
        await db_manager.disconnect()


async def create_migration(name: str):
    """Create a new migration file."""
    migrations_dir = backend_dir / "migrations"
    migrations_dir.mkdir(exist_ok=True)
    
    # Get next migration number
    existing_migrations = list(migrations_dir.glob("*.sql"))
    next_number = len(existing_migrations) + 1
    
    # Create migration file
    migration_file = migrations_dir / f"{next_number:03d}_{name}.sql"
    
    template = f"""-- Migration: {name}
-- Created: {datetime.now().isoformat()}

-- Add your SQL statements here

"""
    
    with open(migration_file, 'w') as f:
        f.write(template)
    
    logger.info(f"Created migration file: {migration_file}")


if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument("command", choices=["migrate", "create"], help="Command to run")
    parser.add_argument("--name", help="Migration name (for create command)")
    
    args = parser.parse_args()
    
    if args.command == "migrate":
        asyncio.run(run_migrations())
    elif args.command == "create":
        if not args.name:
            logger.error("Migration name is required for create command")
            sys.exit(1)
        asyncio.run(create_migration(args.name))