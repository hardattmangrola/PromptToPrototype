"""MongoDB Atlas connection and collection access."""
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

import logging
from pathlib import Path

from app.config import get_settings


def _ensure_logs_dir() -> Path:
    p = Path(__file__).resolve().parent.parent / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_mongo_logger() -> logging.Logger:
    logdir = _ensure_logs_dir()
    logger = logging.getLogger("app.mongodb")
    if not logger.handlers:
        fh = logging.FileHandler(logdir / "mongodb.log")
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
    return logger

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_mongodb() -> None:
    """Connect to MongoDB Atlas. Call at startup."""
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.mongodb_db_name]
    await _client.admin.command("ping")
    # Log connection success
    try:
        logger = _get_mongo_logger()
        logger.info("MongoDB connected to database '%s'", settings.mongodb_db_name)
    except Exception:
        pass
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


def get_user_collection() -> AsyncIOMotorCollection:
    """Users collection (email unique, role, hashed password)."""
    return get_db().users


def get_refusal_log_collection() -> AsyncIOMotorCollection:
    """Audit log for refused queries."""
    return get_db().refusal_logs


def get_user_uploads_collection() -> AsyncIOMotorCollection:
    """User document uploads (upload_id -> namespace, filename)."""
    return get_db().user_uploads
