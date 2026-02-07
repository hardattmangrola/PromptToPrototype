"""MongoDB Atlas connection and collection access."""
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.collection import AsyncCollection

from app.config import get_settings

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_mongodb() -> None:
    """Connect to MongoDB Atlas. Call at startup."""
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.mongodb_db_name]
    await _client.admin.command("ping")
    # Ensure unique email for users
    await _db.users.create_index("email", unique=True)


async def close_mongodb() -> None:
    """Close MongoDB connection. Call at shutdown."""
    global _client
    if _client:
        _client.close()
        _client = None


def get_db() -> AsyncIOMotorDatabase:
    """Get database instance. Raises if not connected."""
    if _db is None:
        raise RuntimeError("MongoDB not connected. Call connect_mongodb() at startup.")
    return _db


def get_user_collection() -> AsyncCollection:
    """Users collection (email unique, role, hashed password)."""
    return get_db().users


def get_refusal_log_collection() -> AsyncCollection:
    """Audit log for refused queries."""
    return get_db().refusal_logs
