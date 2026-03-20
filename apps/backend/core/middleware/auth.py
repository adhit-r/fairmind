
import logging
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp
import jwt
from jwt import PyJWKClient

from config.settings import settings

logger = logging.getLogger(__name__)

class NeonAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify Neon JWT tokens and inject user info into request.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.jwt_secret = settings.jwt_secret
        self.neon_jwks_client = (
            PyJWKClient(settings.neon_jwks_url) if settings.neon_jwks_url else None
        )
        
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
            verify_kwargs = {}
            if settings.neon_jwt_audience:
                verify_kwargs["audience"] = settings.neon_jwt_audience
            if settings.neon_jwt_issuer:
                verify_kwargs["issuer"] = settings.neon_jwt_issuer

            if self.neon_jwks_client:
                signing_key = self.neon_jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256"],
                    options={"verify_aud": bool(settings.neon_jwt_audience)},
                    **verify_kwargs,
                )
            elif settings.jwt_secret:
                payload = jwt.decode(
                    token,
                    settings.jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": bool(settings.neon_jwt_audience)},
                    **verify_kwargs,
                )
            elif settings.is_development:
                payload = jwt.decode(token, options={"verify_signature": False})
            else:
                return Response(
                    "JWT verification configuration missing",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
                
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
        
        # In development, also allow API access without auth for testing
        if settings.is_development:
            if any(path.startswith(p) for p in [
                "/api/v1/database",
                "/api/v1/core",
                "/api/v1/bias-detection",
                "/api/v1/bias/llm-judge",
                "/api/v1/modern-bias-detection",
                "/api/v1/multimodal-bias-detection",
                "/api/v1/ai-bom",
                "/api/v1/ai-governance",
                "/api/v1/analytics",
                "/api/v1/remediation",
                "/api/v1/compliance",
                "/api/v1/marketplace",
                "/api/v1/reports",
                "/api/v1/settings",
                "/api/v1/datasets",
                "/api/v1/monitoring",
                "/api/v1/mlops"
            ]):
                return True
                
        return path in public_paths or path.startswith("/static")
