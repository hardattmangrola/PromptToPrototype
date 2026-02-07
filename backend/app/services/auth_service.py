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
    """Verify credentials and return user, or None if invalid. Raises specific errors for debugging."""
    if not email or not password:
        return None
    user = await get_user_by_email(email)
    if not user:
        return None
    if user.disabled:
        return None  # User exists but is disabled
    if not verify_password(password, user.hashed_password):
        return None  # Password mismatch
    return user


async def login_for_tokens(email: str, password: str) -> Token:
    """Authenticate and return access + refresh tokens. Validates input and user state."""
    # Input validation
    if not email or not email.strip():
        raise UnauthorizedError("Email is required")
    if not password or not password.strip():
        raise UnauthorizedError("Password is required")
    
    email = email.strip().lower()
    
    # Check if user exists
    user_exists = await get_user_by_email(email)
    if not user_exists:
        raise UnauthorizedError("User not found. Please register first.")
    
    # Check if disabled
    if user_exists.disabled:
        raise UnauthorizedError("Account is disabled. Contact support.")
    
    # Authenticate
    user = await authenticate_user(email, password)
    if not user:
        raise UnauthorizedError("Invalid password. Please try again.")
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
    """Create a new user (registration). Validates input and ensures email uniqueness."""
    # Validate email
    if not data.email or not data.email.strip():
        raise ValueError("Email is required")
    
    # Validate password
    if not data.password or len(data.password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    # Validate role
    if data.role not in ["patient", "doctor"]:
        raise ValueError("Role must be 'patient' or 'doctor'")
    
    # Validate full_name if provided
    if data.full_name is not None and len(data.full_name.strip()) == 0:
        raise ValueError("Full name cannot be empty if provided")
    
    # Check if email already exists
    email_lower = data.email.lower().strip()
    existing = await get_user_by_email(email_lower)
    if existing:
        raise ValueError("Email already registered. Please login or use a different email.")
    
    # Create user document
    internal = UserCreateInternal(
        **data.model_dump(exclude={"email"}),
        email=email_lower,
        hashed_password=get_password_hash(data.password),
    )
    col = get_user_collection()
    doc = {
        "email": internal.email,
        "hashed_password": internal.hashed_password,
        "role": internal.role,
        "full_name": (internal.full_name or "").strip() or None,
        "disabled": False,
    }
    result = await col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return UserInDB(**doc)
