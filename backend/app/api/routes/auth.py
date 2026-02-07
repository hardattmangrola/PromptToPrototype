"""Auth routes: login, refresh, me."""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_payload
from app.schemas.auth import LoginRequest, RefreshRequest, Token, UserResponse
from app.schemas.user import UserCreate
from app.services.auth_service import (
    login_for_tokens,
    refresh_tokens,
    get_user_by_id,
    create_user,
)
from app.core.exceptions import AppException

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(body: LoginRequest):
    """Authenticate with email/password; returns access and refresh tokens."""
    return await login_for_tokens(body.email, body.password)


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
    """Register a new patient or doctor. Email must be unique."""
    try:
        user = await create_user(body)
        return UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role,
            full_name=user.full_name,
        )
    except ValueError as e:
        raise AppException(str(e), status_code=400)
