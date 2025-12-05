
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp
import jwt
from jwt import PyJWKClient

from config.settings import settings

logger = logging.getLogger(__name__)

class SupabaseAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify Supabase JWT tokens and inject user info into request.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_service_role_key
        self.jwt_secret = settings.jwt_secret # Fallback or specific secret
        
        # If using Supabase, we might need to fetch JWKS or use the secret
        # For HS256 (default Supabase), it's the JWT secret (which is often the anon key or a specific secret)
        # Usually Supabase uses the project JWT secret.
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip auth for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Enforce auth globally for non-public endpoints
            return Response("Missing or invalid authentication token", status_code=status.HTTP_401_UNAUTHORIZED)
            
        token = auth_header.split(" ")[1]
        
        try:
            # Verify token
            # Note: In a real Supabase setup, you'd use the JWT secret from Supabase dashboard
            # Here we assume settings.jwt_secret is set to that value.
            
            # If we don't have the secret configured yet, we might skip verification or fail
            if not settings.jwt_secret or settings.jwt_secret == "development-jwt-secret-change-in-production":
                 # In dev with mock, maybe decode without verification or use a dummy secret
                 # For now, let's try to decode unverified if in dev, or verify if secret exists
                 if settings.is_development:
                     payload = jwt.decode(token, options={"verify_signature": False})
                 else:
                     # Remove audience check to support internal tokens
                     payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
            else:
                # Remove audience check to support internal tokens
                payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
                
            request.state.user = payload
            
        except jwt.ExpiredSignatureError:
            return Response("Token expired", status_code=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return Response("Invalid token", status_code=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return Response("Authentication failed", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return await call_next(request)
        
    def _is_public_endpoint(self, path: str) -> bool:
        public_paths = [
            "/health",
            "/health/live",
            "/health/ready",
            "/docs",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/",
            "/api"
        ]
        return path in public_paths or path.startswith("/static")
