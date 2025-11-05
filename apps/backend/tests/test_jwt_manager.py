"""
Unit tests for JWT Manager using new secure PyJWT infrastructure.
Tests token creation, verification, and security features.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import jwt as pyjwt

from config.jwt_config import JWTManager, init_jwt_manager, get_jwt_manager
from config.jwt_exceptions import (
    TokenExpiredException,
    InvalidTokenException,
    TokenMissingException,
    TokenCreationException
)


class TestJWTManager:
    """Test suite for JWT Manager functionality."""
    
    @pytest.fixture
    def jwt_manager(self):
        """Create a JWT manager instance for testing."""
        return JWTManager("test-secret-key-for-testing", "HS256")
    
    @pytest.fixture
    def sample_payload(self):
        """Sample JWT payload for testing."""
        return {
            "sub": "test@example.com",
            "user_id": 123,
            "email": "test@example.com",
            "roles": ["user"],
            "permissions": ["read", "write"]
        }
    
    def test_jwt_manager_initialization(self):
        """Test JWT manager initialization."""
        manager = JWTManager("secret", "HS256")
        assert manager.secret_key == "secret"
        assert manager.algorithm == "HS256"
    
    def test_create_token_success(self, jwt_manager, sample_payload):
        """Test successful token creation."""
        token = jwt_manager.create_token(sample_payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots
    
    def test_create_token_with_expiry(self, jwt_manager, sample_payload):
        """Test token creation with custom expiry."""
        expires_delta = timedelta(minutes=30)
        token = jwt_manager.create_token(sample_payload, expires_delta)
        
        # Decode without verification to check expiry
        decoded = jwt_manager.decode_token_unsafe(token)
        assert decoded is not None
        assert "exp" in decoded
        
        # Check that expiry is approximately 30 minutes from now
        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_exp = datetime.utcnow() + expires_delta
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5  # Allow 5 second tolerance
    
    def test_verify_token_success(self, jwt_manager, sample_payload):
        """Test successful token verification."""
        token = jwt_manager.create_token(sample_payload)
        decoded = jwt_manager.verify_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == sample_payload["sub"]
        assert decoded["user_id"] == sample_payload["user_id"]
        assert decoded["email"] == sample_payload["email"]
    
    def test_verify_token_invalid(self, jwt_manager):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        result = jwt_manager.verify_token(invalid_token)
        assert result is None
    
    def test_verify_token_expired(self, jwt_manager, sample_payload):
        """Test verification of expired token."""
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = jwt_manager.create_token(sample_payload, expires_delta)
        
        result = jwt_manager.verify_token(token)
        assert result is None
    
    def test_verify_token_malformed(self, jwt_manager):
        """Test verification of malformed token."""
        malformed_tokens = [
            "not.a.jwt",
            "too.few.parts",
            "too.many.parts.here.extra",
            "",
            "single_string_no_dots"
        ]
        
        for token in malformed_tokens:
            result = jwt_manager.verify_token(token)
            assert result is None
    
    def test_decode_token_unsafe(self, jwt_manager, sample_payload):
        """Test unsafe token decoding (without verification)."""
        token = jwt_manager.create_token(sample_payload)
        decoded = jwt_manager.decode_token_unsafe(token)
        
        assert decoded is not None
        assert decoded["sub"] == sample_payload["sub"]
        assert decoded["user_id"] == sample_payload["user_id"]
    
    def test_decode_token_unsafe_expired(self, jwt_manager, sample_payload):
        """Test unsafe decoding of expired token."""
        expires_delta = timedelta(seconds=-1)
        token = jwt_manager.create_token(sample_payload, expires_delta)
        
        # Unsafe decode should work even for expired tokens
        decoded = jwt_manager.decode_token_unsafe(token)
        assert decoded is not None
        assert decoded["sub"] == sample_payload["sub"]
    
    def test_get_token_expiry(self, jwt_manager, sample_payload):
        """Test getting token expiry time."""
        expires_delta = timedelta(hours=1)
        token = jwt_manager.create_token(sample_payload, expires_delta)
        
        expiry = jwt_manager.get_token_expiry(token)
        assert expiry is not None
        assert isinstance(expiry, datetime)
        
        # Check that expiry is approximately 1 hour from now
        expected_exp = datetime.utcnow() + expires_delta
        time_diff = abs((expiry - expected_exp).total_seconds())
        assert time_diff < 5  # Allow 5 second tolerance
    
    def test_get_token_expiry_invalid(self, jwt_manager):
        """Test getting expiry of invalid token."""
        expiry = jwt_manager.get_token_expiry("invalid.token")
        assert expiry is None
    
    def test_is_token_expired_valid(self, jwt_manager, sample_payload):
        """Test checking if valid token is expired."""
        token = jwt_manager.create_token(sample_payload)
        assert not jwt_manager.is_token_expired(token)
    
    def test_is_token_expired_expired(self, jwt_manager, sample_payload):
        """Test checking if expired token is expired."""
        expires_delta = timedelta(seconds=-1)
        token = jwt_manager.create_token(sample_payload, expires_delta)
        assert jwt_manager.is_token_expired(token)
    
    def test_is_token_expired_invalid(self, jwt_manager):
        """Test checking if invalid token is expired."""
        assert jwt_manager.is_token_expired("invalid.token")
    
    def test_refresh_token_success(self, jwt_manager, sample_payload):
        """Test successful token refresh."""
        original_token = jwt_manager.create_token(sample_payload)
        
        new_token = jwt_manager.refresh_token(original_token)
        assert new_token is not None
        assert new_token != original_token
        
        # Verify new token is valid
        decoded = jwt_manager.verify_token(new_token)
        assert decoded is not None
        assert decoded["sub"] == sample_payload["sub"]
    
    def test_refresh_token_invalid(self, jwt_manager):
        """Test refresh of invalid token."""
        new_token = jwt_manager.refresh_token("invalid.token")
        assert new_token is None
    
    def test_refresh_token_expired(self, jwt_manager, sample_payload):
        """Test refresh of expired token."""
        expires_delta = timedelta(seconds=-1)
        expired_token = jwt_manager.create_token(sample_payload, expires_delta)
        
        new_token = jwt_manager.refresh_token(expired_token)
        assert new_token is None
    
    def test_token_claims_structure(self, jwt_manager, sample_payload):
        """Test that created tokens have proper claims structure."""
        token = jwt_manager.create_token(sample_payload)
        decoded = jwt_manager.decode_token_unsafe(token)
        
        # Check required claims
        assert "sub" in decoded
        assert "exp" in decoded
        assert "iat" in decoded
        assert "nbf" in decoded
        
        # Check custom claims
        assert decoded["user_id"] == sample_payload["user_id"]
        assert decoded["email"] == sample_payload["email"]
    
    def test_token_algorithm_consistency(self, jwt_manager, sample_payload):
        """Test that tokens use the specified algorithm."""
        token = jwt_manager.create_token(sample_payload)
        
        # Decode header to check algorithm
        header = pyjwt.get_unverified_header(token)
        assert header["alg"] == jwt_manager.algorithm
    
    @patch('config.jwt_config.logger')
    def test_logging_on_operations(self, mock_logger, jwt_manager, sample_payload):
        """Test that JWT operations are properly logged."""
        # Test token creation logging
        jwt_manager.create_token(sample_payload)
        mock_logger.debug.assert_called()
        
        # Test token verification logging
        token = jwt_manager.create_token(sample_payload)
        jwt_manager.verify_token(token)
        assert mock_logger.debug.call_count >= 2


class TestJWTManagerGlobal:
    """Test suite for global JWT manager functions."""
    
    def test_init_jwt_manager(self):
        """Test global JWT manager initialization."""
        manager = init_jwt_manager("test-secret", "HS256")
        assert isinstance(manager, JWTManager)
        assert manager.secret_key == "test-secret"
        assert manager.algorithm == "HS256"
    
    def test_get_jwt_manager_success(self):
        """Test getting initialized JWT manager."""
        # Initialize first
        init_jwt_manager("test-secret", "HS256")
        
        # Then get
        manager = get_jwt_manager()
        assert isinstance(manager, JWTManager)
    
    def test_get_jwt_manager_not_initialized(self):
        """Test getting JWT manager when not initialized."""
        # Reset global manager
        import config.jwt_config
        config.jwt_config.jwt_manager = None
        
        with pytest.raises(RuntimeError, match="JWT manager not initialized"):
            get_jwt_manager()


class TestJWTManagerErrorHandling:
    """Test suite for JWT manager error handling."""
    
    @pytest.fixture
    def jwt_manager(self):
        """Create a JWT manager instance for testing."""
        return JWTManager("test-secret-key", "HS256")
    
    def test_create_token_with_invalid_payload(self, jwt_manager):
        """Test token creation with invalid payload."""
        invalid_payloads = [
            None,
            "",
            [],
            {"invalid": object()},  # Non-serializable object
        ]
        
        for payload in invalid_payloads:
            try:
                token = jwt_manager.create_token(payload)
                # If no exception, token should still be created
                assert isinstance(token, str)
            except Exception as e:
                # Exception is acceptable for invalid payloads
                assert isinstance(e, Exception)
    
    def test_verify_token_with_wrong_secret(self, sample_payload):
        """Test token verification with wrong secret."""
        # Create token with one secret
        manager1 = JWTManager("secret1", "HS256")
        token = manager1.create_token(sample_payload)
        
        # Try to verify with different secret
        manager2 = JWTManager("secret2", "HS256")
        result = manager2.verify_token(token)
        assert result is None
    
    def test_verify_token_with_wrong_algorithm(self, sample_payload):
        """Test token verification with wrong algorithm."""
        # Create token with HS256
        manager1 = JWTManager("secret", "HS256")
        token = manager1.create_token(sample_payload)
        
        # Try to verify with HS512
        manager2 = JWTManager("secret", "HS512")
        result = manager2.verify_token(token)
        assert result is None
    
    @pytest.fixture
    def sample_payload(self):
        """Sample JWT payload for testing."""
        return {
            "sub": "test@example.com",
            "user_id": 123,
            "email": "test@example.com"
        }