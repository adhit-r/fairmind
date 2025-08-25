#!/usr/bin/env python3
"""
Test Supabase storage functionality
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Supabase Storage Test ===")
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
            
            # Test storage functionality
            bucket_name = "ai-models"
            
            # List existing buckets
            print("\n--- Testing Storage Buckets ---")
            try:
                buckets = client.storage.list_buckets()
                print(f"✅ Found {len(buckets)} storage buckets")
                for bucket in buckets:
                    print(f"  - {bucket.name} (public: {bucket.public})")
            except Exception as e:
                print(f"❌ Failed to list buckets: {e}")
            
            # Check if ai-models bucket exists
            bucket_exists = False
            try:
                for bucket in buckets:
                    if bucket.name == bucket_name:
                        bucket_exists = True
                        print(f"✅ Storage bucket '{bucket_name}' exists")
                        break
                
                if not bucket_exists:
                    print(f"❌ Storage bucket '{bucket_name}' does not exist")
                    print("Creating bucket...")
                    
                    # Create the bucket
                    result = client.storage.create_bucket(
                        id=bucket_name,
                        name=bucket_name,
                        public=False,
                        file_size_limit=52428800,  # 50MB limit
                        allowed_mime_types=[
                            'application/octet-stream',
                            'application/json',
                            'text/plain',
                            'application/x-python-code'
                        ]
                    )
                    print(f"✅ Storage bucket '{bucket_name}' created successfully")
                    
            except Exception as e:
                print(f"❌ Failed to create bucket: {e}")
            
            # Test file upload
            print("\n--- Testing File Upload ---")
            try:
                test_content = "FairMind Storage Test - " + str(os.getpid())
                test_file_path = "test/test_storage.txt"
                
                # Upload test file
                result = client.storage.from_(bucket_name).upload(
                    path=test_file_path,
                    file=test_content.encode(),
                    file_options={
                        "content-type": "text/plain",
                        "upsert": True
                    }
                )
                print(f"✅ Test file uploaded successfully")
                
                # Download test file
                downloaded_content = client.storage.from_(bucket_name).download(test_file_path)
                if downloaded_content.decode() == test_content:
                    print("✅ Test file download successful - content matches")
                else:
                    print("❌ Test file download failed - content mismatch")
                
                # Clean up test file
                client.storage.from_(bucket_name).remove([test_file_path])
                print("✅ Test file cleaned up")
                
            except Exception as e:
                print(f"❌ Failed to test file upload/download: {e}")
            
            print("\n✅ Supabase storage test completed successfully!")
            
        except Exception as e:
            print(f"❌ Failed to create Supabase client: {e}")
            
except ImportError as e:
    print(f"❌ Failed to import Supabase: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
