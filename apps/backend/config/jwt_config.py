"""
JWT Configuration Module

This module provides JWT token management functionality using PyJWT library.
Replaces the vulnerable python-jose library to eliminate security vulnerabilities.

Supports both:
- Internal HS256 JWT tokens (for backwards compatibility)
- External Authentik RS256 tokens (for enterprise SSO)
"""

import jwt
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError
import logging

logger = logging.getLogger(__name__)


class JWTManager:
    """
    JWT token management class using PyJWT library.
    
    Provides secure JWT token creation, verification, and decoding functionality
    while maintaining backward compatibility with existing token formats.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT manager with secret key and algorithm.
        
        Args:
            secret_key: Secret key for JWT signing and verification
            algorithm: JWT signing algorithm (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        logger.info(f"JWT Manager initialized with algorithm: {algorithm}")
    
    def create_token(
        self, 
        payload: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT token with the given payload.
        
        Args:
            payload: Dictionary containing token claims
            expires_delta: Optional expiration time delta
            
        Returns:
            Encoded JWT token string
            
        Raises:
            Exception: If token creation fails
        """
        try:
            to_encode = payload.copy()
            
            # Set expiration time
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(hours=24)
            
            # Add standard claims
            to_encode.update({
                "exp": expire,
                "iat": datetime.utcnow(),
                "nbf": datetime.utcnow()  # Not before
            })
            
            # Create token
            token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            # Ensure token is string (PyJWT < 2.0 returns bytes)
            if isinstance(token, bytes):
                token = token.decode('utf-8')
                
            logger.debug(f"JWT token created for subject: {payload.get('sub', 'unknown')}")
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to create JWT token: {str(e)}")
            raise Exception(f"Token creation failed: {str(e)}") 
   
    def verify_token(
        self,
        token: str,
        use_authentik: bool = False,
        authentik_config: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Supports both internal HS256 tokens and external Authentik RS256 tokens.

        Args:
            token: JWT token string to verify
            use_authentik: Whether to use Authentik JWKS validation
            authentik_config: Authentik configuration object (required if use_authentik=True)

        Returns:
            Decoded token payload if valid, None if invalid
        """
        # If Authentik is enabled, use async JWKS validation
        if use_authentik and authentik_config:
            logger.debug("Using Authentik JWKS validation for token")
            # Note: This requires async context. Should be called via async wrapper
            # For now, we'll require calling the async method directly
            logger.warning("Use async validate_token_with_authentik() for Authentik tokens")
            return None

        # Use internal HS256 validation
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True
                }
            )
            logger.debug(f"JWT token verified for subject: {payload.get('sub', 'unknown')}")
            return payload

        except ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except DecodeError:
            logger.warning("JWT token decode error - malformed token")
            return None
        except InvalidTokenError as e:
            logger.warning(f"JWT token validation failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying JWT token: {str(e)}")
            return None
    
    def decode_token_unsafe(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token without verification (for debugging purposes only).
        
        Args:
            token: JWT token string to decode
            
        Returns:
            Decoded token payload without verification, None if decode fails
            
        Warning:
            This method does not verify the token signature or expiration.
            Use only for debugging or inspection purposes.
        """
        try:
            payload = jwt.decode(
                token, 
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_nbf": False
                }
            )
            logger.debug("JWT token decoded without verification")
            return payload
            
        except Exception as e:
            logger.error(f"Failed to decode JWT token: {str(e)}")
            return None
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get the expiration time of a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Expiration datetime if token is valid, None otherwise
        """
        payload = self.decode_token_unsafe(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"])
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a JWT token is expired.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is expired, False otherwise
        """
        expiry = self.get_token_expiry(token)
        if expiry:
            return datetime.utcnow() > expiry
        return True  # Consider invalid tokens as expired
    
    async def verify_token_with_authentik(
        self,
        token: str,
        authentik_config: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token using Authentik JWKS (RS256).

        This is an async method that validates tokens issued by Authentik.

        Args:
            token: JWT token string to verify
            authentik_config: AuthentikConfig instance with JWKS endpoint

        Returns:
            Decoded token payload if valid, None if invalid
        """
        try:
            logger.debug("Validating token with Authentik JWKS")
            payload = await authentik_config.validate_token(token)

            if payload:
                logger.debug(f"Authentik token verified for subject: {payload.get('sub', 'unknown')}")
                return payload
            else:
                logger.warning("Authentik token validation failed")
                return None

        except Exception as e:
            logger.error(f"Unexpected error validating Authentik token: {str(e)}")
            return None

    def refresh_token(
        self,
        token: str,
        expires_delta: Optional[timedelta] = None
    ) -> Optional[str]:
        """
        Refresh a JWT token with a new expiration time.
        
        Args:
            token: Current JWT token
            expires_delta: New expiration time delta
            
        Returns:
            New JWT token if refresh successful, None otherwise
        """
        payload = self.verify_token(token)
        if payload:
            # Remove old timing claims
            payload.pop("exp", None)
            payload.pop("iat", None)
            payload.pop("nbf", None)
            
            # Create new token
            return self.create_token(payload, expires_delta)
        
        logger.warning("Cannot refresh invalid or expired token")
        return None


# Global JWT manager instance (will be initialized in main app)
jwt_manager: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    """
    Get the global JWT manager instance.
    
    Returns:
        JWTManager instance
        
    Raises:
        RuntimeError: If JWT manager is not initialized
    """
    if jwt_manager is None:
        raise RuntimeError("JWT manager not initialized. Call init_jwt_manager() first.")
    return jwt_manager


def init_jwt_manager(secret_key: str, algorithm: str = "HS256") -> JWTManager:
    """
    Initialize the global JWT manager instance.
    
    Args:
        secret_key: Secret key for JWT operations
        algorithm: JWT algorithm to use
        
    Returns:
        Initialized JWTManager instance
    """
    global jwt_manager
    jwt_manager = JWTManager(secret_key, algorithm)
    logger.info("Global JWT manager initialized")
    return jwt_manager