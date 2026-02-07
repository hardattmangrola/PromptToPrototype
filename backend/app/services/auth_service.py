"""Authentication service: login, refresh, user lookup."""
from typing import Optional

from bson import ObjectId

from app.config import get_settings
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
)
from app.db.mongodb import get_user_collection
from app.db.models import UserInDB
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserCreateInternal
from app.core.exceptions import UnauthorizedError


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Fetch user by email. Returns None if not found."""
    col = get_user_collection()
    doc = await col.find_one({"email": email.lower()})
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return UserInDB(**doc)


async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Fetch user by ID."""
    col = get_user_collection()
    try:
        doc = await col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return UserInDB(**doc)


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """Verify credentials and return user or None."""
    user = await get_user_by_email(email)
    if not user or user.disabled:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def login_for_tokens(email: str, password: str) -> Token:
    """Authenticate and return access + refresh tokens."""
    user = await authenticate_user(email, password)
    if not user:
        raise UnauthorizedError("Invalid email or password")
    settings = get_settings()
    access = create_access_token(subject=str(user.id), role=user.role)
    refresh = create_refresh_token(subject=str(user.id), role=user.role)
    return Token(
        access_token=access,
        refresh_token=refresh,
        expires_in_seconds=settings.access_token_expire_minutes * 60,
    )


async def refresh_tokens(refresh_token: str) -> Token:
    """Issue new access (and optionally refresh) from refresh token."""
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise UnauthorizedError("Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise UnauthorizedError("Refresh token required")
    sub = payload.get("sub")
    role = payload.get("role")
    if not sub or not role:
        raise UnauthorizedError("Invalid token payload")
    user = await get_user_by_id(sub)
    if not user or user.disabled:
        raise UnauthorizedError("User not found or disabled")
    settings = get_settings()
    access = create_access_token(subject=sub, role=role)
    new_refresh = create_refresh_token(subject=sub, role=role)
    return Token(
        access_token=access,
        refresh_token=new_refresh,
        expires_in_seconds=settings.access_token_expire_minutes * 60,
    )


async def create_user(data: UserCreate) -> UserInDB:
    """Create a new user (registration). Email must be unique."""
    existing = await get_user_by_email(data.email)
    if existing:
        raise ValueError("Email already registered")
    internal = UserCreateInternal(
        **data.model_dump(),
        hashed_password=get_password_hash(data.password),
    )
    col = get_user_collection()
    doc = {
        "email": internal.email.lower(),
        "hashed_password": internal.hashed_password,
        "role": internal.role,
        "full_name": internal.full_name,
        "disabled": False,
    }
    result = await col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return UserInDB(**doc)
