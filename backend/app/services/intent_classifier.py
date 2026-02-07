"""
Question classification and risk management.
Classifies every user query into allowed vs forbidden categories before retrieval.
"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.core.exceptions import RefusalError


class AllowedCategory(str, Enum):
    """Allowed question categories (low/medium risk)."""
    FACTUAL_LOOKUP = "factual_lookup"
    DEFINITIONS = "definitions"
    GUIDELINE_NAVIGATION = "guideline_navigation"
    COMPARISONS_DOC = "comparisons_doc"
    ELIGIBILITY_CRITERIA = "eligibility_criteria"
    SUMMARIZATION = "summarization"
    CITATION_TRACEABILITY = "citation_traceability"


class ForbiddenCategory(str, Enum):
    """Forbidden categories - must refuse."""
    DIAGNOSIS = "diagnosis"
    PERSONALIZED_TREATMENT = "personalized_treatment"
    MEDICAL_ADVICE = "medical_advice"
    EXTERNAL_KNOWLEDGE = "external_knowledge"
    UNKNOWN_HIGH_RISK = "unknown_high_risk"


@dataclass
class ClassificationResult:
    allowed: bool
    category: Optional[AllowedCategory] = None
    forbidden_category: Optional[ForbiddenCategory] = None
    reason: Optional[str] = None


# Patterns and keywords for forbidden intents (critical risk)
FORBIDDEN_PATTERNS = [
    (ForbiddenCategory.DIAGNOSIS, re.compile(
        r"\b(what (disease|condition|illness|wrong with me|do i have)|diagnos(e|is|ed)|"
        r"do i have|symptoms suggest|could i have|do i suffer from)\b",
        re.I,
    )),
    (ForbiddenCategory.PERSONALIZED_TREATMENT, re.compile(
        r"\b(what (should i take|medication|drug|treatment) (for me|i take)|"
        r"recommend (me|for me)|prescribe|dosage for me|how much should i (take|use))\b",
        re.I,
    )),
    (ForbiddenCategory.MEDICAL_ADVICE, re.compile(
        r"\b(is (this|it) (safe|ok|okay) for me|can i take|should i (take|use|stop)|"
        r"medical advice|advise me|tell me what to do|what do you recommend)\b",
        re.I,
    )),
    (ForbiddenCategory.EXTERNAL_KNOWLEDGE, re.compile(
        r"\b(best treatment (globally|in the world|generally)|"
        r"latest (research|studies)|outside (the )?document|not in (the )?document)\b",
        re.I,
    )),
]

# Optional: weak signals for allowed categories (used if no forbidden match)
ALLOWED_SIGNALS = {
    AllowedCategory.FACTUAL_LOOKUP: re.compile(
        r"\b(what (is|are|does)|when|where|how (many|much)|which (document|section)|"
        r"according to (the )?document)\b", re.I
    ),
    AllowedCategory.DEFINITIONS: re.compile(
        r"\b(define|definition|meaning of|what does .+ mean|explain the term)\b", re.I
    ),
    AllowedCategory.GUIDELINE_NAVIGATION: re.compile(
        r"\b(step|workflow|process|procedure|how to (apply|follow)|guideline)\b", re.I
    ),
    AllowedCategory.ELIGIBILITY_CRITERIA: re.compile(
        r"\b(eligibility|criteria|inclusion|exclusion|threshold|qualify)\b", re.I
    ),
    AllowedCategory.SUMMARIZATION: re.compile(
        r"\b(summar(y|ize|ise)|overview|brief(ly)|condense)\b", re.I
    ),
    AllowedCategory.CITATION_TRACEABILITY: re.compile(
        r"\b(source|cite|citation|where (is it|does it say)|which (page|section))\b", re.I
    ),
}


def classify_query(query: str) -> ClassificationResult:
    """
    Classify user query into allowed or forbidden category.
    Forbidden takes precedence; otherwise default to allowed (factual_lookup) with optional refinement.
    """
    query = (query or "").strip()
    if not query:
        return ClassificationResult(
            allowed=False,
            forbidden_category=ForbiddenCategory.UNKNOWN_HIGH_RISK,
            reason="empty_query",
        )

    # Check forbidden first
    for category, pattern in FORBIDDEN_PATTERNS:
        if pattern.search(query):
            return ClassificationResult(
                allowed=False,
                forbidden_category=category,
                reason=f"forbidden_{category.value}",
            )

    # Refine allowed category if possible
    for allowed_cat, pattern in ALLOWED_SIGNALS.items():
        if pattern.search(query):
            return ClassificationResult(allowed=True, category=allowed_cat)
    # Default: allow as factual lookup (retrieval + citation will enforce grounding)
    return ClassificationResult(allowed=True, category=AllowedCategory.FACTUAL_LOOKUP)


def ensure_safe_intent(query: str) -> None:
    """
    Classify query and raise RefusalError if forbidden.
    Call this at the start of the RAG pipeline.
    """
    result = classify_query(query)
    if not result.allowed:
        raise RefusalError(
            reason=result.reason or result.forbidden_category.value,
            details={"forbidden_category": result.forbidden_category.value if result.forbidden_category else None},
        )
