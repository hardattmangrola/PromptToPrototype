"""MongoDB document models (internal representation)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserInDB(BaseModel):
    """User document as stored in MongoDB."""

    id: Optional[str] = Field(None, alias="_id")
    email: str
    hashed_password: str
    role: str  # "patient" | "doctor"
    full_name: Optional[str] = None
    disabled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        from_attributes = True


class RefusalLogEntry(BaseModel):
    """Log entry for refused queries (audit trail)."""

    user_id: str
    role: str
    query: str
    reason: str  # e.g. "unsafe_intent", "no_evidence", "validation_failed"
    details: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
