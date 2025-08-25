#!/usr/bin/env python3
"""
Script to run geographic bias database migration
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_migration():
    """Run the geographic bias migration"""
    try:
        # Read the migration SQL
        migration_file = Path(__file__).parent.parent / "supabase" / "migrations" / "20241205_geographic_bias_tables.sql"
        
        if not migration_file.exists():
            print(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("Geographic bias migration SQL:")
        print("=" * 50)
        print(migration_sql)
        print("=" * 50)
        print("\nTo apply this migration:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the SQL above")
        print("4. Click 'Run' to execute the migration")
        print("\nOr use Supabase CLI:")
        print("supabase db push")
        
        return True
        
    except Exception as e:
        print(f"Error reading migration file: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 