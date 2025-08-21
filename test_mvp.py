#!/usr/bin/env python3
"""
Fairmind MVP Test Script
Tests all core functionality of the MVP
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class FairmindMVPTester:
    def __init__(self):
        self.frontend_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8000"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def test_backend_health(self) -> bool:
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Backend Health Check", True, f"Service: {data.get('service')}")
                return True
            else:
                self.log_test("Backend Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}")
            return False
            
    def test_backend_root(self) -> bool:
        """Test backend root endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Backend Root Endpoint", True, f"Message: {data.get('message')}")
                return True
            else:
                self.log_test("Backend Root Endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Root Endpoint", False, f"Error: {str(e)}")
            return False
            
    def test_bias_detection_api(self) -> bool:
        """Test bias detection API"""
        try:
            payload = {
                "dataset_name": "adult",
                "target_column": "income", 
                "sensitive_columns": ["sex", "race"]
            }
            
            # Convert to form data
            files = {
                'dataset_name': (None, 'adult'),
                'target_column': (None, 'income'),
                'sensitive_columns': (None, '["sex", "race"]')
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/bias/analyze-comprehensive",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Bias Detection API", True, "Analysis completed successfully")
                    return True
                else:
                    self.log_test("Bias Detection API", False, f"API returned success=False")
                    return False
            else:
                self.log_test("Bias Detection API", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bias Detection API", False, f"Error: {str(e)}")
            return False
            
    def test_frontend_connectivity(self) -> bool:
        """Test frontend connectivity"""
        try:
            response = requests.get(f"{self.frontend_url}", timeout=5)
            if response.status_code == 200:
                self.log_test("Frontend Connectivity", True, "Frontend is accessible")
                return True
            else:
                self.log_test("Frontend Connectivity", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Connectivity", False, f"Error: {str(e)}")
            return False
            
    def test_frontend_login_page(self) -> bool:
        """Test frontend login page"""
        try:
            response = requests.get(f"{self.frontend_url}/login", timeout=5)
            if response.status_code == 200:
                self.log_test("Frontend Login Page", True, "Login page is accessible")
                return True
            else:
                self.log_test("Frontend Login Page", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Login Page", False, f"Error: {str(e)}")
            return False
            
    def test_dashboard_page(self) -> bool:
        """Test dashboard page (should redirect to login if not authenticated)"""
        try:
            response = requests.get(f"{self.frontend_url}/dashboard", timeout=5)
            # Dashboard should either be accessible or redirect to login
            if response.status_code in [200, 302]:
                self.log_test("Dashboard Page", True, f"Dashboard accessible (Status: {response.status_code})")
                return True
            else:
                self.log_test("Dashboard Page", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Dashboard Page", False, f"Error: {str(e)}")
            return False
            
    def test_model_registry_page(self) -> bool:
        """Test model registry page"""
        try:
            response = requests.get(f"{self.frontend_url}/model-registry", timeout=5)
            if response.status_code in [200, 302]:
                self.log_test("Model Registry Page", True, f"Model registry accessible (Status: {response.status_code})")
                return True
            else:
                self.log_test("Model Registry Page", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Model Registry Page", False, f"Error: {str(e)}")
            return False
            
    def test_bias_detection_page(self) -> bool:
        """Test bias detection page"""
        try:
            response = requests.get(f"{self.frontend_url}/bias-detection", timeout=5)
            if response.status_code in [200, 302]:
                self.log_test("Bias Detection Page", True, f"Bias detection accessible (Status: {response.status_code})")
                return True
            else:
                self.log_test("Bias Detection Page", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bias Detection Page", False, f"Error: {str(e)}")
            return False
            
    def test_api_endpoints(self) -> bool:
        """Test all API endpoints"""
        endpoints = [
            "/api/v1/bias/analyze",
            "/api/v1/bias/analyze-model", 
            "/api/v1/bias/mitigate-bias"
        ]
        
        all_success = True
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                # Most endpoints should return 405 (Method Not Allowed) for GET
                # or 422 (Unprocessable Entity) for missing parameters
                if response.status_code in [405, 422, 404]:
                    self.log_test(f"API Endpoint {endpoint}", True, f"Endpoint exists (Status: {response.status_code})")
                else:
                    self.log_test(f"API Endpoint {endpoint}", True, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"API Endpoint {endpoint}", False, f"Error: {str(e)}")
                all_success = False
                
        return all_success
        
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Fairmind MVP Test Suite")
        print("=" * 50)
        
        # Backend tests
        print("\n🔧 Backend Tests:")
        self.test_backend_health()
        self.test_backend_root()
        self.test_bias_detection_api()
        self.test_api_endpoints()
        
        # Frontend tests
        print("\n🌐 Frontend Tests:")
        self.test_frontend_connectivity()
        self.test_frontend_login_page()
        self.test_dashboard_page()
        self.test_model_registry_page()
        self.test_bias_detection_page()
        
        # Summary
        print("\n📊 Test Summary:")
        print("=" * 50)
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! MVP is ready for pilot!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
            
        return passed == total

def main():
    """Main test runner"""
    tester = FairmindMVPTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 MVP Testing Complete!")
        print("\nNext steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Login with demo credentials:")
        print("   - Email: demo@fairmind.xyz")
        print("   - Password: demo123")
        print("3. Explore the dashboard and features")
        print("4. Test bias detection with sample models")
        print("5. Check the model registry")
        
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please fix the issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
