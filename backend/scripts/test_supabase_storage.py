#!/usr/bin/env python3
"""
Test Supabase Storage Functionality

This script tests the Supabase storage functionality for FairMind.
Run this to verify that storage is working correctly.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import hashlib

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from services.model_storage_service import model_storage_service
from supabase_client import SupabaseService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseStorageTester:
    def __init__(self):
        load_dotenv()
        self.supabase_service = SupabaseService()
        self.test_org_id = "test_org"
        
    def check_connection(self) -> bool:
        """Check if Supabase is connected"""
        logger.info("Testing Supabase connection...")
        
        if not self.supabase_service.is_connected():
            logger.error("❌ Supabase not connected")
            return False
        
        logger.info("✅ Supabase connected successfully")
        return True
    
    def check_storage_service(self) -> bool:
        """Check if storage service is available"""
        logger.info("Testing storage service...")
        
        if not model_storage_service.is_supabase_available():
            logger.error("❌ Storage service not available")
            return False
        
        storage_info = model_storage_service.get_storage_info()
        logger.info(f"✅ Storage service available: {storage_info}")
        return True
    
    async def test_bucket_access(self) -> bool:
        """Test bucket access"""
        logger.info("Testing bucket access...")
        
        try:
            # List files in bucket
            files = self.supabase_service.client.storage.from_("ai-models").list()
            logger.info(f"✅ Bucket access successful. Found {len(files)} files")
            return True
        except Exception as e:
            logger.error(f"❌ Bucket access failed: {e}")
            return False
    
    async def test_upload_download(self) -> bool:
        """Test upload and download functionality"""
        logger.info("Testing upload and download...")
        
        try:
            # Create test content
            test_content = f"FairMind Storage Test - {asyncio.get_event_loop().time()}"
            test_filename = "test_upload_download.txt"
            test_path = f"{self.test_org_id}/{test_filename}"
            
            # Upload test file
            self.supabase_service.client.storage.from_("ai-models").upload(
                path=test_path,
                file=test_content.encode(),
                file_options={
                    "content-type": "text/plain",
                    "upsert": True
                }
            )
            logger.info("✅ Upload successful")
            
            # Download test file
            downloaded_content = self.supabase_service.client.storage.from_("ai-models").download(test_path)
            
            if downloaded_content.decode() == test_content:
                logger.info("✅ Download successful - content matches")
                
                # Clean up
                self.supabase_service.client.storage.from_("ai-models").remove([test_path])
                logger.info("✅ Cleanup successful")
                return True
            else:
                logger.error("❌ Download failed - content mismatch")
                return False
                
        except Exception as e:
            logger.error(f"❌ Upload/download test failed: {e}")
            return False
    
    async def test_model_storage_service(self) -> bool:
        """Test the model storage service"""
        logger.info("Testing model storage service...")
        
        try:
            # Create test model metadata
            test_metadata = {
                "name": "Test Model",
                "version": "1.0.0",
                "type": "classification",
                "framework": "scikit-learn",
                "description": "Test model for storage validation"
            }
            
            # Create test file
            with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
                test_content = f"Test model content - {asyncio.get_event_loop().time()}"
                f.write(test_content.encode())
                temp_file_path = f.name
            
            try:
                # Test upload using model storage service
                with open(temp_file_path, 'rb') as f:
                    result = await model_storage_service.upload_model(
                        model_file=f,
                        model_metadata=test_metadata,
                        organization_id=self.test_org_id
                    )
                
                if result:
                    logger.info("✅ Model storage service upload successful")
                    
                    # Test download
                    model_id = result.get('model_id', 'test_model')
                    downloaded_content = await model_storage_service.download_model(
                        model_id=model_id,
                        organization_id=self.test_org_id
                    )
                    
                    if downloaded_content and downloaded_content.decode() == test_content:
                        logger.info("✅ Model storage service download successful")
                        
                        # Test list models
                        models = await model_storage_service.list_models(self.test_org_id)
                        logger.info(f"✅ List models successful. Found {len(models)} models")
                        
                        # Clean up
                        await model_storage_service.delete_model(model_id, self.test_org_id)
                        logger.info("✅ Model storage service cleanup successful")
                        return True
                    else:
                        logger.error("❌ Model storage service download failed")
                        return False
                else:
                    logger.error("❌ Model storage service upload failed")
                    return False
                    
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"❌ Model storage service test failed: {e}")
            return False
    
    async def test_organization_isolation(self) -> bool:
        """Test organization isolation"""
        logger.info("Testing organization isolation...")
        
        try:
            org1 = "test_org_1"
            org2 = "test_org_2"
            
            # Upload files to different organizations
            content1 = f"Content for {org1}"
            content2 = f"Content for {org2}"
            
            # Upload to org1
            self.supabase_service.client.storage.from_("ai-models").upload(
                path=f"{org1}/test.txt",
                file=content1.encode(),
                file_options={"content-type": "text/plain", "upsert": True}
            )
            
            # Upload to org2
            self.supabase_service.client.storage.from_("ai-models").upload(
                path=f"{org2}/test.txt",
                file=content2.encode(),
                file_options={"content-type": "text/plain", "upsert": True}
            )
            
            # List files for each organization
            files1 = self.supabase_service.client.storage.from_("ai-models").list(path=org1)
            files2 = self.supabase_service.client.storage.from_("ai-models").list(path=org2)
            
            if len(files1) == 1 and len(files2) == 1:
                logger.info("✅ Organization isolation working correctly")
                
                # Clean up
                self.supabase_service.client.storage.from_("ai-models").remove([f"{org1}/test.txt", f"{org2}/test.txt"])
                logger.info("✅ Organization isolation cleanup successful")
                return True
            else:
                logger.error("❌ Organization isolation failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Organization isolation test failed: {e}")
            return False
    
    async def test_file_types(self) -> bool:
        """Test different file types"""
        logger.info("Testing different file types...")
        
        try:
            test_files = [
                ("test.json", '{"test": "data"}', "application/json"),
                ("test.txt", "Plain text content", "text/plain"),
                ("test.md", "# Markdown content", "text/markdown"),
                ("test.pkl", b"pickle content", "application/octet-stream")
            ]
            
            for filename, content, content_type in test_files:
                test_path = f"{self.test_org_id}/{filename}"
                
                # Upload
                if isinstance(content, str):
                    file_content = content.encode()
                else:
                    file_content = content
                
                self.supabase_service.client.storage.from_("ai-models").upload(
                    path=test_path,
                    file=file_content,
                    file_options={
                        "content-type": content_type,
                        "upsert": True
                    }
                )
                
                # Download and verify
                downloaded = self.supabase_service.client.storage.from_("ai-models").download(test_path)
                
                if downloaded == file_content:
                    logger.info(f"✅ {filename} - upload/download successful")
                else:
                    logger.error(f"❌ {filename} - content mismatch")
                    return False
                
                # Clean up
                self.supabase_service.client.storage.from_("ai-models").remove([test_path])
            
            logger.info("✅ All file types tested successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ File type test failed: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all storage tests"""
        logger.info("🚀 Starting Supabase Storage Tests")
        logger.info("=" * 50)
        
        tests = [
            ("Connection Test", self.check_connection),
            ("Storage Service Test", self.check_storage_service),
            ("Bucket Access Test", self.test_bucket_access),
            ("Upload/Download Test", self.test_upload_download),
            ("Model Storage Service Test", self.test_model_storage_service),
            ("Organization Isolation Test", self.test_organization_isolation),
            ("File Types Test", self.test_file_types)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n🧪 Running: {test_name}")
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                if result:
                    passed += 1
                    logger.info(f"✅ {test_name} - PASSED")
                else:
                    logger.error(f"❌ {test_name} - FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name} - ERROR: {e}")
        
        logger.info("=" * 50)
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Supabase storage is working correctly.")
            return True
        else:
            logger.error(f"⚠️ {total - passed} tests failed. Please check your configuration.")
            return False

async def main():
    """Main function"""
    tester = SupabaseStorageTester()
    success = await tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
