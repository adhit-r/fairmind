"""
Test script for real API functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_create_ai_bom():
    """Test creating an AI BOM document"""
    print("\nTesting AI BOM creation...")
    
    bom_data = {
        "name": "Test AI Model BOM",
        "version": "1.0.0",
        "description": "Test AI BOM for demonstration",
        "project_name": "Test Project",
        "organization": "FairMind",
        "overall_risk_level": "medium",
        "overall_compliance_status": "compliant",
        "created_by": "test-user",
        "tags": ["test", "demo"],
        "components": [
            {
                "name": "Test Model",
                "type": "model",
                "version": "1.0.0",
                "description": "Test machine learning model",
                "vendor": "FairMind",
                "license": "MIT",
                "risk_level": "low",
                "compliance_status": "compliant"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/ai-bom/create", json=bom_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Created BOM ID: {result['data']['id']}")
        return result['data']['id']
    else:
        print(f"Error: {response.text}")
        return None

def test_list_ai_bom():
    """Test listing AI BOM documents"""
    print("\nTesting AI BOM listing...")
    response = requests.get(f"{BASE_URL}/api/v1/ai-bom/documents")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Found {len(result['data']['documents'])} documents")
        return result['data']['documents']
    else:
        print(f"Error: {response.text}")
        return []

def main():
    """Main test function"""
    print("Testing Real AI BOM API...")
    
    # Test health
    if not test_health():
        print("Health check failed!")
        return
    
    # Test create
    bom_id = test_create_ai_bom()
    if not bom_id:
        print("Create test failed!")
        return
    
    # Test list
    documents = test_list_ai_bom()
    if not documents:
        print("List test failed!")
        return
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()


