"""FastAPI dependencies: auth, DB, current user."""
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError

security = HTTPBearer(auto_error=False)


async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Validate Bearer JWT and return payload (sub, role, etc.).
    Use when token is in Authorization header.
    """
    if not credentials:
        raise UnauthorizedError("Missing or invalid authorization header")
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise UnauthorizedError("Invalid or expired token")
    if payload.get("type") != "access":
        raise UnauthorizedError("Access token required")
    return payload


async def get_optional_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Same as get_current_user_payload but returns None if no/invalid token."""
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        return payload
    except Exception:
        return None
