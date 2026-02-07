"""
JWT and password security. Uses bcrypt for hashing and HS256 for JWT.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt

from app.config import get_settings

# bcrypt has a 72-byte limit; truncate to avoid ValueError
BCRYPT_MAX_PASSWORD_BYTES = 72
BCRYPT_ROUNDS = 12


def _truncate_password_for_bcrypt(password: str) -> bytes:
    """Truncate to 72 bytes so bcrypt accepts it. Returns bytes."""
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) <= BCRYPT_MAX_PASSWORD_BYTES:
        return pwd_bytes
    return pwd_bytes[:BCRYPT_MAX_PASSWORD_BYTES]


def get_password_hash(password: str) -> str:
    """Hash password with bcrypt (password truncated to 72 bytes if longer)."""
    pwd_bytes = _truncate_password_for_bcrypt(password)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hash (plain truncated to 72 bytes if longer)."""
    pwd_bytes = _truncate_password_for_bcrypt(plain_password)
    try:
        hash_bytes = hashed_password.encode("utf-8")
    except Exception:
        return False
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


def create_access_token(
    subject: str,
    role: str,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """Create short-lived access JWT."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(subject: str, role: str) -> str:
    """Create long-lived refresh JWT."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": subject,
        "role": role,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT. Raises on invalid/expired."""
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
