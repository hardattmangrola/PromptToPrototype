"""Database connections and models."""

from app.db.mongodb import get_db, get_user_collection, get_refusal_log_collection
from app.db.models import UserInDB

__all__ = [
    "get_db",
    "get_user_collection",
    "get_refusal_log_collection",
    "UserInDB",
]
