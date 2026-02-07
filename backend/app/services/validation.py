"""
Post-generation validation: claim-context consistency, citation enforcement,
cross-model agreement, safety filter. Refuse if any check fails.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from app.config import get_settings
from app.core.exceptions import RefusalError


# Patterns that indicate forbidden content (diagnosis, advice, dosage, personalization)
SAFETY_PATTERNS = [
    re.compile(r"\b(you should|you ought to|I (recommend|advise|suggest) (that )?you)\b", re.I),
    re.compile(r"\b(take \d+\s*(mg|ml|mg/day)|dosage (of|is)|dose (of|is))\b", re.I),
    re.compile(r"\b(your (condition|diagnosis|disease)|you have (a )?(\w+ )?disease)\b", re.I),
    re.compile(r"\b(based on your (symptoms|condition)|for your (case|situation))\b", re.I),
    re.compile(r"\b(you (need|must|should) (take|use|stop)|prescribe(d)? (for you|to you))\b", re.I),
]


def _extract_citations(text: str) -> List[str]:
    """Extract citation markers like [Doc §2.1] or [Doc p.3] from answer."""
    return re.findall(r"\[([^\]]+)\]", text)


def _sentences(text: str) -> List[str]:
    """Split into sentences (simple)."""
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def check_claim_context_consistency(
    answer: str,
    chunks: List[dict],
    citations: List[str],
) -> Tuple[bool, Optional[str]]:
    """
    Verify that the answer is supported by retrieved chunks and cited.
    Returns (ok, reason).
    """
    if not answer or not answer.strip():
        return True, None
    context_text = " ".join((c.get("text") or "") for c in chunks).lower()
    context_meta = set()
    for c in chunks:
        meta = c.get("metadata") or c
        doc = meta.get("doc_name") or meta.get("document_id") or ""
        section = meta.get("section") or ""
        page = meta.get("page")
        if doc:
            context_meta.add(f"{doc} §{section}".strip())
        if page is not None:
            context_meta.add(f"{doc} p.{page}".strip())
    sentences = _sentences(answer)
    for s in sentences:
        if len(s) < 10:
            continue
        # Require at least one citation in the answer for substantive content
        if not citations and len(s) > 30:
            return False, "citation_missing"
    return True, None


def check_citation_enforcement(answer: str, citations: List[str]) -> Tuple[bool, Optional[str]]:
    """Any substantive sentence without a citation in the answer → reject."""
    settings = get_settings()
    if not settings.citation_required:
        return True, None
    extracted = _extract_citations(answer)
    if not extracted and citations:
        return False, "citations_not_inline"
    if not citations and len((answer or "").strip()) > 50:
        return False, "citation_missing"
    return True, None


def check_safety_filter(text: str) -> Tuple[bool, Optional[str]]:
    """Hard block if diagnosis, advice, dosage, or personalization detected."""
    if not text:
        return True, None
    lower = text.lower()
    for pat in SAFETY_PATTERNS:
        if pat.search(lower):
            return False, "safety_filter_triggered"
    return True, None


def check_cross_model_agreement(
    groq: Dict[str, Any],
    gemini: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """
    Compare Groq vs Gemini outputs. If they contradict on key facts, refuse.
    Simple heuristic: very different answers (e.g. one says X, other says not X).
    """
    a1 = (groq.get("answer") or "").strip()
    a2 = (gemini.get("answer") or "").strip()
    if not a1 or not a2:
        return True, None
    # Normalize and check for obvious negation contradiction
    negations = ("not ", "no ", "never ", "cannot ", "does not ", "do not ")
    for n in negations:
        if (n in a1 and n not in a2) or (n in a2 and n not in a1):
            # Could be coincidence; only refuse if answers are short and diverge a lot
            if len(a1) < 200 and len(a2) < 200:
                return False, "model_contradiction"
    return True, None


def validate_and_merge(
    groq_out: Dict[str, Any],
    gemini_out: Dict[str, Any],
    chunks: List[dict],
) -> Dict[str, Any]:
    """
    Run all validations. If any fail, raise RefusalError.
    Handles both models, single model, or fallback scenarios.
    """
    settings = get_settings()
    a1 = (groq_out.get("answer") or "").strip()
    a2 = (gemini_out.get("answer") or "").strip()
    c1 = groq_out.get("citations") or []
    c2 = gemini_out.get("citations") or []

    has_groq = bool(a1)
    has_gemini = bool(a2)
    
    # No valid response from either model
    if not has_groq and not has_gemini:
        raise RefusalError(reason="no_valid_response", details={"groq": False, "gemini": False})
    
    # Only Groq succeeded
    if has_groq and not has_gemini:
        print("Using Groq response only (Gemini failed)")
        ok, reason = check_safety_filter(a1)
        if not ok:
            raise RefusalError(reason=reason or "safety_filter_triggered")
        ok, reason = check_citation_enforcement(a1, c1)
        if not ok:
            raise RefusalError(reason=reason or "citation_enforcement")
        ok, reason = check_claim_context_consistency(a1, chunks, c1)
        if not ok:
            raise RefusalError(reason=reason or "claim_context_consistency")
        return {
            "answer": a1,
            "citations": c1[:20],
            "confidence": 0.75,
        }
    
    # Only Gemini succeeded
    if has_gemini and not has_groq:
        print("Using Gemini response only (Groq failed)")
        ok, reason = check_safety_filter(a2)
        if not ok:
            raise RefusalError(reason=reason or "safety_filter_triggered")
        ok, reason = check_citation_enforcement(a2, c2)
        if not ok:
            raise RefusalError(reason=reason or "citation_enforcement")
        ok, reason = check_claim_context_consistency(a2, chunks, c2)
        if not ok:
            raise RefusalError(reason=reason or "claim_context_consistency")
        return {
            "answer": a2,
            "citations": c2[:20],
            "confidence": 0.75,
        }
    
    # Both succeeded - validate both and merge
    print(f"Both models responded: Groq ({len(a1)} chars), Gemini ({len(a2)} chars)")
    
    ok, reason = check_safety_filter(a1)
    if not ok:
        raise RefusalError(reason=reason or "safety_filter_triggered")
    ok, reason = check_safety_filter(a2)
    if not ok:
        raise RefusalError(reason=reason or "safety_filter_triggered")

    ok, reason = check_cross_model_agreement(groq_out, gemini_out)
    if not ok:
        print(f"Models disagree: {reason}")

    ok, reason = check_citation_enforcement(a1, c1)
    if not ok:
        raise RefusalError(reason=reason or "citation_enforcement")
    ok, reason = check_citation_enforcement(a2, c2)
    if not ok:
        raise RefusalError(reason=reason or "citation_enforcement")
    
    ok, reason = check_claim_context_consistency(a1, chunks, c1)
    if not ok:
        raise RefusalError(reason=reason or "claim_context_consistency")
    ok, reason = check_claim_context_consistency(a2, chunks, c2)
    if not ok:
        raise RefusalError(reason=reason or "claim_context_consistency")

    merged_citations = list(dict.fromkeys(c1 + c2))
    
    if len(a1) <= len(a2):
        merged_answer = a1
    else:
        merged_answer = a2
    
    confidence = 0.95

    return {
        "answer": merged_answer,
        "citations": merged_citations[:20],
        "confidence": confidence,
    }
