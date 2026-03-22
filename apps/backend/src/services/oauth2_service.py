"""
OAuth2 Service for Authentik Integration

Handles OAuth2 code exchange, token validation, user synchronization,
and refresh token management for Authentik-based authentication.
"""

import logging
import httpx
import secrets
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from config.settings import settings
from config.authentik_config import get_authentik_config
from src.services.user_sync_service import user_sync_service

logger = logging.getLogger("fairmind.oauth2")


class OAuth2Service:
    """Service to handle OAuth2 code exchange and token management with Authentik."""

    def __init__(self):
        """Initialize OAuth2 service."""
        self._state_cache: Dict[str, dict] = {}  # In-memory state cache for CSRF
        self.state_ttl = 300  # 5 minutes

    async def generate_state(self) -> str:
        """
        Generate a state parameter for OAuth2 CSRF protection.

        Returns:
            State string for OAuth2 flow
        """
        state = secrets.token_urlsafe(32)
        self._state_cache[state] = {
            "created_at": datetime.utcnow(),
            "used": False,
        }
        logger.debug(f"Generated OAuth2 state: {state}")
        return state

    def validate_state(self, state: str) -> bool:
        """
        Validate state parameter for CSRF protection.

        Args:
            state: State parameter to validate

        Returns:
            True if valid, False otherwise
        """
        if state not in self._state_cache:
            logger.warning(f"State validation failed: state not found")
            return False

        state_data = self._state_cache[state]

        # Check if state has expired (5 minutes)
        age = (datetime.utcnow() - state_data["created_at"]).total_seconds()
        if age > self.state_ttl:
            logger.warning(f"State validation failed: state expired (age={age}s)")
            del self._state_cache[state]
            return False

        # Check if state was already used
        if state_data.get("used"):
            logger.warning(f"State validation failed: state already used (possible replay attack)")
            del self._state_cache[state]
            return False

        # Mark state as used
        state_data["used"] = True
        logger.debug(f"State validated successfully")
        return True

    async def exchange_code_for_tokens(
        self, code: str, state: str, code_verifier: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Exchange OAuth2 authorization code for tokens from Authentik.

        Args:
            code: Authorization code from Authentik
            state: State parameter for CSRF protection
            code_verifier: PKCE code verifier (optional)

        Returns:
            Dict with access_token, refresh_token, and other token data
            None if exchange failed

        Raises:
            ValueError: If state validation fails
        """
        try:
            # Validate state for CSRF protection
            if not self.validate_state(state):
                raise ValueError("Invalid or expired state parameter")

            # Ensure Authentik is configured
            if not settings.authentik_enabled or not settings.authentik_server_url:
                logger.error("Authentik is not enabled or not configured")
                raise ValueError("Authentik authentication not available")

            # Prepare token exchange request
            token_url = f"{settings.authentik_server_url}/application/o/token/"

            payload = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.authentik_oauth_redirect_uri,
                "client_id": settings.authentik_oauth_client_id,
                "client_secret": settings.authentik_oauth_client_secret,
            }

            # Add PKCE code verifier if provided
            if code_verifier:
                payload["code_verifier"] = code_verifier

            logger.debug(f"Exchanging authorization code at {token_url}")

            # Exchange code for tokens
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(token_url, data=payload)

                if response.status_code != 200:
                    logger.error(
                        f"Token exchange failed: {response.status_code} - {response.text}"
                    )
                    raise ValueError(f"Token exchange failed: {response.status_code}")

                token_data = response.json()
                logger.info("Authorization code exchanged successfully for tokens")
                return token_data

        except ValueError as e:
            logger.warning(f"OAuth2 code exchange validation failed: {str(e)}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Failed to exchange code with Authentik: {str(e)}")
            raise ValueError("Failed to connect to authentication server")
        except Exception as e:
            logger.error(f"Unexpected error during code exchange: {str(e)}")
            raise ValueError("Authentication server error")

    async def validate_token_with_jwks(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate and decode JWT token using Authentik JWKS.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            authentik_config = get_authentik_config()
            if not authentik_config:
                logger.error("Authentik config not initialized")
                return None

            payload = await authentik_config.validate_token(token)
            if payload:
                logger.debug(f"Token validated successfully for user: {payload.get('sub')}")
                return payload

            logger.warning("Token validation failed with JWKS")
            return None

        except Exception as e:
            logger.error(f"Error validating token with JWKS: {str(e)}")
            return None

    async def extract_claims(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Extract claims from JWT token.

        Args:
            token: JWT token string

        Returns:
            Dict with extracted claims or None if extraction failed
        """
        try:
            # Validate token first
            payload = await self.validate_token_with_jwks(token)
            if not payload:
                return None

            # Extract relevant claims
            authentik_config = get_authentik_config()
            role_info = authentik_config.extract_role_info(payload)

            claims = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "username": payload.get("preferred_username") or payload.get("email", "").split("@")[0],
                "name": payload.get("name"),
                "email_verified": payload.get("email_verified", False),
                "roles": role_info.get("roles", []),
                "groups": role_info.get("groups", []),
            }

            logger.debug(f"Claims extracted for user: {claims.get('email')}")
            return claims

        except Exception as e:
            logger.error(f"Error extracting claims from token: {str(e)}")
            return None

    async def sync_user_from_authentik(
        self, claims: Dict[str, Any], ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sync user from Authentik claims to FairMind database.

        Creates new user if not exists, updates existing user with fresh data.

        Args:
            claims: Extracted claims from Authentik JWT
            ip_address: Client IP address for audit trail

        Returns:
            Dict with user_id, email, roles, org_id if successful, None otherwise
        """
        try:
            # Extract essential data from claims
            authentik_id = claims.get("sub")
            email = claims.get("email")
            username = claims.get("username")
            name = claims.get("name")
            roles = claims.get("roles", [])
            groups = claims.get("groups", [])

            if not authentik_id or not email:
                logger.error("Missing required claims: sub or email")
                return None

            # Sync user using user sync service
            user = await user_sync_service.get_or_create_user(
                authentik_id=authentik_id,
                email=email,
                username=username,
                name=name,
                roles=roles,
                groups=groups,
                ip_address=ip_address,
            )

            if not user:
                logger.error(f"Failed to sync user: {email}")
                return None

            logger.info(f"User synced successfully: {email}")

            # Return user info for token creation
            return {
                "user_id": str(user.id),
                "email": user.email,
                "username": user.username,
                "name": user.name,
                "roles": user.roles,
                "groups": user.groups,
                "org_id": str(user.primary_org_id) if user.primary_org_id else None,
            }

        except Exception as e:
            logger.error(f"Error syncing user from Authentik: {str(e)}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh expired access token using refresh token.

        Calls Authentik token endpoint with refresh_token grant.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dict with new access_token and refresh_token if successful, None otherwise
        """
        try:
            if not settings.authentik_enabled or not settings.authentik_server_url:
                logger.error("Authentik is not enabled or not configured")
                raise ValueError("Authentik authentication not available")

            token_url = f"{settings.authentik_server_url}/application/o/token/"

            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.authentik_oauth_client_id,
                "client_secret": settings.authentik_oauth_client_secret,
            }

            logger.debug(f"Refreshing token at {token_url}")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(token_url, data=payload)

                if response.status_code != 200:
                    logger.error(
                        f"Token refresh failed: {response.status_code} - {response.text}"
                    )
                    raise ValueError(f"Token refresh failed: {response.status_code}")

                token_data = response.json()
                logger.info("Refresh token exchanged successfully")
                return token_data

        except ValueError as e:
            logger.warning(f"OAuth2 token refresh validation failed: {str(e)}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Failed to refresh token with Authentik: {str(e)}")
            raise ValueError("Failed to connect to authentication server")
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise ValueError("Authentication server error")


# Global OAuth2 service instance
oauth2_service = OAuth2Service()
