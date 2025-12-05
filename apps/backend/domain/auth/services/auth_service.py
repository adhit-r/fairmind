"""
Local Authentication Service
Replaces Supabase Auth with a self-contained JWT implementation using SQLite.
"""

import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from core.container import service, ServiceLifetime
from core.base_service import BaseService
from core.interfaces import ILogger
from config.settings import settings
from database.connection import db_manager
from sqlalchemy import text

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class User(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True

@service(lifetime=ServiceLifetime.SINGLETON)
class AuthService(BaseService):
    """
    Handles user authentication, registration, and token management locally.
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Verify credentials and return user if valid."""
        with db_manager.get_session() as session:
            result = session.execute(
                text("SELECT id, email, full_name, role, is_active, hashed_password FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if not result:
                return None
                
            if not self.verify_password(password, result.hashed_password):
                return None
                
            return User(
                id=result.id,
                email=result.email,
                full_name=result.full_name,
                role=result.role,
                is_active=result.is_active
            )

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generate a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def register_user(self, email: str, password: str, full_name: str = None) -> User:
        """Register a new user."""
        hashed_pw = self.get_password_hash(password)
        
        with db_manager.get_session() as session:
            # Check existing
            existing = session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if existing:
                raise ValueError("User with this email already exists")
            
            import uuid
            user_id = str(uuid.uuid4())
            
            session.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, full_name, role, is_active, created_at, updated_at)
                    VALUES (:id, :email, :pwd, :name, 'user', true, :now, :now)
                """),
                {
                    "id": user_id,
                    "email": email,
                    "pwd": hashed_pw,
                    "name": full_name,
                    "now": datetime.now(timezone.utc)
                }
            )
            session.commit()
            
            return User(id=user_id, email=email, full_name=full_name, role="user", is_active=True)
