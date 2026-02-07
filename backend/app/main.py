"""
Healthcare RAG Backend — FastAPI application entry.
Modular, secure, responsible AI; zero hallucination tolerance.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import AppException, RefusalError
from app.db.mongodb import connect_mongodb, close_mongodb
from app.api.routes import auth, health, rag


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect MongoDB at startup; close at shutdown."""
    await connect_mongodb()
    yield
    await close_mongodb()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="RAG-based Healthcare Information Assistant. Context-only; no medical advice.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, **exc.details},
        )

    @app.exception_handler(RefusalError)
    async def refusal_handler(request, exc: RefusalError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "refused": True,
                "message": exc.message,
                "reason": exc.details.get("reason"),
            },
        )

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(rag.router, prefix=settings.api_prefix)

    return app


app = create_app()
