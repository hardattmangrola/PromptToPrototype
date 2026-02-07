"""RAG query endpoint. Requires authentication."""
from typing import Union

from fastapi import APIRouter, Depends

from app.core.rbac import require_any_authenticated
from app.schemas.rag import RAGRequest, RAGResponse, RefusalResponse
from app.services.rag_pipeline import run_rag

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post(
    "/query",
    response_model=Union[RAGResponse, RefusalResponse],
    summary="Ask a question (context-only; may refuse)",
)
async def query(
    body: RAGRequest,
    current: dict = Depends(require_any_authenticated()),
):
    """
    Submit a question to the RAG pipeline. Returns either a grounded answer with
    citations or a refusal message. No medical advice or diagnosis; context-only.
    """
    return await run_rag(
        body.query,
        user_id=current.get("sub"),
        role=current.get("role"),
        top_k=body.top_k,
    )
