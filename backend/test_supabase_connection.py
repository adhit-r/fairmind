#!/usr/bin/env python3
"""
Test Supabase connection and debug issues
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Supabase Connection Test ===")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_SERVICE_ROLE_KEY: {os.getenv('SUPABASE_SERVICE_ROLE_KEY')[:20] + '...' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'None'}")

try:
    from supabase import create_client, Client
    print("✅ Supabase package imported successfully")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
    else:
        print("✅ Supabase credentials found")
        
        try:
            client = create_client(supabase_url, supabase_key)
            print("✅ Supabase client created successfully")
            
            # Test a simple query
            result = client.table("geographic_bias_analyses").select("id", count="exact").execute()
            print(f"✅ Database query successful: {result.count} records found")
            
        except Exception as e:
            print(f"❌ Failed to create Supabase client: {e}")
            
except ImportError as e:
    print(f"❌ Failed to import Supabase: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
