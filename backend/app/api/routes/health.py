"""Health and readiness checks."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Liveness: service is running."""
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    """Readiness: DB and critical deps (optional)."""
    try:
        from app.db.mongodb import get_db
        db = get_db()
        # Motor's list_collection_names() returns an awaitable
        collections = await db.list_collection_names()
        return {"status": "ready", "mongodb": "connected"}
    except Exception as e:
        return {"status": "degraded", "mongodb": str(e)}
