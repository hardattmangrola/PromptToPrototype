"""
Application configuration. All settings loaded from environment variables.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env path relative to backend folder (parent of app/)
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Healthcare RAG Backend"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # MongoDB Atlas
    mongodb_uri: str = Field(..., description="MongoDB Atlas connection string")
    mongodb_db_name: str = "healthcare_rag"

    # JWT
    jwt_secret_key: str = Field(..., description="Secret for JWT signing")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Pinecone (separate dense + sparse indexes)
    pinecone_api_key: str = Field(..., description="Pinecone API key")
    pinecone_environment: Optional[str] = None
    pinecone_index_name: str = "healthcare-hybrid"
    pinecone_index_dense: str = "healthcare-dense"
    pinecone_index_sparse: str = "healthcare-sparse"
    pinecone_host: Optional[str] = None  # Legacy: single hybrid host
    pinecone_host_dense: Optional[str] = None  # e.g. https://healthcare-dense-xxx.svc.region.pinecone.io
    pinecone_host_sparse: Optional[str] = None  # e.g. https://healthcare-sparse-xxx.svc.region.pinecone.io
    pinecone_index_upload: Optional[str] = None  # Optional separate upload index (use if local fallback produced different dim)
    use_hybrid_index: bool = False  # True = single index; False = use separate dense + sparse indexes

    # Embeddings (both dense + sparse will be normalized to this dimension)
    dense_embedding_model: str = "llama-text-embed-v2"
    dense_embedding_dimension: int = 512
    sparse_embedding_model: str = "pinecone-sparse-english-v0"
    sparse_embedding_dimension: int = 512

    # Retrieval
    retrieval_top_k: int = 10
    similarity_threshold: float = 0.65
    rerank_top_k: int = 5

    # LLM
    groq_api_key: str = Field(..., description="Groq API key")
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = "gemini-1.5-flash"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024

    # Safety & validation
    merge_confidence_threshold: float = 0.7
    citation_required: bool = False
    log_refusals: bool = True


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
