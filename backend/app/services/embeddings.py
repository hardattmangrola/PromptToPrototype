"""
Dual embedding strategy: sparse (keyword fidelity) + dense (semantic).
Uses Pinecone Inference API for both when available; configurable model names.
"""
from typing import Any, Dict, List, Optional, Tuple

from app.config import get_settings
from app.db.pinecone import get_pinecone_client
import math


def _get_pinecone_client():
    """Return shared Pinecone client (wrapper around helper)."""
    return get_pinecone_client()


def _ensure_fixed_dim(vec: List[float], dim: int) -> List[float]:
    """Trim or pad a dense vector to exactly `dim` length.

    - If vector is longer than dim: truncate.
    - If shorter: pad with zeros.
    """
    if not isinstance(vec, list):
        return []
    if len(vec) == dim:
        return vec
    if len(vec) > dim:
        return vec[:dim]
    # pad
    return vec + [0.0] * (dim - len(vec))


def _extract_dense_values(item: Any) -> List[float]:
    """Extract list of floats from a single embedding item (dict or list)."""
    if isinstance(item, list):
        return item
    if isinstance(item, dict):
        # Pinecone can return {"vector_type": "dense", "values": [...]}
        v = item.get("values") or item.get("embedding")
        if isinstance(v, list):
            return v
    return []


def _parse_dense_result(result: Any, expected: int) -> List[List[float]]:
    """Parse Pinecone inference response into list of dense vectors."""
    out: List[List[float]] = []
    if isinstance(result, list):
        out = [_extract_dense_values(item) for item in result]
    elif isinstance(result, dict):
        if "embeddings" in result:
            out = [_extract_dense_values(e) for e in result["embeddings"]]
        elif "data" in result:
            out = [_extract_dense_values(e) for e in result["data"]]
        elif "values" in result:
            v = result["values"]
            if isinstance(v, list) and v:
                out = v if isinstance(v[0], list) else [v]
        if not out:
            out = [_extract_dense_values(result)]
    else:
        out = [_extract_dense_values(result)]
    settings = get_settings()
    dim = getattr(settings, "dense_embedding_dimension", 512)
    parsed = [x for x in out if isinstance(x, list) and len(x) > 0][:expected]
    return [_ensure_fixed_dim(v, dim) for v in parsed]


async def embed_dense(texts: List[str]) -> List[List[float]]:
    """
    Generate dense embeddings. Tries Pinecone Inference batch, then one-by-one; then local fallback.
    """
    if not texts:
        return []
    settings = get_settings()
    # 1) Try batch
    try:
        pc = _get_pinecone_client()
        result = pc.inference.embed(
            model=settings.dense_embedding_model,
            inputs=texts,
            parameters={"input_type": "passage", "truncate": "END"},
        )
        out = _parse_dense_result(result, len(texts))
        if out:
            # ensure fixed dimension
            dim = getattr(settings, "dense_embedding_dimension", 512)
            return [_ensure_fixed_dim(v, dim) for v in out]
    except Exception:
        pass
    # 2) Try one text at a time (in case batch format differs)
    try:
        pc = _get_pinecone_client()
        out = []
        for t in texts:
            r = pc.inference.embed(
                model=settings.dense_embedding_model,
                inputs=t,
                parameters={"input_type": "passage", "truncate": "END"},
            )
            item = r[0] if isinstance(r, list) and r else r
            v = _extract_dense_values(item)
            if isinstance(v, list) and len(v) > 0:
                out.append(v)
        if out:
            dim = getattr(settings, "dense_embedding_dimension", 512)
            return [_ensure_fixed_dim(v, dim) for v in out[: len(texts)]]
    except Exception:
        pass
    # 3) Local fallback (sentence-transformers) - no Pinecone Inference needed
    return _embed_dense_local(texts)


def _embed_dense_local(texts: List[str]) -> List[List[float]]:
    """Local dense embeddings (sentence-transformers). Default model is 384-dim; normalized to configured dim."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return []
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vecs = model.encode(texts, convert_to_numpy=True)
        out = vecs.tolist()
        # local fallback model is 384-dim by default; but normalize to configured dim
        settings = get_settings()
        dim = getattr(settings, "dense_embedding_dimension", 512)
        return [_ensure_fixed_dim(v, dim) for v in out]
    except Exception:
        return []


def embed_dense_query_local(query: str) -> List[float]:
    """Local dense query embedding. Local model is 384-dim by default; result is normalized to configured dim."""
    out = _embed_dense_local([query])
    return out[0] if out else []


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
        v = _extract_dense_values(result[0])
    elif isinstance(result, dict):
        v = _extract_dense_values(result)
    else:
        v = _extract_dense_values(result)
    dim = getattr(settings, "dense_embedding_dimension", 512)
    return _ensure_fixed_dim(v, dim)


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
    """Normalize Pinecone sparse embed response to list of {indices, values}. Exactly expected_count items."""
    out: List[Dict[str, Any]] = []
    settings = get_settings()
    sparse_dim = getattr(settings, "sparse_embedding_dimension", 512)
    if isinstance(result, dict) and "data" in result:
        result = result["data"]
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                indices = item.get("sparse_indices", item.get("indices", []))
                values = item.get("sparse_values", item.get("values", []))
                # map indices into configured sparse dimension using modulo and aggregate duplicates
                if indices and values:
                    agg = {}
                    for idx, val in zip(indices, values):
                        if not isinstance(idx, int):
                            try:
                                idx = int(idx)
                            except Exception:
                                continue
                        mapped = idx % sparse_dim
                        agg[mapped] = agg.get(mapped, 0.0) + float(val)
                    new_indices = list(agg.keys())
                    new_values = [agg[i] for i in new_indices]
                    out.append({"indices": new_indices, "values": new_values})
                else:
                    out.append({"indices": [], "values": []})
            else:
                out.append({"indices": [], "values": []})
    elif isinstance(result, dict):
        if "sparse_indices" in result and "sparse_values" in result:
            indices = result["sparse_indices"]
            values = result["sparse_values"]
        elif "indices" in result and "values" in result:
            indices = result["indices"]
            values = result["values"]
        else:
            indices = []
            values = []
        if indices and values:
            agg = {}
            for idx, val in zip(indices, values):
                if not isinstance(idx, int):
                    try:
                        idx = int(idx)
                    except Exception:
                        continue
                mapped = idx % sparse_dim
                agg[mapped] = agg.get(mapped, 0.0) + float(val)
            new_indices = list(agg.keys())
            new_values = [agg[i] for i in new_indices]
            out.append({"indices": new_indices, "values": new_values})
        else:
            out.append({"indices": [], "values": []})
    while len(out) < expected_count:
        out.append({"indices": [], "values": []})
    return out[:expected_count]


async def embed_hybrid_query(query: str) -> Tuple[List[float], Dict[str, Any]]:
    """Generate both dense and sparse vectors for a query. Used by retrieval."""
    dense = await embed_dense_query(query)
    sparse = await embed_sparse_query(query)
    return dense, sparse
