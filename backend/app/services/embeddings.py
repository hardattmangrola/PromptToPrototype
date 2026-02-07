"""
Dual embedding strategy: sparse (keyword fidelity) + dense (semantic).
Uses Pinecone Inference API for both when available; configurable model names.
"""
from typing import Any, Dict, List, Optional, Tuple

from app.config import get_settings


def _get_pinecone_client():
    """Lazy import to avoid loading Pinecone before config is ready."""
    from pinecone import Pinecone
    settings = get_settings()
    return Pinecone(api_key=settings.pinecone_api_key)


async def embed_dense(texts: List[str]) -> List[List[float]]:
    """
    Generate dense embeddings (semantic) using configured model.
    Uses Pinecone Inference when available (e.g. llama-text-embed-v2).
    """
    if not texts:
        return []
    settings = get_settings()
    pc = _get_pinecone_client()
    # Pinecone inference: model name from config
    result = pc.inference.embed(
        model=settings.dense_embedding_model,
        inputs=texts,
        parameters={"input_type": "passage", "truncate": "END"},
    )
    # Result shape depends on API; assume list of { "values": [...] }
    if isinstance(result, list):
        return [item.get("values", item) if isinstance(item, dict) else item for item in result]
    if isinstance(result, dict) and "embeddings" in result:
        return [e.get("values", e) for e in result["embeddings"]]
    if isinstance(result, dict) and "values" in result:
        return result["values"]
    return list(result)


async def embed_dense_query(query: str) -> List[float]:
    """Single query dense embedding (input_type=query)."""
    settings = get_settings()
    pc = _get_pinecone_client()
    result = pc.inference.embed(
        model=settings.dense_embedding_model,
        inputs=query,
        parameters={"input_type": "query", "truncate": "END"},
    )
    if isinstance(result, list) and result:
        r = result[0]
        return r.get("values", r) if isinstance(r, dict) else r
    if isinstance(result, dict):
        return result.get("values", result.get("embedding", []))
    return list(result)


async def embed_sparse(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Generate sparse embeddings (keyword fidelity).
    Returns list of { "indices": [...], "values": [...] } for each text.
    """
    if not texts:
        return []
    settings = get_settings()
    pc = _get_pinecone_client()
    result = pc.inference.embed(
        model=settings.sparse_embedding_model,
        inputs=texts,
        parameters={"input_type": "passage", "truncate": "END"},
    )
    return _normalize_sparse_result(result, len(texts))


async def embed_sparse_query(query: str) -> Dict[str, Any]:
    """Single query sparse embedding (input_type=query)."""
    settings = get_settings()
    pc = _get_pinecone_client()
    result = pc.inference.embed(
        model=settings.sparse_embedding_model,
        inputs=query,
        parameters={"input_type": "query", "truncate": "END"},
    )
    out = _normalize_sparse_result(result, 1)
    return out[0] if out else {"indices": [], "values": []}


def _normalize_sparse_result(result: Any, expected_count: int) -> List[Dict[str, Any]]:
    """Normalize Pinecone sparse embed response to list of {indices, values}."""
    out: List[Dict[str, Any]] = []
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                indices = item.get("sparse_indices", item.get("indices", []))
                values = item.get("sparse_values", item.get("values", []))
                out.append({"indices": indices, "values": values})
            else:
                out.append({"indices": [], "values": []})
    elif isinstance(result, dict):
        if "sparse_indices" in result and "sparse_values" in result:
            out.append({
                "indices": result["sparse_indices"],
                "values": result["sparse_values"],
            })
        elif "indices" in result and "values" in result:
            out.append({"indices": result["indices"], "values": result["values"]})
    while len(out) < expected_count:
        out.append({"indices": [], "values": []})
    return out[:expected_count]


async def embed_hybrid_query(query: str) -> Tuple[List[float], Dict[str, Any]]:
    """Generate both dense and sparse vectors for a query. Used by retrieval."""
    dense = await embed_dense_query(query)
    sparse = await embed_sparse_query(query)
    return dense, sparse
