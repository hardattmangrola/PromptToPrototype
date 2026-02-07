"""Document upload: PDF for RAG querying in document scope."""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.exceptions import HTTPException

from app.core.rbac import require_any_authenticated
from app.db.mongodb import get_user_uploads_collection
from app.schemas.document import UploadResponse
from app.services.document_upload_service import process_and_upsert_pdf

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT = ("application/pdf",)


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    current: dict = Depends(require_any_authenticated()),
):
    """
    Upload a medical PDF. Querying will be scoped to this document only.
    If the question is out of scope or critical (e.g. diagnosis/advice), the system will refuse and advise consulting a doctor.
    """
    if file.content_type not in ALLOWED_CONTENT and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")
    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(400, f"File too large (max {MAX_PDF_SIZE // (1024*1024)} MB)")
    user_id = current.get("sub") or ""
    try:
        result = await process_and_upsert_pdf(content, file.filename or "document.pdf", user_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    col = get_user_uploads_collection()
    await col.insert_one({
        "upload_id": result["upload_id"],
        "user_id": user_id,
        "namespace": result["namespace"],
        "filename": result["filename"],
        "chunk_count": result["chunk_count"],
        "index_used": result.get("index_used"),
    })
    return UploadResponse(**result)
