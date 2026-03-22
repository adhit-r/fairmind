"""
Authentik Configuration and JWKS Validation Module

This module provides integration with Authentik for JWT validation using
JSON Web Key Sets (JWKS). It validates RS256-signed tokens from Authentik
while maintaining backwards compatibility with internal HS256 tokens.
"""

import json
import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import lru_cache
from jwt import decode as jwt_decode
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class JWKSCache:
    """Cache JWKS from Authentik with TTL."""

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize JWKS cache.

        Args:
            ttl_seconds: Cache time-to-live in seconds (default: 1 hour)
        """
        self.ttl_seconds = ttl_seconds
        self.cached_jwks: Optional[Dict[str, Any]] = None
        self.cache_time: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if cache has expired."""
        if self.cache_time is None:
            return True
        return datetime.utcnow() > self.cache_time + timedelta(seconds=self.ttl_seconds)

    def get(self) -> Optional[Dict[str, Any]]:
        """Get cached JWKS if valid."""
        if not self.is_expired():
            return self.cached_jwks
        return None

    def set(self, jwks: Dict[str, Any]) -> None:
        """Cache JWKS data."""
        self.cached_jwks = jwks
        self.cache_time = datetime.utcnow()
        logger.debug("JWKS cached successfully")

    def invalidate(self) -> None:
        """Invalidate cache."""
        self.cached_jwks = None
        self.cache_time = None


class AuthentikConfig:
    """Authentik JWKS configuration and JWT validation."""

    def __init__(
        self,
        jwks_url: str,
        issuer: str,
        audience: str,
        algorithm: str = "RS256",
        jwks_cache_ttl: int = 3600,
    ):
        """Initialize Authentik configuration.

        Args:
            jwks_url: URL to Authentik's JWKS endpoint
            issuer: Expected token issuer (iss claim)
            audience: Expected token audience (aud claim)
            algorithm: Token signing algorithm (default: RS256)
            jwks_cache_ttl: JWKS cache TTL in seconds (default: 1 hour)
        """
        self.jwks_url = jwks_url
        self.issuer = issuer
        self.audience = audience
        self.algorithm = algorithm
        self.jwks_cache = JWKSCache(ttl_seconds=jwks_cache_ttl)
        self._cached_public_keys: Dict[str, Any] = {}

        logger.info(
            f"Authentik config initialized: "
            f"issuer={issuer}, audience={audience}, algorithm={algorithm}"
        )

    async def fetch_jwks(self) -> Optional[Dict[str, Any]]:
        """Fetch JWKS from Authentik endpoint.

        Returns:
            JWKS dict if successful, None otherwise
        """
        # Check cache first
        cached = self.jwks_cache.get()
        if cached is not None:
            logger.debug("Using cached JWKS")
            return cached

        try:
            logger.debug(f"Fetching JWKS from {self.jwks_url}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()

                jwks = response.json()
                self.jwks_cache.set(jwks)
                return jwks

        except httpx.RequestError as e:
            logger.error(f"Failed to fetch JWKS: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching JWKS: {str(e)}")
            return None

    def get_public_key(self, kid: str, jwks: Dict[str, Any]) -> Optional[str]:
        """Get public key from JWKS by key ID.

        Args:
            kid: Key ID (from JWT header)
            jwks: JWKS dict from Authentik

        Returns:
            PEM-formatted public key or None if not found
        """
        try:
            # Find key with matching kid
            keys = jwks.get("keys", [])
            key_data = None

            for key in keys:
                if key.get("kid") == kid:
                    key_data = key
                    break

            if not key_data:
                logger.warning(f"Key ID {kid} not found in JWKS")
                return None

            # Convert JWK to PEM format
            if key_data.get("kty") == "RSA":
                # Extract RSA public key components
                from jwt import PyJWKClient
                from jwt.algorithms import RSAAlgorithm

                # Use PyJWT's built-in JWK to PEM conversion
                rsa_key = RSAAlgorithm.from_jwk(json.dumps(key_data))
                public_pem = rsa_key.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                return public_pem.decode("utf-8")

            logger.warning(f"Unsupported key type: {key_data.get('kty')}")
            return None

        except Exception as e:
            logger.error(f"Error extracting public key: {str(e)}")
            return None

    async def validate_token(
        self, token: str, options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Validate and decode JWT token using JWKS.

        Args:
            token: JWT token string
            options: Additional JWT validation options

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            # Decode header to get key ID without verification
            import jwt as pyjwt

            unverified_header = pyjwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                logger.warning("JWT missing key ID (kid) in header")
                return None

            # Fetch JWKS
            jwks = await self.fetch_jwks()
            if not jwks:
                logger.error("Failed to fetch JWKS for token validation")
                return None

            # Get public key
            public_key = self.get_public_key(kid, jwks)
            if not public_key:
                logger.warning(f"Public key not found for kid: {kid}")
                return None

            # Validate token
            validate_options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            }
            if options:
                validate_options.update(options)

            payload = jwt_decode(
                token,
                public_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options=validate_options,
            )

            logger.debug(f"Token validated for subject: {payload.get('sub', 'unknown')}")
            return payload

        except ExpiredSignatureError:
            logger.warning("Authentik token has expired")
            return None
        except DecodeError as e:
            logger.warning(f"Token decode error: {str(e)}")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            return None

    def map_authentik_roles_to_fairmind(self, groups: List[str]) -> List[str]:
        """Map Authentik groups to FairMind roles.

        Args:
            groups: List of Authentik group names

        Returns:
            List of FairMind role names
        """
        role_mapping = {
            "fairmind-admin": "admin",
            "fairmind-analyst": "analyst",
            "fairmind-viewer": "viewer",
        }

        roles = []
        for group in groups:
            if group in role_mapping:
                roles.append(role_mapping[group])
            else:
                logger.debug(f"No role mapping found for group: {group}")

        return roles

    def extract_role_info(self, token_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract role and group information from Authentik token.

        Args:
            token_payload: Decoded JWT payload

        Returns:
            Dict with 'groups' and 'roles' keys
        """
        try:
            # Authentik includes groups in the token or user_id can be used to fetch groups
            groups = token_payload.get("groups", [])
            roles = self.map_authentik_roles_to_fairmind(groups)

            return {
                "groups": groups,
                "roles": roles,
                "user_id": token_payload.get("sub"),
                "username": token_payload.get("preferred_username"),
                "email": token_payload.get("email"),
                "name": token_payload.get("name"),
            }

        except Exception as e:
            logger.error(f"Error extracting role info: {str(e)}")
            return {
                "groups": [],
                "roles": ["viewer"],  # Default to viewer role on error
                "user_id": token_payload.get("sub"),
            }


# Global Authentik config instance
authentik_config: Optional[AuthentikConfig] = None


def init_authentik_config(
    jwks_url: str,
    issuer: str,
    audience: str,
    algorithm: str = "RS256",
    jwks_cache_ttl: int = 3600,
) -> AuthentikConfig:
    """Initialize global Authentik configuration.

    Args:
        jwks_url: URL to Authentik's JWKS endpoint
        issuer: Expected token issuer
        audience: Expected token audience
        algorithm: Token signing algorithm
        jwks_cache_ttl: JWKS cache TTL in seconds

    Returns:
        Initialized AuthentikConfig instance
    """
    global authentik_config
    authentik_config = AuthentikConfig(
        jwks_url=jwks_url,
        issuer=issuer,
        audience=audience,
        algorithm=algorithm,
        jwks_cache_ttl=jwks_cache_ttl,
    )
    logger.info("Authentik configuration initialized")
    return authentik_config


def get_authentik_config() -> Optional[AuthentikConfig]:
    """Get global Authentik configuration instance.

    Returns:
        AuthentikConfig instance or None if not initialized
    """
    return authentik_config
