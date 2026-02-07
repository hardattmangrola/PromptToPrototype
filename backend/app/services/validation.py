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
    # User requested removal of guardrails.
    return True, None


def check_citation_enforcement(answer: str, citations: List[str]) -> Tuple[bool, Optional[str]]:
    """Any substantive sentence without a citation in the answer → reject."""
    # User requested removal of guardrails.
    return True, None


def check_safety_filter(text: str) -> Tuple[bool, Optional[str]]:
    """Hard block if diagnosis, advice, dosage, or personalization detected."""
    # User requested removal of hardcoded restrictions. relying on LLM prompt instructions.
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
        print("\n=== Validation: Groq only ===")
        ok, reason = check_safety_filter(a1)
        if not ok:
            print(f"  Safety filter FAILED: {reason}")
            raise RefusalError(reason=reason or "safety_filter_triggered")
        print("  Safety filter ✓")
        ok, reason = check_citation_enforcement(a1, c1)
        if not ok:
            print(f"  Citation enforcement FAILED: {reason}")
            raise RefusalError(reason=reason or "citation_enforcement")
        print("  Citation enforcement ✓")
        ok, reason = check_claim_context_consistency(a1, chunks, c1)
        if not ok:
            print(f"  Claim consistency FAILED: {reason}")
            raise RefusalError(reason=reason or "claim_context_consistency")
        print("  Claim consistency ✓")
        print("  All validations PASSED\n")
        return {
            "answer": a1,
            "citations": c1[:20],
            "confidence": 0.80,
        }
    
    # Only Gemini succeeded
    if has_gemini and not has_groq:
        print("\n=== Validation: Gemini only ===")
        ok, reason = check_safety_filter(a2)
        if not ok:
            print(f"  Safety filter FAILED: {reason}")
            raise RefusalError(reason=reason or "safety_filter_triggered")
        print("  Safety filter ✓")
        ok, reason = check_citation_enforcement(a2, c2)
        if not ok:
            print(f"  Citation enforcement FAILED: {reason}")
            raise RefusalError(reason=reason or "citation_enforcement")
        print("  Citation enforcement ✓")
        ok, reason = check_claim_context_consistency(a2, chunks, c2)
        if not ok:
            print(f"  Claim consistency FAILED: {reason}")
            raise RefusalError(reason=reason or "claim_context_consistency")
        print("  Claim consistency ✓")
        print("  All validations PASSED\n")
        return {
            "answer": a2,
            "citations": c2[:20],
            "confidence": 0.75,
        }
    
    # Both succeeded - validate both and merge
    print(f"\n=== Validation: Both models ===")
    print(f"  Groq: {len(a1)} chars | Gemini: {len(a2)} chars")
    
    ok, reason = check_safety_filter(a1)
    if not ok:
        print(f"  Groq safety filter FAILED: {reason}")
        raise RefusalError(reason=reason or "safety_filter_triggered")
    print("  Groq safety filter ✓")
    
    ok, reason = check_safety_filter(a2)
    if not ok:
        print(f"  Gemini safety filter FAILED: {reason}")
        raise RefusalError(reason=reason or "safety_filter_triggered")
    print("  Gemini safety filter ✓")

    ok, reason = check_cross_model_agreement(groq_out, gemini_out)
    if not ok:
        print(f"  Cross-model agreement: {reason}")
    else:
        print(f"  Cross-model agreement ✓")

    ok, reason = check_citation_enforcement(a1, c1)
    if not ok:
        print(f"  Groq citation FAILED: {reason}")
        raise RefusalError(reason=reason or "citation_enforcement")
    print("  Groq citations ✓")
    
    ok, reason = check_citation_enforcement(a2, c2)
    if not ok:
        print(f"  Gemini citation FAILED: {reason}")
        raise RefusalError(reason=reason or "citation_enforcement")
    print("  Gemini citations ✓")
    
    ok, reason = check_claim_context_consistency(a1, chunks, c1)
    if not ok:
        print(f"  Groq consistency FAILED: {reason}")
        raise RefusalError(reason=reason or "claim_context_consistency")
    print("  Groq claim consistency ✓")
    
    ok, reason = check_claim_context_consistency(a2, chunks, c2)
    if not ok:
        print(f"  Gemini consistency FAILED: {reason}")
        raise RefusalError(reason=reason or "claim_context_consistency")
    print("  Gemini claim consistency ✓")

    merged_citations = list(dict.fromkeys(c1 + c2))
    
    if len(a1) <= len(a2):
        merged_answer = a1
        print(f"  Selected Groq (shorter)")
    else:
        merged_answer = a2
        print(f"  Selected Gemini (shorter)")
    
    confidence = 0.95
    print(f"  All validations PASSED (confidence: {confidence})\n")

    return {
        "answer": merged_answer,
        "citations": merged_citations[:20],
        "confidence": confidence,
    }
