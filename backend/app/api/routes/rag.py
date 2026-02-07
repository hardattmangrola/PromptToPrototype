"""RAG query endpoint. Requires authentication."""
from typing import Optional, Tuple, Union

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from app.core.rbac import require_any_authenticated
from app.db.mongodb import get_user_uploads_collection
from app.schemas.rag import RAGRequest, RAGResponse, RefusalResponse
from app.services.rag_pipeline import run_rag

router = APIRouter(prefix="/rag", tags=["rag"])


async def _resolve_upload_context(upload_id: Optional[str], namespace: Optional[str], user_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (namespace, index_override). index_override is used when upload used a different Pinecone index (e.g. 384-dim)."""
    if upload_id:
        col = get_user_uploads_collection()
        doc = await col.find_one({"upload_id": upload_id, "user_id": user_id})
        if not doc:
            raise HTTPException(404, "Upload not found or access denied")
        return doc.get("namespace"), doc.get("index_used")
    return namespace, None


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
    Submit a question to the RAG pipeline. Optionally scope to an uploaded document
    via namespace or upload_id. Returns grounded answer with citations or refusal.
    For critical questions or out-of-scope: strictly refuses and advises consulting a doctor.
    """
    user_id = current.get("sub") or ""
    namespace, index_override = await _resolve_upload_context(body.upload_id, body.namespace, user_id)
    return await run_rag(
        body.query,
        user_id=user_id,
        role=current.get("role"),
        top_k=body.top_k,
        namespace=namespace,
        index_override=index_override,
    )
