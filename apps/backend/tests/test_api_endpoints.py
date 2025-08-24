"""
Comprehensive API Endpoint Tests

This test suite covers all major API endpoints to ensure they work correctly
for customer deployment using modern tools (uv, httpx).
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
import tempfile
import os
from datetime import datetime

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app

# Use FastAPI TestClient for testing
@pytest.fixture
def client():
    return TestClient(app)

class TestAPIEndpoints:
    """Test suite for all API endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert "features" in data
    
    def test_api_info_endpoint(self, client):
        """Test API information endpoint"""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Fairmind ML Service API"
        assert "version" in data
        assert "endpoints" in data
    
    @patch('api.routes.bias_detection.ComprehensiveBiasDetectionService')
    def test_bias_detection_analyze(self, mock_service, client):
        """Test bias detection analysis endpoint"""
        # Mock the service response
        mock_service_instance = Mock()
        mock_service_instance.analyze_dataset_comprehensive.return_value = {
            "overall_bias_score": 0.15,
            "demographic_parity": 0.12,
            "equalized_odds": 0.18,
            "recommendations": ["Consider retraining with balanced data"]
        }
        mock_service.return_value = mock_service_instance
        
        # Test data
        test_data = {
            "model_path": "test_model.pkl",
            "dataset_path": "test_data.csv",
            "target": "income",
            "features": ["age", "education", "hours_per_week"],
            "protected_attributes": ["gender", "race"]
        }
        
        response = client.post("/api/v1/bias-detection/analyze", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert "overall_bias_score" in data
        assert "recommendations" in data

        def test_ai_bom_create_document(self, client):
                """Test AI BOM document creation"""
                # Test data
                test_data = {
                    "project_name": "Test Project",
                    "description": "Test AI BOM document",
                    "components": [
                        {
                            "name": "Test Model",
                            "version": "1.0.0",
                            "type": "ml_model"
                        }
                    ]
                }

                response = client.post("/api/v1/ai-bom/documents", json=test_data)
                # Should return 200 or 422 (validation error)
                assert response.status_code in [200, 422]
                if response.status_code == 200:
                    data = response.json()
                    assert data["success"] == True
    
    @patch('api.routes.monitoring.MonitoringService')
    def test_monitoring_config_create(self, mock_service, client):
        """Test monitoring configuration creation"""
        # Mock the service response
        mock_service_instance = Mock()
        mock_service_instance.create_config.return_value = {
            "id": "test-config-id",
            "model_id": "test-model",
            "metrics": ["accuracy", "bias", "drift"],
            "enabled": True
        }
        mock_service.return_value = mock_service_instance
        
        # Test data
        test_data = {
            "model_id": "test-model",
            "metrics": ["accuracy", "bias", "drift"],
            "thresholds": {"accuracy": 0.8},
            "frequency": 300,
            "enabled": True
        }
        
        response = client.post("/api/v1/monitoring/config", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    @patch('api.routes.monitoring.AlertService')
    def test_alert_rule_create(self, mock_service, client):
        """Test alert rule creation"""
        # Mock the service response
        mock_service_instance = Mock()
        mock_service_instance.create_rule.return_value = {
            "id": "test-rule-id",
            "name": "Test Alert Rule",
            "model_id": "test-model",
            "metric": "accuracy",
            "condition": "<",
            "threshold": 0.8,
            "severity": "medium"
        }
        mock_service.return_value = mock_service_instance
        
        # Test data
        test_data = {
            "name": "Test Alert Rule",
            "model_id": "test-model",
            "metric": "accuracy",
            "condition": "<",
            "threshold": 0.8,
            "severity": "medium"
        }
        
        response = client.post("/api/v1/monitoring/alerts/rules", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_cors_headers(self, client):
        """Test CORS headers are properly set"""
        response = client.options("/health")
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    def test_error_handling(self, client):
        """Test error handling for invalid requests"""
        # Test invalid JSON
        response = client.post("/api/v1/bias-detection/analyze", 
                              data="invalid json",
                              headers={"Content-Type": "application/json"})
        assert response.status_code == 422  # Validation error
        
        # Test non-existent endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_protected_endpoints_require_auth(self, client):
        """Test that protected endpoints require authentication"""
        # These endpoints should require authentication
        protected_endpoints = [
            "/api/v1/core/dashboard",
            "/api/v1/core/models",
            "/api/v1/core/datasets"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            # Should return 401 or redirect to login
            assert response.status_code in [401, 403, 302]

class TestDataValidation:
    """Test data validation for API endpoints"""
    
    def test_bias_detection_validation(self, client):
        """Test bias detection input validation"""
        # Test missing required fields
        invalid_data = {
            "model_path": "test.pkl"
            # Missing required fields
        }
        
        response = client.post("/api/v1/bias-detection/analyze", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_ai_bom_validation(self, client):
        """Test AI BOM input validation"""
        # Test invalid component data
        invalid_data = {
            "project_name": "Test",
            "components": [
                {
                    "name": "",  # Empty name should fail validation
                    "version": "1.0.0"
                }
            ]
        }
        
        response = client.post("/api/v1/ai-bom/documents", json=invalid_data)
        assert response.status_code == 422  # Validation error

class TestPerformance:
    """Test API performance under load"""
    
    def test_health_endpoint_performance(self, client):
        """Test health endpoint response time"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Health check should respond quickly (< 100ms)
        assert (end_time - start_time) < 0.1
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.get("/health")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(errors) == 0
        assert len(results) == 10
        assert all(status == 200 for status in results)

class TestFileUpload:
    """Test file upload functionality"""
    
    def test_model_upload(self, client):
        """Test model file upload"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp_file:
            tmp_file.write(b"fake model data")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                files = {"file": ("test_model.pkl", f, "application/octet-stream")}
                data = {"model_name": "Test Model", "version": "1.0.0"}
                response = client.post("/api/v1/models/upload", files=files, data=data)
            
            # Should return 200 or 422 (depending on validation)
            assert response.status_code in [200, 422]
        finally:
            # Clean up
            os.unlink(tmp_file_path)
    
    def test_dataset_upload(self, client):
        """Test dataset file upload"""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
            tmp_file.write(b"age,income,gender\n25,50000,male\n30,60000,female")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                files = {"file": ("test_data.csv", f, "text/csv")}
                data = {"dataset_name": "Test Dataset", "description": "Test data"}
                response = client.post("/api/v1/datasets/upload", files=files, data=data)
            
            # Should return 200 or 422 (depending on validation)
            assert response.status_code in [200, 422]
        finally:
            # Clean up
            os.unlink(tmp_file_path)

class TestMonitoringEndpoints:
    """Test monitoring and alerting endpoints"""
    
    @patch('api.routes.monitoring.MonitoringService')
    def test_metrics_recording(self, mock_service, client):
        """Test metrics recording endpoint"""
        mock_service_instance = Mock()
        mock_service_instance.record_metrics.return_value = {
            "id": "test-metric-id",
            "model_id": "test-model",
            "timestamp": datetime.now().isoformat()
        }
        mock_service.return_value = mock_service_instance
        
        test_metrics = {
            "model_id": "test-model",
            "accuracy": 0.85,
            "latency": 150.0,
            "error_rate": 0.02
        }
        
        response = client.post("/api/v1/monitoring/metrics", json=test_metrics)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    @patch('api.routes.monitoring.AlertService')
    def test_alerts_listing(self, mock_service, client):
        """Test alerts listing endpoint"""
        mock_service_instance = Mock()
        mock_service_instance.list_alerts.return_value = [
            {
                "id": "test-alert-1",
                "model_id": "test-model",
                "severity": "medium",
                "message": "Test alert message"
            }
        ]
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/monitoring/alerts")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data

if __name__ == "__main__":
    # Run tests with uv
    pytest.main([__file__, "-v"])
