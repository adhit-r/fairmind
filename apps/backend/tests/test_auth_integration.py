"""
Integration tests for authentication system using new JWT infrastructure.
Tests complete authentication flows including login, token verification, and logout.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
from datetime import datetime, timedelta

from api.main import app
from config.auth import auth_manager
from config.jwt_config import init_jwt_manager


class TestAuthenticationIntegration:
    """Integration tests for authentication endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def setup_jwt(self):
        """Setup JWT manager for testing."""
        init_jwt_manager("test-secret-key-for-integration", "HS256")
    
    def test_login_success_admin(self, client, setup_jwt):
        """Test successful admin login."""
        login_data = {
            "email": "admin@fairmind.ai",
            "password": "admin123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data
        
        # Check token type
        assert data["token_type"] == "bearer"
        
        # Check user data
        user = data["user"]
        assert user["email"] == "admin@fairmind.ai"
        assert user["role"] == "admin"
        assert user["username"] == "admin"
    
    def test_login_success_analyst(self, client, setup_jwt):
        """Test successful analyst login."""
        login_data = {
            "email": "analyst@fairmind.ai",
            "password": "analyst123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check user role
        user = data["user"]
        assert user["email"] == "analyst@fairmind.ai"
        assert user["role"] == "analyst"
    
    def test_login_invalid_credentials(self, client, setup_jwt):
        """Test login with invalid credentials."""
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid email or password" in data["detail"]
    
    def test_login_missing_fields(self, client, setup_jwt):
        """Test login with missing fields."""
        # Missing password
        response = client.post("/api/v1/auth/login", json={"email": "test@example.com"})
        assert response.status_code == 422
        
        # Missing email
        response = client.post("/api/v1/auth/login", json={"password": "password"})
        assert response.status_code == 422
        
        # Empty request
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422
    
    def test_protected_endpoint_with_valid_token(self, client, setup_jwt):
        """Test accessing protected endpoint with valid token."""
        # First login to get token
        login_data = {
            "email": "admin@fairmind.ai",
            "password": "admin123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@fairmind.ai"
    
    def test_protected_endpoint_without_token(self, client, setup_jwt):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]
    
    def test_protected_endpoint_with_invalid_token(self, client, setup_jwt):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid token" in data["detail"]
    
    def test_protected_endpoint_with_malformed_header(self, client, setup_jwt):
        """Test accessing protected endpoint with malformed auth header."""
        test_cases = [
            {"Authorization": "invalid_format"},
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "Basic dGVzdA=="},  # Wrong auth type
        ]
        
        for headers in test_cases:
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 401
    
    def test_token_refresh_success(self, client, setup_jwt):
        """Test successful token refresh."""
        # First login to get refresh token
        login_data = {
            "email": "admin@fairmind.ai",
            "password": "admin123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
    
    def test_token_refresh_invalid_token(self, client, setup_jwt):
        """Test token refresh with invalid refresh token."""
        refresh_data = {"refresh_token": "invalid.refresh.token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
    
    def test_logout_success(self, client, setup_jwt):
        """Test successful logout."""
        # First login
        login_data = {
            "email": "admin@fairmind.ai",
            "password": "admin123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully logged out" in data["message"]
    
    def test_logout_without_token(self, client, setup_jwt):
        """Test logout without token."""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401
    
    @patch('config.cache.cache_manager.set')
    @patch('config.cache.cache_manager.delete')
    def test_login_logout_flow_with_cache(self, mock_delete, mock_set, client, setup_jwt):
        """Test complete login-logout flow with cache operations."""
        mock_set.return_value = AsyncMock()
        mock_delete.return_value = AsyncMock()
        
        # Login
        login_data = {
            "email": "admin@fairmind.ai",
            "password": "admin123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 200


class TestAuthenticationMiddleware:
    """Integration tests for JWT authentication middleware."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def setup_jwt(self):
        """Setup JWT manager for testing."""
        init_jwt_manager("test-secret-key-for-middleware", "HS256")
    
    def test_public_endpoints_accessible(self, client, setup_jwt):
        """Test that public endpoints are accessible without authentication."""
        public_endpoints = [
            "/health",
            "/",
            "/api",
            "/api/v1/auth/login",
            "/api/v1/auth/health"
        ]
        
        for endpoint in public_endpoints:
            response = client.get(endpoint)
            # Should not return 401 (may return other status codes for different reasons)
            assert response.status_code != 401
    
    def test_protected_endpoints_require_auth(self, client, setup_jwt):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/api/v1/auth/me",
            "/api/v1/auth/logout",
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_middleware_adds_user_to_request_state(self, client, setup_jwt):
        """Test that middleware adds user information to request state."""
        # Login to get token
        login_data = {
            "email": "admin@fairmind.ai",
            "password": "admin123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        # The fact that we get user data means middleware successfully
        # verified token and added user to request state


class TestAuthenticationSecurity:
    """Security-focused integration tests."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def setup_jwt(self):
        """Setup JWT manager for testing."""
        init_jwt_manager("test-secret-key-for-security", "HS256")
    
    def test_token_expiry_handling(self, client, setup_jwt):
        """Test handling of expired tokens."""
        # Create a token that expires immediately
        from config.jwt_config import get_jwt_manager
        jwt_manager = get_jwt_manager()
        
        payload = {
            "sub": "test@example.com",
            "user_id": 123,
            "email": "test@example.com"
        }
        
        # Create expired token
        expired_token = jwt_manager.create_token(payload, timedelta(seconds=-1))
        
        # Try to use expired token
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower()
    
    def test_token_tampering_detection(self, client, setup_jwt):
        """Test detection of tampered tokens."""
        # Login to get valid token
        login_data = {
            "email": "admin@fairmind.ai",
            "password": "admin123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        original_token = login_response.json()["access_token"]
        
        # Tamper with token (change last character)
        tampered_token = original_token[:-1] + "X"
        
        # Try to use tampered token
        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_sql_injection_in_login(self, client, setup_jwt):
        """Test SQL injection attempts in login."""
        sql_injection_attempts = [
            {"email": "admin@fairmind.ai'; DROP TABLE users; --", "password": "admin123"},
            {"email": "admin@fairmind.ai", "password": "' OR '1'='1"},
            {"email": "' UNION SELECT * FROM users --", "password": "password"},
        ]
        
        for attempt in sql_injection_attempts:
            response = client.post("/api/v1/auth/login", json=attempt)
            # Should either return 401 (invalid credentials) or 422 (validation error)
            assert response.status_code in [401, 422]
    
    def test_xss_in_login_response(self, client, setup_jwt):
        """Test XSS prevention in login responses."""
        xss_payload = "<script>alert('xss')</script>"
        
        login_data = {
            "email": f"test{xss_payload}@example.com",
            "password": "password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Should return error, and response should not contain unescaped script
        response_text = response.text
        assert "<script>" not in response_text
        assert "alert(" not in response_text


class TestAuthenticationPerformance:
    """Performance-focused integration tests."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def setup_jwt(self):
        """Setup JWT manager for testing."""
        init_jwt_manager("test-secret-key-for-performance", "HS256")
    
    def test_concurrent_login_requests(self, client, setup_jwt):
        """Test handling of concurrent login requests."""
        import concurrent.futures
        import threading
        
        def login_request():
            login_data = {
                "email": "admin@fairmind.ai",
                "password": "admin123"
            }
            return client.post("/api/v1/auth/login", json=login_data)
        
        # Execute multiple concurrent login requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(login_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200
    
    def test_token_verification_performance(self, client, setup_jwt):
        """Test token verification performance."""
        # Login to get token
        login_data = {
            "email": "admin@fairmind.ai",
            "password": "admin123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Measure token verification time
        import time
        
        headers = {"Authorization": f"Bearer {token}"}
        
        start_time = time.time()
        for _ in range(100):
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 200
        end_time = time.time()
        
        # Should complete 100 verifications in reasonable time (< 1 second)
        total_time = end_time - start_time
        assert total_time < 1.0, f"Token verification too slow: {total_time}s for 100 requests"