#!/usr/bin/env python3
"""
Script to check what data exists in Supabase database
Uses SQLAlchemy to query the database directly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import db_manager
from sqlalchemy import text
import json
from typing import Dict, Any, List

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_table(table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Check a table in database"""
    try:
        with db_manager.get_session() as session:
            # Try to get table info first
            query = text(f"""
                SELECT * FROM {table_name} 
                LIMIT :limit
            """)
            result = session.execute(query, {"limit": limit})
            rows = result.fetchall()
            
            # Convert to list of dicts
            if rows:
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
            return []
    except Exception as e:
        print(f"⚠️  Error querying {table_name}: {e}")
        return []

def get_table_count(table_name: str) -> int:
    """Get count of records in a table"""
    try:
        with db_manager.get_session() as session:
            query = text(f"SELECT COUNT(*) as count FROM {table_name}")
            result = session.execute(query)
            row = result.fetchone()
            return row[0] if row else 0
    except Exception as e:
        return 0

def list_all_tables() -> List[str]:
    """List all tables in the database"""
    try:
        with db_manager.get_session() as session:
            # Check if PostgreSQL or SQLite
            db_url = os.getenv("DATABASE_URL", "")
            if db_url.startswith("postgresql"):
                # PostgreSQL/Supabase
                query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            else:
                # SQLite
                query = text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            
            result = session.execute(query)
            return [row[0] for row in result.fetchall()]
    except Exception as e:
        print(f"⚠️  Could not list tables: {e}")
        return []

def main():
    print_section("Database Check")
    
    # Test connection
    if not db_manager.test_connection():
        print("❌ Database connection failed")
        print("\nPlease check:")
        print("  - DATABASE_URL environment variable")
        print("  - Database credentials")
        return
    
    print("✅ Database connection successful")
    
    # Check database type
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgresql"):
        print("📊 Database Type: PostgreSQL (Supabase)")
        db_type = "postgresql"
    else:
        print("📊 Database Type: SQLite (Local)")
        db_type = "sqlite"
        print("\n⚠️  Currently using SQLite. To check Supabase, set DATABASE_URL to:")
        print("   postgresql://user:password@host:port/database")
    
    # List all tables
    print_section("Available Tables")
    all_tables = list_all_tables()
    
    if all_tables:
        print(f"Found {len(all_tables)} table(s):")
        for table in all_tables:
            count = get_table_count(table)
            status = "✅" if count > 0 else "⚠️"
            print(f"  {status} {table}: {count} record(s)")
    else:
        print("⚠️  No tables found or unable to list tables")
    
    # Check specific tables
    tables_to_check = [
        "models",
        "ml_models", 
        "datasets",
        "bias_analyses",
        "audit_logs",
        "profiles",
        "ai_bom_documents",
        "ai_bom_components",
        "compliance_frameworks",
        "policies",
        "risks",
        "evidence",
        "reports",
    ]
    
    # Filter to only check tables that exist
    existing_tables = [t for t in tables_to_check if t in all_tables] if all_tables else tables_to_check
    
    results = {}
    
    for table in existing_tables:
        print_section(f"Table: {table}")
        data = check_table(table, limit=3)
        results[table] = data
        
        count = get_table_count(table)
        
        if count > 0:
            print(f"✅ Found {count} total record(s)")
            if data:
                print("\nSample record:")
                # Convert datetime and other non-serializable types
                sample = {}
                for k, v in data[0].items():
                    if hasattr(v, 'isoformat'):
                        sample[k] = v.isoformat()
                    elif isinstance(v, (dict, list)):
                        sample[k] = v
                    else:
                        sample[k] = str(v) if v is not None else None
                print(json.dumps(sample, indent=2, default=str))
        else:
            print("⚠️  No data found")
    
    # Summary
    print_section("Summary")
    total_records = sum(get_table_count(t) for t in existing_tables)
    tables_with_data = [table for table in existing_tables if get_table_count(table) > 0]
    
    print(f"Total records across checked tables: {total_records}")
    print(f"Tables with data: {len(tables_with_data)}/{len(existing_tables)}")
    
    if tables_with_data:
        print("\nTables with data:")
        for table in tables_with_data:
            count = get_table_count(table)
            print(f"  ✅ {table}: {count} record(s)")
    
    if db_type == "sqlite":
        print("\n" + "=" * 60)
        print("  To check Supabase, set DATABASE_URL environment variable:")
        print("  export DATABASE_URL='postgresql://user:pass@host:port/db'")
        print("=" * 60)

if __name__ == "__main__":
    main()
