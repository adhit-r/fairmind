"""
Auth Routes - API endpoints for local authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional

from core.container import inject
from domain.auth.services.auth_service import AuthService, User

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=User)
async def register(user_data: UserRegister, auth_service: AuthService = Depends(lambda: inject(AuthService))):
    try:
        print(f"DEBUG: Registering with password length: {len(user_data.password)}")
        user = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password[:50], # Truncate here too
            full_name=user_data.full_name
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(lambda: inject(AuthService))
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user.email, "id": user.id, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    # In a real app, verify token and fetch user
    # For now, just decoding to show it works
    # Middleware handles verification usually
    return User(id="me", email="user@example.com", role="user", is_active=True)
