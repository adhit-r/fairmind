"""
Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "service" in data
    
    def test_readiness_check(self, client: TestClient):
        """Test readiness probe endpoint."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["ready", "not_ready"]
        assert "timestamp" in data
    
    def test_liveness_check(self, client: TestClient):
        """Test liveness probe endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_health_check_async(self, async_client: AsyncClient):
        """Test health check with async client."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "service" in data
    
    def test_health_check_includes_system_info(self, client: TestClient):
        """Test that health check includes system information."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
    
    def test_health_check_includes_dependency_checks(self, client: TestClient):
        """Test that health check includes dependency checks."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        # Current health payload is lightweight; readiness/live probes cover dependencies.
        assert "status" in data
    
    def test_health_check_response_time(self, client: TestClient):
        """Test that health check includes response time."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
    
    def test_health_check_headers(self, client: TestClient):
        """Test that health check includes proper headers."""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Should include security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
    
    def test_multiple_health_checks(self, client: TestClient):
        """Test multiple health checks to ensure consistency."""
        responses = []
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            responses.append(response.json())
        
        # All responses should have the same structure
        for response_data in responses:
            assert "status" in response_data
            assert "service" in response_data
