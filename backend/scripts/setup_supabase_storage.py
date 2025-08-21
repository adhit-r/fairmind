#!/usr/bin/env python3
"""
Supabase Storage Setup Script for FairMind

This script sets up the necessary storage buckets and policies for AI model storage.
Run this script after setting up your Supabase project and environment variables.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from supabase_client import SupabaseService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseStorageSetup:
    def __init__(self):
        load_dotenv()
        self.supabase_service = SupabaseService()
        self.bucket_name = os.getenv("STORAGE_BUCKET", "ai-models")
        
    def check_connection(self) -> bool:
        """Check if Supabase is connected"""
        if not self.supabase_service.is_connected():
            logger.error("❌ Supabase not connected. Please check your environment variables:")
            logger.error("   - SUPABASE_URL")
            logger.error("   - SUPABASE_SERVICE_ROLE_KEY")
            return False
        logger.info("✅ Supabase connected successfully")
        return True
    
    async def create_storage_bucket(self) -> bool:
        """Create the AI models storage bucket"""
        try:
            logger.info(f"Creating storage bucket: {self.bucket_name}")
            
            # Create bucket using Supabase client
            result = self.supabase_service.client.storage.create_bucket(
                id=self.bucket_name,
                name=self.bucket_name,
                public=False,
                file_size_limit=52428800,  # 50MB limit
                allowed_mime_types=[
                    'application/octet-stream',
                    'application/json',
                    'text/plain',
                    'application/x-python-code'
                ]
            )
            
            logger.info(f"✅ Storage bucket '{self.bucket_name}' created successfully")
            return True
            
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"✅ Storage bucket '{self.bucket_name}' already exists")
                return True
            else:
                logger.error(f"❌ Failed to create storage bucket: {e}")
                return False
    
    async def setup_rls_policies(self) -> bool:
        """Set up Row Level Security policies for storage"""
        try:
            logger.info("Setting up RLS policies for storage...")
            
            # Enable RLS on storage.objects
            rls_query = """
            ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
            """
            
            # Create policy for organization-based access
            policy_query = """
            CREATE POLICY "Organization-based model access" ON storage.objects
            FOR ALL USING (
                bucket_id = 'ai-models' AND
                (storage.foldername(name))[1] = auth.jwt() ->> 'organization_id'
            );
            """
            
            # Execute the queries
            self.supabase_service.client.rpc('exec_sql', {'sql': rls_query}).execute()
            self.supabase_service.client.rpc('exec_sql', {'sql': policy_query}).execute()
            
            logger.info("✅ RLS policies set up successfully")
            return True
            
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("✅ RLS policies already exist")
                return True
            else:
                logger.error(f"❌ Failed to set up RLS policies: {e}")
                return False
    
    async def create_sample_organization_folders(self) -> bool:
        """Create sample organization folders in storage"""
        try:
            logger.info("Creating sample organization folders...")
            
            organizations = ['demo_org', 'admin_org', 'test_org']
            
            for org in organizations:
                # Create a sample file to establish the folder structure
                sample_content = f"# Sample folder for {org}\n# Created by FairMind setup script"
                
                # Upload sample file to establish folder
                file_path = f"{org}/README.md"
                self.supabase_service.client.storage.from_(self.bucket_name).upload(
                    path=file_path,
                    file=sample_content.encode(),
                    file_options={
                        "content-type": "text/markdown",
                        "upsert": True
                    }
                )
                
                logger.info(f"✅ Created folder structure for {org}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create sample folders: {e}")
            return False
    
    async def test_storage_access(self) -> bool:
        """Test storage access by uploading and downloading a test file"""
        try:
            logger.info("Testing storage access...")
            
            # Test file content
            test_content = "FairMind Storage Test - " + str(asyncio.get_event_loop().time())
            
            # Upload test file
            test_file_path = "test/test_storage.txt"
            self.supabase_service.client.storage.from_(self.bucket_name).upload(
                path=test_file_path,
                file=test_content.encode(),
                file_options={
                    "content-type": "text/plain",
                    "upsert": True
                }
            )
            
            # Download test file
            downloaded_content = self.supabase_service.client.storage.from_(self.bucket_name).download(test_file_path)
            
            if downloaded_content.decode() == test_content:
                logger.info("✅ Storage access test passed")
                
                # Clean up test file
                self.supabase_service.client.storage.from_(self.bucket_name).remove([test_file_path])
                logger.info("✅ Test file cleaned up")
                return True
            else:
                logger.error("❌ Storage access test failed - content mismatch")
                return False
                
        except Exception as e:
            logger.error(f"❌ Storage access test failed: {e}")
            return False
    
    async def migrate_existing_models(self) -> bool:
        """Migrate existing models from local storage to Supabase"""
        try:
            logger.info("Migrating existing models to Supabase...")
            
            local_storage_path = Path("storage/models")
            if not local_storage_path.exists():
                logger.info("No local models to migrate")
                return True
            
            migrated_count = 0
            
            for org_folder in local_storage_path.iterdir():
                if org_folder.is_dir():
                    org_name = org_folder.name
                    logger.info(f"Migrating models for organization: {org_name}")
                    
                    for model_file in org_folder.iterdir():
                        if model_file.is_file():
                            try:
                                # Read model file
                                with open(model_file, 'rb') as f:
                                    file_content = f.read()
                                
                                # Upload to Supabase
                                supabase_path = f"{org_name}/{model_file.name}"
                                self.supabase_service.client.storage.from_(self.bucket_name).upload(
                                    path=supabase_path,
                                    file=file_content,
                                    file_options={
                                        "content-type": "application/octet-stream",
                                        "upsert": True
                                    }
                                )
                                
                                migrated_count += 1
                                logger.info(f"  ✅ Migrated: {model_file.name}")
                                
                            except Exception as e:
                                logger.error(f"  ❌ Failed to migrate {model_file.name}: {e}")
            
            logger.info(f"✅ Migration completed. {migrated_count} models migrated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    async def run_setup(self):
        """Run the complete setup process"""
        logger.info("🚀 Starting Supabase Storage Setup for FairMind")
        logger.info("=" * 50)
        
        # Check connection
        if not self.check_connection():
            return False
        
        # Create storage bucket
        if not await self.create_storage_bucket():
            return False
        
        # Set up RLS policies
        if not await self.setup_rls_policies():
            return False
        
        # Create sample folders
        if not await self.create_sample_organization_folders():
            return False
        
        # Test storage access
        if not await self.test_storage_access():
            return False
        
        # Migrate existing models
        if not await self.migrate_existing_models():
            return False
        
        logger.info("=" * 50)
        logger.info("🎉 Supabase Storage Setup Completed Successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Update your .env file with the correct Supabase credentials")
        logger.info("2. Restart your backend server")
        logger.info("3. Test model upload/download functionality")
        logger.info("4. Monitor storage usage in your Supabase dashboard")
        
        return True

async def main():
    """Main function"""
    setup = SupabaseStorageSetup()
    success = await setup.run_setup()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
