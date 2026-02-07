"""
Process uploaded PDF: semantic chunking, dual embedding, Pinecone upsert.
Enforces strict medical safety, traceability, and auditability constraints.

Pipeline:
  1. Extract & semantically chunk PDF (preserve original text)
  2. Generate dense embedding (semantic similarity)
  3. Generate sparse embedding (medical terminology matching)
  4. Enrich metadata (page, section, chunk_type, timestamp)
  5. Upsert to Pinecone with full traceability
"""
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from app.config import get_settings
from app.services.pdf_service import extract_and_chunk_pdf
from app.services.embeddings import embed_dense, embed_sparse
from app.db.pinecone import get_pinecone_client
import logging

logger = logging.getLogger("app.document_upload")


def _get_dense_index(index_override: Optional[str] = None):
    settings = get_settings()
    pc = get_pinecone_client()
    if index_override:
        return pc.Index(index_override)
    if settings.pinecone_host_dense:
        return pc.Index(host=settings.pinecone_host_dense)
    return pc.Index(settings.pinecone_index_dense)


def _get_sparse_index(index_override: Optional[str] = None):
    settings = get_settings()
    pc = get_pinecone_client()
    if index_override:
        return pc.Index(index_override)
    if settings.pinecone_host_sparse:
        return pc.Index(host=settings.pinecone_host_sparse)
    return pc.Index(settings.pinecone_index_sparse)


def _get_pinecone_index(index_name_override: Optional[str] = None):
    settings = get_settings()
    pc = get_pinecone_client()
    if settings.pinecone_host and not index_name_override:
        return pc.Index(host=settings.pinecone_host)
    name = index_name_override or settings.pinecone_index_name
    return pc.Index(name)


def _use_dual_index() -> bool:
    s = get_settings()
    return bool(s.pinecone_host_dense and s.pinecone_host_sparse)


async def process_and_upsert_pdf(
    file_content: bytes,
    filename: str,
    user_id: str,
) -> dict:
    """
    Chunk PDF, embed (dense + sparse), upsert to Pinecone only. No local storage.
    Returns upload_id, namespace, filename, chunk_count. Raises on failure.
    """
    chunks = extract_and_chunk_pdf(file_content, filename or "document.pdf")
    if not chunks:
        raise ValueError("PDF has no extractable text")

    settings = get_settings()
    upload_id = str(uuid.uuid4())
    namespace = f"user_{user_id}_{upload_id}".replace("-", "_")[:255]

    texts = [c["text"] for c in chunks]
    dense_vecs = await embed_dense(texts)
    sparse_vecs = await embed_sparse(texts)
    n = min(len(dense_vecs), len(chunks))
    if n == 0:
        raise ValueError("No valid embeddings returned; check embedding API and indexes")
    while len(sparse_vecs) < n:
        sparse_vecs.append({"indices": [], "values": []})
    sparse_vecs = sparse_vecs[:n]
    chunks = chunks[:n]
    dense_vecs = dense_vecs[:n]

    # If embeddings came back at a different dimension than configured, require an upload index
    index_used: Optional[str] = None
    dense_dim = len(dense_vecs[0]) if dense_vecs else 0
    if dense_dim != getattr(settings, "dense_embedding_dimension", 512):
        index_used = getattr(settings, "pinecone_index_upload", None)
        if not index_used:
            raise ValueError(
                f"Embeddings are {dense_dim}-dimensional (mismatch). "
                f"Set PINECONE_INDEX_UPLOAD to a {dense_dim}-dim Pinecone index in .env, "
                f"or ensure Pinecone Inference returns {getattr(settings, 'dense_embedding_dimension', 512)}-dim embeddings (dense_embedding_model)."
            )

    batch_size = 100
    meta_truncate = 50_000
    use_dual = _use_dual_index() and not index_used
    upload_timestamp = datetime.now(timezone.utc).isoformat()

    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_dense = dense_vecs[i : i + batch_size]
        batch_sparse = sparse_vecs[i : i + batch_size]

        if use_dual:
            dense_records = []
            sparse_records = []
            for j, (ch, dv, sv) in enumerate(zip(batch_chunks, batch_dense, batch_sparse)):
                if not dv or not isinstance(dv, list) or len(dv) == 0:
                    continue
                vid = f"{namespace}_{i + j}"
                
                # Enrich metadata with full traceability
                meta = {
                    "text": ch["text"][:meta_truncate],
                    "document_id": upload_id,
                    "document_title": filename,
                    "doc_name": ch["doc_name"],
                    "page_number": ch.get("page"),
                    "section_title": ch.get("section"),
                    "chunk_type": ch.get("chunk_type", "general"),
                    "upload_timestamp": upload_timestamp,
                    "source": "uploaded_pdf",
                }
                
                dense_records.append({"id": vid, "values": dv, "metadata": meta})
                if sv and (sv.get("indices") or sv.get("values")):
                    sparse_records.append({
                        "id": vid,
                        "sparse_values": {"indices": sv.get("indices", []), "values": sv.get("values", [])},
                        "metadata": meta,
                    })
            
            if dense_records:
                try:
                    _get_dense_index().upsert(vectors=dense_records, namespace=namespace)
                    logger.info(f"Upserted {len(dense_records)} dense vectors to namespace {namespace}")
                except Exception as e:
                    # If dimension mismatch, try upload index (if configured)
                    try:
                        settings = get_settings()
                        logger.info("Dense upsert failed: %s. Attempting upload index fallback.", str(e))
                        upload_idx_name = getattr(settings, "pinecone_index_upload", None)
                        if upload_idx_name:
                            _get_dense_index(upload_idx_name).upsert(vectors=dense_records, namespace=namespace)
                            logger.info("Dense upsert succeeded to upload index %s", upload_idx_name)
                        else:
                            raise
                    except Exception:
                        raise
            
            if sparse_records:
                try:
                    _get_sparse_index().upsert(vectors=sparse_records, namespace=namespace)
                    logger.info(f"Upserted {len(sparse_records)} sparse vectors to namespace {namespace}")
                except Exception as e:
                    raise RuntimeError(f"Pinecone sparse index upsert failed: {e}") from e
        else:
            records = []
            for j, (ch, dv, sv) in enumerate(zip(batch_chunks, batch_dense, batch_sparse)):
                if not dv or not isinstance(dv, list) or len(dv) == 0:
                    continue
                vid = f"{namespace}_{i + j}"
                
                # Enrich metadata with full traceability
                meta = {
                    "text": ch["text"][:meta_truncate],
                    "document_id": upload_id,
                    "document_title": filename,
                    "doc_name": ch["doc_name"],
                    "page_number": ch.get("page"),
                    "section_title": ch.get("section"),
                    "chunk_type": ch.get("chunk_type", "general"),
                    "upload_timestamp": upload_timestamp,
                    "source": "uploaded_pdf",
                }
                
                record = {"id": vid, "values": dv, "metadata": meta}
                if sv and (sv.get("indices") or sv.get("values")):
                    record["sparse_values"] = {"indices": sv.get("indices", []), "values": sv.get("values", [])}
                records.append(record)
            
            if records:
                idx = _get_pinecone_index(index_used)
                try:
                    idx.upsert(vectors=records, namespace=namespace)
                    logger.info(f"Upserted {len(records)} hybrid vectors to namespace {namespace}")
                except Exception as e:
                    # If vector dimension mismatch, attempt to fallback to upload index if provided
                    settings = get_settings()
                    upload_idx_name = getattr(settings, "pinecone_index_upload", None)
                    logger.info("Primary upsert failed: %s", str(e))
                    if upload_idx_name and upload_idx_name != (index_used or ""):
                        try:
                            logger.info("Retrying upsert to upload index %s", upload_idx_name)
                            _get_pinecone_index(upload_idx_name).upsert(vectors=records, namespace=namespace)
                            logger.info("Upsert to upload index succeeded")
                        except Exception:
                            raise
                    else:
                        raise

    return {
        "upload_id": upload_id,
        "namespace": namespace,
        "filename": filename or "document.pdf",
        "chunk_count": n,
        "index_used": index_used,
    }
