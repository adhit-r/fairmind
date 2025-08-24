#!/usr/bin/env python3
"""
Test Runner for FairMind Backend

This script runs the test suite and provides a summary of results.
"""

import subprocess
import sys
import os

def run_tests():
    """Run the test suite"""
    print("🧪 Running FairMind Backend Tests...")
    print("=" * 50)
    
    try:
        # Run tests with uv
        result = subprocess.run([
            "uv", "run", "pytest", "tests/", "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print(f"❌ Some tests failed (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_health_check():
    """Run a quick health check"""
    print("\n🏥 Running Health Check...")
    print("-" * 30)
    
    try:
        # Test if the app can be imported
        result = subprocess.run([
            "uv", "run", "python", "-c", 
            "from api.main import app; print('✅ FastAPI app imported successfully')"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error in health check: {e}")
        return False

def main():
    """Main function"""
    print("🚀 FairMind Backend Test Suite")
    print("=" * 50)
    
    # Run health check first
    health_ok = run_health_check()
    
    if not health_ok:
        print("\n❌ Health check failed. Fixing issues before running tests...")
        return 1
    
    # Run tests
    tests_ok = run_tests()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Test Suite: {'✅ PASS' if tests_ok else '❌ FAIL'}")
    
    if health_ok and tests_ok:
        print("\n🎉 All checks passed! Backend is ready for deployment.")
        return 0
    else:
        print("\n⚠️  Some issues found. Please review and fix before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
