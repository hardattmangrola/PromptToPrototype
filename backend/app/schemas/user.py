"""User creation and internal schemas."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(patient|doctor)$")
    full_name: Optional[str] = None


class UserCreateInternal(UserCreate):
    """Internal schema with hashed password (set by service)."""
    hashed_password: str
