#!/usr/bin/env python3
"""
Quick Start Supabase Storage Setup

This script provides an interactive setup process for Supabase storage.
It will guide you through the entire setup process step by step.
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

class QuickStartSupabase:
    def __init__(self):
        self.env_file = Path(".env")
        self.supabase_service = None
        
    def print_banner(self):
        """Print welcome banner"""
        print("=" * 60)
        print("🚀 FairMind Supabase Storage Quick Start")
        print("=" * 60)
        print()
        print("This script will help you set up Supabase storage for FairMind.")
        print("You'll need your Supabase project URL and service role key.")
        print()
    
    def get_user_input(self, prompt: str, required: bool = True) -> str:
        """Get user input with validation"""
        while True:
            value = input(prompt).strip()
            if value or not required:
                return value
            print("❌ This field is required. Please try again.")
    
    def create_env_file(self) -> bool:
        """Create .env file with user input"""
        print("📝 Step 1: Configure Environment Variables")
        print("-" * 40)
        
        if self.env_file.exists():
            overwrite = input("⚠️  .env file already exists. Overwrite? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("❌ Setup cancelled.")
                return False
        
        print("\n🔑 Please provide your Supabase credentials:")
        print("   (Get these from your Supabase project dashboard → Settings → API)")
        print()
        
        supabase_url = self.get_user_input("Enter your Supabase Project URL: ")
        service_role_key = self.get_user_input("Enter your Service Role Key: ")
        anon_key = self.get_user_input("Enter your Anon Key: ")
        
        # Create .env content
        env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_SERVICE_ROLE_KEY={service_role_key}
SUPABASE_ANON_KEY={anon_key}

# Storage Configuration
STORAGE_BUCKET=ai-models
STORAGE_REGION=us-east-1

# Backend Configuration
BACKEND_URL=http://localhost:8000
UPLOAD_DIR=uploads
DATASET_DIR=datasets
MODEL_REGISTRY=models_registry.json
SIM_RESULTS=simulation_results.json

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
"""
        
        try:
            with open(self.env_file, 'w') as f:
                f.write(env_content)
            print("✅ .env file created successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        print("\n🔗 Step 2: Testing Supabase Connection")
        print("-" * 40)
        
        load_dotenv()
        self.supabase_service = SupabaseService()
        
        if not self.supabase_service.is_connected():
            print("❌ Failed to connect to Supabase.")
            print("   Please check your credentials in the .env file.")
            return False
        
        print("✅ Successfully connected to Supabase!")
        return True
    
    async def setup_storage(self) -> bool:
        """Set up storage bucket and policies"""
        print("\n🗄️  Step 3: Setting Up Storage")
        print("-" * 40)
        
        try:
            # Import and run setup script
            from scripts.setup_supabase_storage import SupabaseStorageSetup
            setup = SupabaseStorageSetup()
            
            # Run setup steps
            if not setup.check_connection():
                return False
            
            if not await setup.create_storage_bucket():
                return False
            
            if not await setup.setup_rls_policies():
                return False
            
            if not await setup.create_sample_organization_folders():
                return False
            
            if not await setup.test_storage_access():
                return False
            
            print("✅ Storage setup completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Storage setup failed: {e}")
            return False
    
    async def migrate_models(self) -> bool:
        """Migrate existing models"""
        print("\n🔄 Step 4: Migrating Existing Models")
        print("-" * 40)
        
        local_storage = Path("storage/models")
        if not local_storage.exists():
            print("ℹ️  No local models found. Skipping migration.")
            return True
        
        migrate = input("📦 Found local models. Migrate to Supabase? (Y/n): ").strip().lower()
        if migrate in ['', 'y', 'yes']:
            try:
                from scripts.migrate_to_supabase import ModelMigrationService
                migration_service = ModelMigrationService()
                
                if await migration_service.run_migration():
                    print("✅ Model migration completed successfully!")
                    return True
                else:
                    print("⚠️  Model migration completed with some issues.")
                    return True
            except Exception as e:
                print(f"❌ Model migration failed: {e}")
                return False
        else:
            print("ℹ️  Skipping model migration.")
            return True
    
    async def run_tests(self) -> bool:
        """Run storage tests"""
        print("\n🧪 Step 5: Running Storage Tests")
        print("-" * 40)
        
        run_tests = input("🧪 Run comprehensive storage tests? (Y/n): ").strip().lower()
        if run_tests in ['', 'y', 'yes']:
            try:
                from scripts.test_supabase_storage import SupabaseStorageTester
                tester = SupabaseStorageTester()
                
                if await tester.run_all_tests():
                    print("✅ All tests passed!")
                    return True
                else:
                    print("⚠️  Some tests failed. Please check the output above.")
                    return False
            except Exception as e:
                print(f"❌ Tests failed: {e}")
                return False
        else:
            print("ℹ️  Skipping tests.")
            return True
    
    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n🎯 Next Steps")
        print("-" * 40)
        print("✅ Supabase storage is now configured!")
        print()
        print("📋 To complete the setup:")
        print("1. Start your backend server: python main.py")
        print("2. Start your frontend: cd frontend && bun dev")
        print("3. Visit http://localhost:3000")
        print("4. Verify that dashboard shows real data")
        print()
        print("📊 Monitor your storage:")
        print("- Go to your Supabase dashboard")
        print("- Navigate to Storage → Buckets")
        print("- Click on the 'ai-models' bucket")
        print()
        print("🔧 For advanced configuration:")
        print("- Read SUPABASE_STORAGE_SETUP.md")
        print("- Check backend/STORAGE_SETUP_GUIDE.md")
        print()
        print("🎉 Congratulations! Your FairMind Supabase storage is ready!")
    
    async def run(self) -> bool:
        """Run the complete quick start process"""
        self.print_banner()
        
        # Step 1: Create .env file
        if not self.create_env_file():
            return False
        
        # Step 2: Test connection
        if not self.test_connection():
            return False
        
        # Step 3: Setup storage
        if not await self.setup_storage():
            return False
        
        # Step 4: Migrate models
        if not await self.migrate_models():
            return False
        
        # Step 5: Run tests
        if not await self.run_tests():
            return False
        
        # Print next steps
        self.print_next_steps()
        
        return True

async def main():
    """Main function"""
    quick_start = QuickStartSupabase()
    success = await quick_start.run()
    
    if success:
        print("\n✅ Quick start completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Quick start failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
