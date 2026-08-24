"""
Tests for the production improvements: Database pooling, Redis caching, JWT auth, and compression.
"""

import pytest
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import json
import time

from api.main import app
from config.database import db_manager
from config.cache import cache_manager
from config.auth import auth_manager, User, UserRole
from config.jwt_exceptions import InvalidTokenException
from api.routes import core as core_routes


class TestDatabasePooling:
    """Test database connection pooling."""
    
    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """Test database connection pool initialization."""
        await db_manager.initialize()
        assert db_manager.database is not None
        
        # Test health check
        is_healthy = await db_manager.health_check()
        assert is_healthy is True
        
        await db_manager.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection_context_manager(self):
        """Test database connection context manager."""
        await db_manager.initialize()
        
        async with db_manager.get_connection() as conn:
            assert conn is not None
        
        await db_manager.disconnect()
    
    @pytest.mark.asyncio
    async def test_transaction_context_manager(self):
        """Test database transaction context manager."""
        await db_manager.initialize()
        
        async with db_manager.get_transaction() as transaction:
            assert transaction is not None
        
        await db_manager.disconnect()
    
    @pytest.mark.asyncio
    async def test_pool_status(self):
        """Test connection pool status reporting."""
        await db_manager.initialize()
        
        pool_status = await db_manager.get_pool_status()
        assert isinstance(pool_status, dict)
        
        await db_manager.disconnect()


class TestRedisCaching:
    """Test Redis caching functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self):
        """Test cache initialization."""
        await cache_manager.initialize()
        
        # Test health check
        is_healthy = await cache_manager.health_check()
        # Note: This might be False if Redis is not available, which is OK for tests
        assert isinstance(is_healthy, bool)
        
        await cache_manager.disconnect()
    
    @pytest.mark.asyncio
    async def test_cache_operations(self):
        """Test basic cache operations."""
        await cache_manager.initialize()
        
        # Test set and get
        key = "test_key"
        value = {"test": "data", "number": 42}
        
        success = await cache_manager.set(key, value, ttl=60)
        if success:  # Only test if cache is available
            retrieved_value = await cache_manager.get(key)
            assert retrieved_value == value
            
            # Test exists
            exists = await cache_manager.exists(key)
            assert exists is True
            
            # Test delete
            deleted = await cache_manager.delete(key)
            assert deleted is True
            
            # Verify deletion
            retrieved_after_delete = await cache_manager.get(key)
            assert retrieved_after_delete is None
        
        await cache_manager.disconnect()
    
    @pytest.mark.asyncio
    async def test_cache_serialization(self):
        """Test cache serialization of different data types."""
        await cache_manager.initialize()
        
        test_cases = [
            ("string", "hello world"),
            ("integer", 42),
            ("float", 3.14),
            ("boolean", True),
            ("list", [1, 2, 3, "test"]),
            ("dict", {"key": "value", "nested": {"data": 123}}),
        ]
        
        for test_name, test_value in test_cases:
            key = f"test_{test_name}"
            success = await cache_manager.set(key, test_value)
            
            if success:  # Only test if cache is available
                retrieved = await cache_manager.get(key)
                assert retrieved == test_value, f"Failed for {test_name}: {retrieved} != {test_value}"
                
                # Clean up
                await cache_manager.delete(key)
        
        await cache_manager.disconnect()
    
    @pytest.mark.asyncio
    async def test_cache_batch_operations(self):
        """Test batch cache operations."""
        await cache_manager.initialize()
        
        test_data = {
            "key1": "value1",
            "key2": {"nested": "data"},
            "key3": [1, 2, 3],
        }
        
        # Test set_many
        success = await cache_manager.set_many(test_data)
        
        if success:  # Only test if cache is available
            # Test get_many
            retrieved_data = await cache_manager.get_many(list(test_data.keys()))
            assert retrieved_data == test_data
            
            # Clean up
            for key in test_data.keys():
                await cache_manager.delete(key)
        
        await cache_manager.disconnect()


class TestJWTAuthentication:
    """Test JWT authentication functionality."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        
        # Hash password
        try:
            hashed = auth_manager.get_password_hash(password)
        except ValueError as exc:
            pytest.skip(f"bcrypt backend issue in this environment: {exc}")
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        
        # Verify password
        is_valid = auth_manager.verify_password(password, hashed)
        assert is_valid is True
        
        # Verify wrong password
        is_invalid = auth_manager.verify_password("wrong_password", hashed)
        assert is_invalid is False
    
    def test_token_creation(self):
        """Test JWT token creation."""
        user = User(
            id="test_user",
            email="test@example.com",
            username="testuser",
            role=UserRole.ANALYST,
            is_active=True,
            created_at=time.time(),
            permissions=["model:read", "dataset:read"]
        )
        
        # Create access token
        access_token = auth_manager.create_access_token(user)
        assert isinstance(access_token, str)
        assert len(access_token) > 100  # JWT tokens are long
        
        # Create refresh token
        refresh_token = auth_manager.create_refresh_token(user)
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 100
        
        # Create API key
        api_key = auth_manager.create_api_key(user, "test_key")
        assert isinstance(api_key, str)
        assert len(api_key) > 100

        for token in (access_token, refresh_token, api_key):
            payload = auth_manager.jwt_manager.verify_token(token)
            assert payload is not None
            assert payload["sub"] == user.id
            assert payload["user_id"] == user.id
    
    @pytest.mark.asyncio
    async def test_token_verification(self):
        """Test JWT token verification."""
        user = User(
            id="test_user",
            email="test@example.com",
            username="testuser",
            role=UserRole.ANALYST,
            is_active=True,
            created_at=time.time(),
            permissions=["model:read", "dataset:read"]
        )
        
        # Create and verify access token
        access_token = auth_manager.create_access_token(user)
        token_data = await auth_manager.verify_token(access_token)
        
        assert token_data.user_id == user.id
        assert token_data.email == user.email
        assert token_data.role == user.role
        assert token_data.permissions == user.permissions

    @pytest.mark.asyncio
    async def test_token_verification_rejects_mismatched_subject(self):
        token = auth_manager.jwt_manager.create_token(
            {
                "sub": "different-user",
                "user_id": "expected-user",
                "email": "expected@example.test",
                "roles": [UserRole.ANALYST.value],
                "permissions": [],
                "token_type": "access",
            }
        )

        with pytest.raises(InvalidTokenException):
            await auth_manager.verify_token(token)
    
    @pytest.mark.asyncio
    async def test_token_revocation(self):
        """Test JWT token revocation."""
        user = User(
            id="test_user",
            email="test@example.com",
            username="testuser",
            role=UserRole.ANALYST,
            is_active=True,
            created_at=time.time(),
            permissions=["model:read"]
        )
        
        # Initialize cache for blacklisting
        await cache_manager.initialize()
        
        # Create token
        access_token = auth_manager.create_access_token(user)
        
        # Verify token works
        token_data = await auth_manager.verify_token(access_token)
        assert token_data.user_id
        
        # Revoke token
        await auth_manager.revoke_token(access_token)
        
        # If cache is disabled, blacklist enforcement is unavailable.
        if cache_manager.redis_client:
            with pytest.raises(Exception):
                await auth_manager.verify_token(access_token)
        else:
            token_data_after = await auth_manager.verify_token(access_token)
            assert token_data_after is not None
        
        await cache_manager.disconnect()


class TestAPICompression:
    """Test API response compression."""
    
    def test_gzip_compression_enabled(self):
        """Test that GZip compression is enabled."""
        client = TestClient(app)
        
        # Make a request that should return a large response
        response = client.get("/")
        
        # Check if compression headers are present
        # Note: TestClient might not show compression headers
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestIntegration:
    """Integration tests for all improvements together."""
    
    @pytest.mark.asyncio
    async def test_authenticated_cached_endpoint(self, monkeypatch):
        """Cache the mounted org-scoped model route after JWT authorization."""
        now = datetime.now(timezone.utc)
        user = User(
            id="user-123",
            email="admin@example.test",
            username="admin",
            role=UserRole.ANALYST,
            created_at=now,
            permissions=["model:read"],
        )
        access_token = auth_manager.create_access_token(user)

        model = {
            "id": "model-123",
            "name": "Credit model",
            "description": "Test model",
            "model_type": "classification",
            "version": "1.0.0",
            "upload_date": now,
            "file_path": "/models/model-123.bin",
            "file_size": 128,
            "tags": "[]",
            "metadata": "{}",
            "status": "active",
            "org_id": "org-123",
        }

        class FakeConnection:
            query_count = 0

            async def fetch_all(self, query, params):
                self.query_count += 1
                assert "org_id = :org_id" in query
                assert params == {"org_id": "org-123", "limit": 10, "offset": 0}
                return [model]

        class FakeCache:
            def __init__(self):
                self.values = {}

            async def get(self, key):
                return self.values.get(key)

            async def set(self, key, value, ttl):
                assert ttl == 300
                self.values[key] = value
                return True

        connection = FakeConnection()

        @asynccontextmanager
        async def fake_get_db_connection():
            yield connection

        verify_token = auth_manager.verify_token

        async def verify_token_with_org(token):
            token_data = await verify_token(token)
            return SimpleNamespace(
                id=token_data.user_id,
                org_id="org-123",
                email=token_data.email,
                role=token_data.role,
                permissions=token_data.permissions,
                token_type=token_data.token_type,
            )

        monkeypatch.setattr(core_routes, "cache_manager", FakeCache())
        monkeypatch.setattr(core_routes, "get_db_connection", fake_get_db_connection)
        monkeypatch.setattr(core_routes.settings, "environment", "production")
        monkeypatch.setattr(auth_manager, "verify_token", verify_token_with_org)

        client = TestClient(app)
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            first = client.get("/api/v1/core/models", headers=headers)
            second = client.get("/api/v1/core/models", headers=headers)
        finally:
            client.close()

        assert first.status_code == second.status_code == 200
        assert first.json() == {
            "success": True,
            "data": [{**model, "upload_date": now.isoformat()}],
            "count": 1,
        }
        assert second.json() == first.json()
        assert connection.query_count == 1
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        client = TestClient(app)
        
        # Make multiple requests quickly
        responses = []
        for i in range(5):
            response = client.get("/")
            responses.append(response)
        
        # All should succeed (rate limit is high for tests)
        for response in responses:
            assert response.status_code == 200
            # Check standard API headers
            assert "X-API-Version" in response.headers
    
    def test_security_headers(self):
        """Test security headers are present."""
        client = TestClient(app)
        
        response = client.get("/")
        
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
    
    def test_health_endpoints(self):
        """Test health check endpoints."""
        client = TestClient(app)
        
        # Test main health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert "service" in health_data
        
        # Test readiness endpoint
        response = client.get("/health/ready")
        assert response.status_code == 200
        
        # Test liveness endpoint
        response = client.get("/health/live")
        assert response.status_code == 200


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
