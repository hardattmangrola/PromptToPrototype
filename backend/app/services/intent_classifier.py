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
# NOTE: Patterns must be SPECIFIC to avoid false positives on innocent factual questions.
# "What is the patient name?" is ALLOWED (factual lookup).
# "What should I take?" is FORBIDDEN (personalized treatment).
FORBIDDEN_PATTERNS = [
    # Diagnosis: must ask about THEIR condition
    (ForbiddenCategory.DIAGNOSIS, re.compile(
        r"\b(do i (have|suffer)|what (is|do i) (have|got)|diagnose (me|my)|my diagnosis)\b",
        re.I,
    )),
    # Personalized treatment: must ask about THEIR care
    (ForbiddenCategory.PERSONALIZED_TREATMENT, re.compile(
        r"\b(what (should i|can i|do i) (take|use|do)|for (me|my (condition|case|situation))|prescribe (me|to me)|dosage for (me|my)|my treatment|medication for (me|my))\b",
        re.I,
    )),
    # Medical advice: must ask for personal guidance
    (ForbiddenCategory.MEDICAL_ADVICE, re.compile(
        r"\b(is (this|it|that) (safe|ok|okay) for (me|you)|should i (take|use|stop|do)|what should i do|can i safely|advise (me|you)|you (should|must|recommend)|tell (me|you) what to do)\b",
        re.I,
    )),
    # External knowledge: must explicitly reference outside doc
    (ForbiddenCategory.EXTERNAL_KNOWLEDGE, re.compile(
        r"\b(best treatment (globally|in the world|generally|elsewhere)|latest (research|studies|clinical|findings)|outside (the )?document|not in (the )?document|beyond|what do (you|I) think)\b",
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
