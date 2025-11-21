#!/usr/bin/env python3
"""
Check both SQLite and Supabase databases to see what data exists
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import db_manager
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
import json

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_current_db():
    """Check what database is currently connected"""
    print_section("Current Database Connection")
    
    db_url = os.getenv("DATABASE_URL", "")
    
    if db_url.startswith("postgresql"):
        print("✅ Connected to: PostgreSQL (Supabase)")
        print(f"   Connection: {db_url[:50]}...")
        return "postgresql"
    else:
        print("⚠️  Connected to: SQLite (Local)")
        print("   To connect to Supabase, set DATABASE_URL to PostgreSQL connection string")
        return "sqlite"

def check_tables(db_type: str):
    """Check tables in the current database"""
    print_section("Tables in Current Database")
    
    try:
        with db_manager.get_session() as session:
            if db_type == "postgresql":
                query = text("""
                    SELECT table_name, 
                           (SELECT COUNT(*) FROM information_schema.columns 
                            WHERE table_name = t.table_name) as column_count
                    FROM information_schema.tables t
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            else:
                query = text("""
                    SELECT name as table_name,
                           (SELECT COUNT(*) FROM pragma_table_info(name)) as column_count
                    FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
            
            result = session.execute(query)
            tables = result.fetchall()
            
            if tables:
                print(f"Found {len(tables)} table(s):\n")
                for table in tables:
                    table_name = table[0]
                    column_count = table[1] if len(table) > 1 else "?"
                    
                    # Get row count
                    try:
                        count_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
                        count_result = session.execute(count_query)
                        row_count = count_result.fetchone()[0]
                        status = "✅" if row_count > 0 else "⚠️"
                        print(f"  {status} {table_name}: {row_count} rows, {column_count} columns")
                    except Exception as e:
                        print(f"  ⚠️  {table_name}: Error getting count - {e}")
            else:
                print("No tables found")
                
    except Exception as e:
        print(f"Error checking tables: {e}")

def check_models():
    """Check models table specifically"""
    print_section("Models Table")
    
    try:
        with db_manager.get_session() as session:
            query = text("SELECT COUNT(*) as count FROM models")
            result = session.execute(query)
            count = result.fetchone()[0]
            
            print(f"Total models: {count}")
            
            if count > 0:
                # Get sample models
                sample_query = text("SELECT id, name, model_type, status FROM models LIMIT 5")
                sample_result = session.execute(sample_query)
                samples = sample_result.fetchall()
                
                print("\nSample models:")
                for model in samples:
                    print(f"  - {model[0]}: {model[1]} ({model[2]}) - {model[3]}")
                    
    except Exception as e:
        print(f"Error checking models: {e}")

def check_datasets():
    """Check datasets table"""
    print_section("Datasets Table")
    
    try:
        with db_manager.get_session() as session:
            # Check if table exists
            db_url = os.getenv("DATABASE_URL", "")
            if db_url.startswith("postgresql"):
                check_query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'datasets'
                    )
                """)
            else:
                check_query = text("""
                    SELECT EXISTS (
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='datasets'
                    )
                """)
            
            exists_result = session.execute(check_query)
            exists = exists_result.fetchone()[0]
            
            if exists:
                count_query = text("SELECT COUNT(*) as count FROM datasets")
                count_result = session.execute(count_query)
                count = count_result.fetchone()[0]
                print(f"Total datasets: {count}")
                
                if count > 0:
                    sample_query = text("SELECT id, name, file_type FROM datasets LIMIT 5")
                    sample_result = session.execute(sample_query)
                    samples = sample_result.fetchall()
                    
                    print("\nSample datasets:")
                    for dataset in samples:
                        print(f"  - {dataset[0]}: {dataset[1]} ({dataset[2]})")
            else:
                print("⚠️  Datasets table does not exist")
                
    except Exception as e:
        print(f"Error checking datasets: {e}")

def main():
    print_section("Database Check - All Sources")
    
    # Check what database we're connected to
    db_type = check_current_db()
    
    # Check tables
    check_tables(db_type)
    
    # Check specific important tables
    check_models()
    check_datasets()
    
    # Summary
    print_section("Summary")
    print("Current database connection is being used by the backend API.")
    print("\nIf Supabase has more data, you may need to:")
    print("  1. Set DATABASE_URL to your Supabase PostgreSQL connection string")
    print("  2. Restart the backend server")
    print("  3. The backend will then use Supabase instead of SQLite")

if __name__ == "__main__":
    main()

