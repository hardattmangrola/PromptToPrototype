"""RAG request/response and citation schemas."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    doc_name: str
    section: Optional[str] = None
    page: Optional[int] = None
    snippet: Optional[str] = None


class RAGRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: Optional[int] = Field(None, ge=1, le=20)
    include_metadata: bool = True
    namespace: Optional[str] = Field(None, description="Pinecone namespace (e.g. from document upload)")
    upload_id: Optional[str] = Field(None, description="Resolve to namespace from upload record")


class RAGResponse(BaseModel):
    """Successful grounded answer with citations."""
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list, description="Raw source metadata")
    confidence: Optional[float] = None
    limitations: Optional[str] = Field(
        None,
        description="Clear statement of limitations when applicable",
    )


class RefusalResponse(BaseModel):
    """When the system refuses to answer."""
    refused: bool = True
    message: str = Field(
        default="I cannot answer this question because it requires medical advice or "
                "information not present in the provided documents. "
                "Please consult a qualified healthcare professional."
    )
    reason: Optional[str] = None  # For logging/debug: unsafe_intent, no_evidence, etc.
