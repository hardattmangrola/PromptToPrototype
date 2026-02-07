"""
Hybrid retrieval: dense + sparse over Pinecone.
Supports either a single hybrid index or separate dense and sparse indexes (query both, merge with RRF).
"""
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.services.embeddings import embed_hybrid_query
from app.db.pinecone import get_pinecone_client


def _get_pinecone_index(index_name_override: Optional[str] = None):
    """Return the configured Pinecone index. Use index_name_override for upload index (e.g. different-dim)."""
    settings = get_settings()
    pc = get_pinecone_client()
    if settings.pinecone_host and not index_name_override:
        return pc.Index(host=settings.pinecone_host)
    name = index_name_override or (settings.pinecone_index_name if getattr(settings, "use_hybrid_index", True) else settings.pinecone_index_dense)
    return pc.Index(name)


def _get_dense_index(index_override: Optional[str] = None):
    """Dense index (configured dense embedding dimension)."""
    settings = get_settings()
    pc = get_pinecone_client()
    if index_override:
        return pc.Index(index_override)
    if settings.pinecone_host_dense:
        return pc.Index(host=settings.pinecone_host_dense)
    return _get_pinecone_index(settings.pinecone_index_dense)


def _get_sparse_index(index_override: Optional[str] = None):
    """Sparse index (pinecone-sparse-english-v0)."""
    settings = get_settings()
    pc = get_pinecone_client()
    if index_override:
        return pc.Index(index_override)
    if settings.pinecone_host_sparse:
        return pc.Index(host=settings.pinecone_host_sparse)
    return pc.Index(settings.pinecone_index_sparse)


def _rrf_score(ranks: List[int], k: int = 60) -> float:
    """Reciprocal Rank Fusion score."""
    return sum(1.0 / (k + r) for r in ranks)


async def _query_dual_index(
    dense_vec: List[float],
    sparse_vec: Dict[str, Any],
    namespace: str,
    fetch_k: int,
    threshold: float,
    k: int,
) -> List[Dict[str, Any]]:
    """Query separate dense and sparse indexes, merge with RRF."""
    dense_index = _get_dense_index()
    sparse_index = _get_sparse_index()
    query_params = {"top_k": fetch_k, "include_metadata": True, "namespace": namespace or ""}

    dense_resp = dense_index.query(vector=dense_vec, **query_params)
    sparse_resp = None
    if sparse_vec.get("indices"):
        try:
            sparse_resp = sparse_index.query(sparse_vector=sparse_vec, **query_params)
        except Exception:
            try:
                sparse_resp = sparse_index.query(vector=sparse_vec.get("indices", []), **query_params)
            except Exception:
                pass

    id_to_meta: Dict[str, Dict[str, Any]] = {}
    id_to_rrf: Dict[str, float] = defaultdict(float)
    for rank, m in enumerate((dense_resp.matches or []), start=1):
        mid = getattr(m, "id", "")
        id_to_rrf[mid] += _rrf_score([rank])
        if m.metadata and mid not in id_to_meta:
            id_to_meta[mid] = {
                "id": mid,
                "score": getattr(m, "score", 0) or 0,
                "metadata": dict(m.metadata),
                "text": (m.metadata.get("text") or m.metadata.get("chunk_text") or ""),
            }
    for rank, m in enumerate((sparse_resp.matches or []) if sparse_resp else [], start=1):
        mid = getattr(m, "id", "")
        id_to_rrf[mid] += _rrf_score([rank])
        if m.metadata and mid not in id_to_meta:
            id_to_meta[mid] = {
                "id": mid,
                "score": getattr(m, "score", 0) or 0,
                "metadata": dict(m.metadata),
                "text": (m.metadata.get("text") or m.metadata.get("chunk_text") or ""),
            }
        elif mid in id_to_meta:
            id_to_meta[mid]["score"] = max(id_to_meta[mid].get("score", 0), getattr(m, "score", 0) or 0)

    combined = [(mid, id_to_rrf[mid], id_to_meta[mid]) for mid in id_to_meta if id_to_meta[mid].get("score", 0) >= threshold]
    if not combined:
        combined = [(mid, id_to_rrf[mid], id_to_meta[mid]) for mid in id_to_meta]
    combined.sort(key=lambda x: -x[1])
    return [c[2] for c in combined[:k]]


async def hybrid_query(
    query: str,
    *,
    top_k: Optional[int] = None,
    namespace: Optional[str] = None,
    filter_dict: Optional[Dict[str, Any]] = None,
    index_override: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval: embed query (dense + sparse), query Pinecone.
    When pinecone_host_dense and pinecone_host_sparse are set, queries both and merges with RRF.
    When index_override is set (e.g. 384-dim upload index), use single index + local query embedding.
    """
    settings = get_settings()
    k = top_k or settings.retrieval_top_k
    threshold = settings.similarity_threshold
    fetch_k = min(max(settings.rerank_top_k, k) * 2, 40)

    if index_override:
        from app.services.embeddings import embed_dense_query_local
        dense_vec = embed_dense_query_local(query)
        sparse_vec = {"indices": [], "values": []}
        index = _get_pinecone_index(index_override)
        query_params = {"vector": dense_vec, "top_k": fetch_k, "include_metadata": True, "namespace": namespace or ""}
        if filter_dict:
            query_params["filter"] = filter_dict
        try:
            resp = index.query(**query_params)
            matches = list(resp.matches or [])
        except Exception as e:
            # If index expects a different dimension, try the upload index (if configured)
            settings = get_settings()
            upload_idx = getattr(settings, "pinecone_index_upload", None)
            if upload_idx:
                try:
                    idx2 = _get_pinecone_index(upload_idx)
                    resp = idx2.query(**query_params)
                    matches = list(resp.matches or [])
                except Exception:
                    raise
            else:
                raise
    else:
        dense_vec, sparse_vec = await embed_hybrid_query(query)
        if settings.pinecone_host_dense and settings.pinecone_host_sparse:
            return await _query_dual_index(dense_vec, sparse_vec, namespace or "", fetch_k, threshold, k)
        index = _get_pinecone_index()
        query_params = {
            "vector": dense_vec,
            "top_k": fetch_k,
            "include_metadata": True,
            "namespace": namespace or "",
        }
        if sparse_vec.get("indices"):
            query_params["sparse_vector"] = sparse_vec
        if filter_dict:
            query_params["filter"] = filter_dict
        resp = index.query(**query_params)
        matches = list(resp.matches or [])

    passed = [m for m in matches if (getattr(m, "score", 0) or 0) >= threshold]
    if not passed:
        passed = matches[:k]
    section_best: Dict[str, Any] = {}
    for m in passed:
        meta = dict(m.metadata) if m.metadata else {}
        doc = meta.get("doc_name") or meta.get("document_id") or ""
        section = meta.get("section") or ""
        key = f"{doc}::{section}::{getattr(m, 'id', '')}"
        score = getattr(m, "score", 0) or 0
        if key not in section_best or (section_best[key].get("score") or 0) < score:
            section_best[key] = {
                "id": getattr(m, "id", ""),
                "score": score,
                "metadata": meta,
                "text": meta.get("text") or meta.get("chunk_text") or "",
            }
    deduped = sorted(section_best.values(), key=lambda x: -(x.get("score") or 0))[:k]
    return deduped
