#!/usr/bin/env python3
"""
Script to check Supabase data using the Supabase client
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase_client import supabase_service
import json
from typing import Dict, Any, List

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_table_via_client(table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Check a table using Supabase client"""
    try:
        if not supabase_service.is_connected():
            return []
        
        response = supabase_service.client.table(table_name).select("*").limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"⚠️  Error querying {table_name}: {e}")
        return []

def get_table_count_via_client(table_name: str) -> int:
    """Get count of records using Supabase client"""
    try:
        if not supabase_service.is_connected():
            return 0
        
        response = supabase_service.client.table(table_name).select("id", count="exact").limit(1).execute()
        return response.count if hasattr(response, 'count') else 0
    except Exception as e:
        return 0

def main():
    print_section("Supabase Client Check")
    
    # Check connection
    if not supabase_service.is_connected():
        print("❌ Supabase client is not connected")
        print("\nPlease check environment variables:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_ROLE_KEY")
        return
    
    print("✅ Supabase client connected")
    print(f"   URL: {supabase_service.url}")
    
    # List of tables to check
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
    
    results = {}
    
    for table in tables_to_check:
        print_section(f"Table: {table}")
        try:
            data = check_table_via_client(table, limit=3)
            count = get_table_count_via_client(table)
            results[table] = data
            
            if count > 0 or data:
                print(f"✅ Found {count if count > 0 else len(data)} record(s)")
                if data:
                    print("\nSample record:")
                    print(json.dumps(data[0], indent=2, default=str))
            else:
                print("⚠️  No data found or table doesn't exist")
        except Exception as e:
            print(f"⚠️  Error: {e}")
            results[table] = []
    
    # Summary
    print_section("Summary")
    tables_with_data = [table for table, data in results.items() if data]
    
    print(f"Tables with data: {len(tables_with_data)}/{len(tables_to_check)}")
    
    if tables_with_data:
        print("\nTables with data:")
        for table in tables_with_data:
            count = get_table_count_via_client(table)
            print(f"  ✅ {table}: {count if count > 0 else len(results[table])} record(s)")

if __name__ == "__main__":
    main()

