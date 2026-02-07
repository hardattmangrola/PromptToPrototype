"""Auth-related request/response schemas."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="JWT refresh token")


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: Optional[int] = None


class TokenPayload(BaseModel):
    sub: str
    role: str
    type: str  # "access" | "refresh"
    exp: int
    iat: int


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    full_name: Optional[str] = None
