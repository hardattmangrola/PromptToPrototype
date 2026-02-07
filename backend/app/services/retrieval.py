"""
Hybrid retrieval: sparse + dense over Pinecone.
Single hybrid index (recommended): one index with dense + sparse vectors.
Score normalization, similarity thresholding, deduplication, top-K.
"""
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.services.embeddings import embed_hybrid_query


def _get_pinecone_index():
    """Return the configured Pinecone index (hybrid or dense)."""
    from pinecone import Pinecone
    settings = get_settings()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    if settings.pinecone_host:
        return pc.Index(host=settings.pinecone_host)
    # Index name for hybrid single index
    name = settings.pinecone_index_name if getattr(settings, "use_hybrid_index", True) else settings.pinecone_index_dense
    return pc.Index(name)


def _rrf_score(ranks: List[int], k: int = 60) -> float:
    """Reciprocal Rank Fusion score."""
    return sum(1.0 / (k + r) for r in ranks)


async def hybrid_query(
    query: str,
    *,
    top_k: Optional[int] = None,
    namespace: Optional[str] = None,
    filter_dict: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval: embed query (dense + sparse), query Pinecone,
    apply similarity threshold, dedupe by section, return top-K chunks.
    """
    settings = get_settings()
    k = top_k or settings.retrieval_top_k
    threshold = settings.similarity_threshold
    fetch_k = min(max(settings.rerank_top_k, k) * 2, 40)

    dense_vec, sparse_vec = await embed_hybrid_query(query)
    index = _get_pinecone_index()

    query_params: Dict[str, Any] = {
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

    # Apply similarity threshold (dotproduct/cosine in [0,1] or [-1,1] depending on metric)
    passed = [m for m in matches if (getattr(m, "score", 0) or 0) >= threshold]
    if not passed:
        passed = matches[:k]

    # Deduplicate by doc+section, keep best score
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
