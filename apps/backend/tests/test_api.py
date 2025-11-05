"""Test API endpoints."""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestSecurityEndpoints:
    """Test security-related endpoints."""

    def test_security_status(self):
        """Test security status endpoint."""
        response = client.get("/api/v1/security/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "last_scan" in data

    def test_container_scan(self):
        """Test container vulnerability scan endpoint."""
        response = client.post("/api/v1/security/container/scan", params={"image_name": "test:latest"})
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert "target" in data
        assert data["target"] == "test:latest"

    def test_llm_security_test(self):
        """Test LLM security testing endpoint."""
        response = client.post(
            "/api/v1/security/llm/test",
            params={"prompt": "test prompt", "model_id": "test-model"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "test_id" in data
        assert "model_id" in data
        assert data["model_id"] == "test-model"


class TestModelsEndpoints:
    """Test model-related endpoints."""

    def test_get_models(self):
        """Test get models endpoint."""
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_model(self):
        """Test create model endpoint."""
        model_data = {
            "name": "test-model",
            "type": "classification",
            "description": "Test model"
        }
        response = client.post("/api/v1/models", json=model_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-model"


class TestDatasetsEndpoints:
    """Test dataset-related endpoints."""

    def test_get_datasets(self):
        """Test get datasets endpoint."""
        response = client.get("/api/v1/datasets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_dataset(self):
        """Test create dataset endpoint."""
        dataset_data = {
            "name": "test-dataset",
            "description": "Test dataset",
            "size": 1000
        }
        response = client.post("/api/v1/datasets", json=dataset_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-dataset"
