#!/usr/bin/env python3
"""
Migrate Models to Supabase Storage

This script migrates existing models from local storage to Supabase storage.
Run this after setting up Supabase storage and environment variables.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
import hashlib
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from services.model_storage_service import model_storage_service
from supabase_client import SupabaseService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelMigrationService:
    def __init__(self):
        load_dotenv()
        self.supabase_service = SupabaseService()
        self.local_storage_path = Path("storage/models")
        self.registry_file = Path("models_registry.json")
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        logger.info("Checking prerequisites...")
        
        # Check if Supabase is connected
        if not self.supabase_service.is_connected():
            logger.error("❌ Supabase not connected. Please check your environment variables.")
            return False
        
        # Check if local storage exists
        if not self.local_storage_path.exists():
            logger.error("❌ Local storage path does not exist: storage/models")
            return False
        
        # Check if registry file exists
        if not self.registry_file.exists():
            logger.error("❌ Model registry file does not exist: models_registry.json")
            return False
        
        logger.info("✅ All prerequisites met")
        return True
    
    def load_model_registry(self) -> list:
        """Load the model registry"""
        try:
            with open(self.registry_file, 'r') as f:
                registry = json.load(f)
            logger.info(f"✅ Loaded {len(registry)} models from registry")
            return registry
        except Exception as e:
            logger.error(f"❌ Failed to load model registry: {e}")
            return []
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    async def migrate_model_file(self, model_info: dict, org_id: str) -> bool:
        """Migrate a single model file to Supabase"""
        try:
            # Get the local file path
            local_path = model_info.get('path', '')
            if not local_path:
                logger.warning(f"⚠️ No path found for model: {model_info.get('name', 'Unknown')}")
                return False
            
            local_file_path = Path(local_path)
            if not local_file_path.exists():
                logger.warning(f"⚠️ Local file not found: {local_path}")
                return False
            
            # Read the file
            with open(local_file_path, 'rb') as f:
                file_content = f.read()
            
            # Determine the Supabase path
            filename = local_file_path.name
            supabase_path = f"{org_id}/{filename}"
            
            # Determine content type based on file extension
            content_type = "application/octet-stream"
            if filename.endswith('.json'):
                content_type = "application/json"
            elif filename.endswith('.txt'):
                content_type = "text/plain"
            elif filename.endswith('.md'):
                content_type = "text/markdown"
            
            # Upload to Supabase
            self.supabase_service.client.storage.from_("ai-models").upload(
                path=supabase_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "upsert": True
                }
            )
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(local_file_path)
            
            # Update model info with Supabase metadata
            model_info.update({
                'supabase_path': supabase_path,
                'file_hash': file_hash,
                'file_size': len(file_content),
                'migrated_at': datetime.now().isoformat(),
                'storage_type': 'supabase'
            })
            
            logger.info(f"✅ Migrated: {filename} ({len(file_content)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate {model_info.get('name', 'Unknown')}: {e}")
            return False
    
    async def migrate_organization_models(self, org_id: str, models: list) -> dict:
        """Migrate all models for an organization"""
        logger.info(f"Migrating models for organization: {org_id}")
        
        org_models = [m for m in models if m.get('org_id') == org_id]
        logger.info(f"Found {len(org_models)} models for {org_id}")
        
        migrated_count = 0
        failed_count = 0
        total_size = 0
        
        for model in org_models:
            success = await self.migrate_model_file(model, org_id)
            if success:
                migrated_count += 1
                total_size += model.get('file_size', 0)
            else:
                failed_count += 1
        
        return {
            'organization': org_id,
            'total_models': len(org_models),
            'migrated': migrated_count,
            'failed': failed_count,
            'total_size': total_size
        }
    
    async def update_model_registry(self, models: list) -> bool:
        """Update the model registry with migration information"""
        try:
            # Create backup of original registry
            backup_path = self.registry_file.with_suffix('.json.backup')
            with open(self.registry_file, 'r') as f:
                original_data = f.read()
            
            with open(backup_path, 'w') as f:
                f.write(original_data)
            
            logger.info(f"✅ Created backup: {backup_path}")
            
            # Write updated registry
            with open(self.registry_file, 'w') as f:
                json.dump(models, f, indent=2)
            
            logger.info("✅ Updated model registry")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update model registry: {e}")
            return False
    
    async def verify_migration(self, models: list) -> bool:
        """Verify that all migrated models are accessible in Supabase"""
        logger.info("Verifying migration...")
        
        verification_count = 0
        total_models = len([m for m in models if m.get('storage_type') == 'supabase'])
        
        for model in models:
            if model.get('storage_type') == 'supabase':
                try:
                    supabase_path = model.get('supabase_path')
                    if supabase_path:
                        # Try to download a small portion to verify access
                        result = self.supabase_service.client.storage.from_("ai-models").download(
                            path=supabase_path,
                            options={"transform": {"width": 1, "height": 1}}
                        )
                        verification_count += 1
                        logger.info(f"✅ Verified: {model.get('name', 'Unknown')}")
                except Exception as e:
                    logger.error(f"❌ Verification failed for {model.get('name', 'Unknown')}: {e}")
        
        logger.info(f"✅ Verified {verification_count}/{total_models} models")
        return verification_count == total_models
    
    async def run_migration(self) -> bool:
        """Run the complete migration process"""
        logger.info("🚀 Starting Model Migration to Supabase")
        logger.info("=" * 50)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Load model registry
        models = self.load_model_registry()
        if not models:
            return False
        
        # Get unique organizations
        organizations = list(set([m.get('org_id', 'demo_org') for m in models]))
        logger.info(f"Found organizations: {organizations}")
        
        # Migrate models for each organization
        migration_results = []
        for org_id in organizations:
            result = await self.migrate_organization_models(org_id, models)
            migration_results.append(result)
        
        # Update model registry
        if not await self.update_model_registry(models):
            return False
        
        # Verify migration
        if not await self.verify_migration(models):
            logger.warning("⚠️ Some models failed verification")
        
        # Print summary
        logger.info("=" * 50)
        logger.info("📊 Migration Summary:")
        total_migrated = sum(r['migrated'] for r in migration_results)
        total_failed = sum(r['failed'] for r in migration_results)
        total_size = sum(r['total_size'] for r in migration_results)
        
        for result in migration_results:
            logger.info(f"  {result['organization']}: {result['migrated']}/{result['total_models']} models migrated")
        
        logger.info(f"  Total: {total_migrated} migrated, {total_failed} failed")
        logger.info(f"  Total size: {total_size / (1024*1024):.2f} MB")
        
        if total_failed == 0:
            logger.info("🎉 Migration completed successfully!")
            return True
        else:
            logger.warning(f"⚠️ Migration completed with {total_failed} failures")
            return False

async def main():
    """Main function"""
    migration_service = ModelMigrationService()
    success = await migration_service.run_migration()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
