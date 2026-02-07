"""
System and user prompts for grounded generation.
Strict context-only, no prior knowledge, mandatory citations.
"""
from typing import List

GROUNDING_SYSTEM = """You are a healthcare document assistant. You answer ONLY using the provided context from medical documents. You must NEVER use prior knowledge, training data, or assumptions.

RULES (non-negotiable):
1. Use ONLY information that appears verbatim or is directly inferable from the provided context.
2. If the answer is not in the context, say: "This information is not present in the provided documents."
3. Do not diagnose, recommend treatments, or give medical advice. Only report what the documents state.
4. Avoid certainty language (e.g. "certainly", "definitely"). Prefer "According to the document...", "The guidelines state...".
5. Every factual claim MUST have a citation in the format: [DocName §section] or [DocName p.X].
6. Output valid JSON only, with this exact structure:
{"answer": "your answer text with inline citations", "citations": ["DocA §2.1", "DocB p.3"]}
Do not include any text outside the JSON."""

GROUNDING_USER_TEMPLATE = """Context from provided documents:
---
{context}
---

User question: {query}

Respond with JSON only: {{"answer": "...", "citations": ["..."]}}"""


def build_grounding_user(context: str, query: str) -> str:
    return GROUNDING_USER_TEMPLATE.format(context=context.strip(), query=query.strip())


def format_context(chunks: List[dict]) -> str:
    """Format retrieved chunks as a single context string with source labels."""
    parts = []
    for i, c in enumerate(chunks, 1):
        meta = c.get("metadata") or c
        doc = meta.get("doc_name") or meta.get("document_id") or "Document"
        section = meta.get("section") or ""
        page = meta.get("page") or ""
        label = f"[{doc}"
        if section:
            label += f" §{section}"
        if page:
            label += f" p.{page}"
        label += "]"
        text = c.get("text") or ""
        parts.append(f"{label}\n{text}")
    return "\n\n".join(parts)
