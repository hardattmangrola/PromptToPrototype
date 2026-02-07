"""Pinecone client helper with connection logging."""
from pathlib import Path
import logging
from typing import Optional

from app.config import get_settings


def _ensure_logs_dir() -> Path:
    p = Path(__file__).resolve().parent.parent / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_logger(name: str, filename: str) -> logging.Logger:
    logdir = _ensure_logs_dir()
    logger = logging.getLogger(f"app.{name}")
    if not logger.handlers:
        fh = logging.FileHandler(logdir / filename)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
    return logger


def get_pinecone_client() -> object:
    """Return a Pinecone client and log connection success/failure to logs/pinecone.log.

    This is a lazy helper so modules can import without immediately contacting Pinecone.
    """
    settings = get_settings()
    logger = _get_logger("pinecone", "pinecone.log")
    try:
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
        # Quick smoke-check: list indexes (may raise if key/host invalid)
        try:
            _ = pc.list_indexes()
        except Exception:
            # still consider client created but log warning
            logger.warning("Pinecone client created but list_indexes() failed")
        else:
            logger.info("Pinecone client created and list_indexes() succeeded")
        return pc
    except Exception as e:
        logger.exception(f"Failed to create Pinecone client: {e}")
        raise
