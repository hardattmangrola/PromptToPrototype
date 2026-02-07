"""
Full RAG pipeline: intent -> retrieval -> context -> LLM (parallel) -> validation -> merge.
Strict flow with refusal at any failure; no hallucination tolerance.
"""
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.core.exceptions import RefusalError
from app.services.intent_classifier import ensure_safe_intent
from app.services.retrieval import hybrid_query
from app.services.llm.orchestrator import llm_grounded_generate
from app.services.validation import validate_and_merge
from app.schemas.rag import Citation, RAGResponse, RefusalResponse


async def log_refusal(user_id: str, role: str, query: str, reason: str, details: Optional[dict] = None) -> None:
    """Log refused query for audit."""
    settings = get_settings()
    if not settings.log_refusals:
        return
    try:
        from app.db.mongodb import get_refusal_log_collection
        from app.db.models import RefusalLogEntry
        col = get_refusal_log_collection()
        entry = RefusalLogEntry(
            user_id=user_id,
            role=role,
            query=query[:500],
            reason=reason,
            details=details,
        )
        await col.insert_one(entry.model_dump())
    except Exception:
        pass


async def run_rag(
    query: str,
    *,
    user_id: Optional[str] = None,
    role: Optional[str] = None,
    top_k: Optional[int] = None,
    namespace: Optional[str] = None,
) -> RAGResponse | RefusalResponse:
    """
    Execute the full RAG pipeline. Returns RAGResponse on success or RefusalResponse on refusal.
    """
    settings = get_settings()
    try:
        # Step 1: Intent classification — abort early if unsafe
        ensure_safe_intent(query)
    except RefusalError as e:
        await log_refusal(user_id or "", role or "", query, e.details.get("reason", "unsafe_intent"), e.details)
        return RefusalResponse(
            message=RefusalError.REFUSAL_MESSAGE,
            reason=e.details.get("reason", "unsafe_intent"),
        )

    # Step 2: Hybrid retrieval
    try:
        chunks = await hybrid_query(query, top_k=top_k, namespace=namespace)
    except Exception as e:
        await log_refusal(user_id or "", role or "", query, "retrieval_error", {"error": str(e)})
        return RefusalResponse(message=RefusalError.REFUSAL_MESSAGE, reason="retrieval_error")

    if not chunks:
        await log_refusal(user_id or "", role or "", query, "no_results", None)
        return RefusalResponse(
            message="No relevant information was found in the provided documents for this question.",
            reason="no_evidence",
        )

    # Similarity threshold already applied in hybrid_query; if we got chunks we proceed
    # Step 3 & 4: Context injection + LLM invocation (parallel)
    try:
        groq_out, gemini_out = await llm_grounded_generate(query, chunks)
    except Exception as e:
        await log_refusal(user_id or "", role or "", query, "llm_error", {"error": str(e)})
        return RefusalResponse(message=RefusalError.REFUSAL_MESSAGE, reason="llm_error")

    # Step 5 & 6: Post-generation validation and merge
    try:
        merged = validate_and_merge(groq_out, gemini_out, chunks)
    except RefusalError as e:
        await log_refusal(user_id or "", role or "", query, e.details.get("reason", "validation_failed"), e.details)
        return RefusalResponse(
            message=RefusalError.REFUSAL_MESSAGE,
            reason=e.details.get("reason", "validation_failed"),
        )

    # Step 7: Build response with citations and limitations disclaimer
    citations_out: List[Citation] = []
    for c in merged.get("citations", []):
        if isinstance(c, str):
            parts = c.replace("§", " ").replace("p.", " ").split()
            doc_name = parts[0] if parts else c
            section = None
            page = None
            for i, p in enumerate(parts[1:], 1):
                if p.isdigit():
                    if "p." in c or "p." in c.lower():
                        page = int(p)
                    else:
                        section = p
                    break
            citations_out.append(Citation(doc_name=doc_name, section=section, page=page))
        else:
            citations_out.append(
                Citation(
                    doc_name=c.get("doc_name", ""),
                    section=c.get("section"),
                    page=c.get("page"),
                    snippet=c.get("snippet"),
                )
            )

    sources = [c.get("metadata") or c for c in chunks[:10]]
    limitations = (
        "This answer is based only on the provided documents. It does not constitute medical advice. "
        "Please consult a qualified healthcare professional for personal health decisions."
    )
    return RAGResponse(
        answer=merged["answer"],
        citations=citations_out,
        sources=sources,
        confidence=merged.get("confidence"),
        limitations=limitations,
    )
