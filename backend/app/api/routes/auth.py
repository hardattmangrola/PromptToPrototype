"""Auth routes: login, refresh, me."""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_payload
from app.schemas.auth import LoginRequest, RefreshRequest, Token, UserResponse
from app.schemas.user import UserCreate
from app.services.auth_service import (
    login_for_tokens,
    refresh_tokens,
    get_user_by_id,
    get_user_by_email,
    create_user,
)
from app.core.exceptions import AppException

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(body: LoginRequest):
    """Authenticate with email/password; returns access and refresh tokens.
    
    Returns:
    - 200 OK with tokens if credentials are valid
    - 401 Unauthorized if user not found or password incorrect
    
    Usage: POST /auth/login
    Body: {"email": "user@example.com", "password": "SecurePass123"}
    """
    try:
        return await login_for_tokens(body.email, body.password)
    except AppException:
        raise
    except Exception as e:
        raise AppException(f"Login failed: {str(e)}", status_code=500)


@router.get("/exists/{email}")
async def email_exists(email: str):
    """Check if an email is already registered (for frontend validation).
    
    Returns:
    - {"exists": true} if email is registered
    - {"exists": false} if email is available
    """
    user = await get_user_by_email(email)
    return {"exists": user is not None, "email": email}


@router.post("/refresh", response_model=Token)
async def refresh(body: RefreshRequest):
    """Exchange refresh token for new access and refresh tokens."""
    return await refresh_tokens(body.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current: dict = Depends(get_current_user_payload)):
    """Return current user info."""
    user = await get_user_by_id(current["sub"])
    if not user:
        raise AppException("User not found", status_code=404)
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        full_name=user.full_name,
    )


@router.post("/register", response_model=UserResponse)
async def register(body: UserCreate):
    """Register a new patient or doctor. Email must be unique.
    
    Returns:
    - 201 Created with user info if registration succeeds
    - 400 Bad Request if email exists or validation fails
    
    Usage: POST /auth/register
    Body: {
        "email": "newuser@example.com",
        "password": "SecurePass123",
        "role": "patient",
        "full_name": "John Doe"
    }
    """
    try:
        # Validate input using Pydantic (already done by FastAPI)
        user = await create_user(body)
        return UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role,
            full_name=user.full_name,
        )
    except ValueError as e:
        # Return 400 Bad Request for validation errors
        raise AppException(str(e), status_code=400)
    except Exception as e:
        # Return 500 for unexpected errors
        raise AppException(f"Registration failed: {str(e)}", status_code=500)
