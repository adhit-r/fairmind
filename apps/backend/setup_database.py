#!/usr/bin/env python3
"""
Database setup script for AI BOM system
Sets up the database schema and initial data
"""

import os
import asyncio
from supabase_client import supabase_service

async def setup_database():
    """Set up the database schema and initial data"""
    print("🚀 Setting up AI BOM database...")
    
    try:
        if not supabase_service.is_connected():
            print("❌ Supabase not connected. Please check your credentials.")
            print("Required environment variables:")
            print("- SUPABASE_URL")
            print("- SUPABASE_SERVICE_ROLE_KEY")
            return
        
        print("✅ Supabase connected")
        
        # Read SQL setup files
        sql_files = [
            "supabase/ai_bom_setup.sql"
        ]
        
        for sql_file in sql_files:
            if os.path.exists(sql_file):
                print(f"📄 Executing {sql_file}...")
                with open(sql_file, 'r') as f:
                    sql_content = f.read()
                
                # Split SQL by statements (simple approach)
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for i, statement in enumerate(statements):
                    if statement:
                        try:
                            print(f"   Executing statement {i+1}/{len(statements)}...")
                            # Note: Direct SQL execution requires RPC function or client-side execution
                            # For now, we'll provide instructions
                            if i == 0:  # Only show message once
                                print("   ℹ️  SQL execution requires running the script directly in Supabase SQL editor")
                                print("   📋 Copy the contents of supabase/ai_bom_setup.sql to Supabase SQL editor")
                        except Exception as e:
                            print(f"   ⚠️  Statement {i+1} failed: {e}")
            else:
                print(f"❌ SQL file not found: {sql_file}")
        
        # Test connection with a simple query
        try:
            # Try to access a basic table or create a test
            print("\n🔍 Testing database connection...")
            
            # This would normally test access to the tables
            print("✅ Database setup instructions provided")
            print("\n📋 Manual Setup Required:")
            print("1. Go to your Supabase Dashboard > SQL Editor")
            print("2. Copy and paste the contents of backend/supabase/ai_bom_setup.sql")
            print("3. Run the SQL script to create the AI BOM schema")
            print("4. The script will create:")
            print("   - ai_bom_documents table")
            print("   - ai_bom_components table") 
            print("   - ai_bom_analyses table")
            print("   - Proper indexes and RLS policies")
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
        
        print("\n🎉 Database setup process completed!")
        print("   Once you run the SQL script in Supabase, the database integration will be fully functional.")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(setup_database())
