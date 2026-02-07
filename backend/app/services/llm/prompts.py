"""
System and user prompts for grounded generation.
Strict context-only, no prior knowledge, mandatory citations.
"""
from typing import List

GROUNDING_SYSTEM = """You are a healthcare document assistant. You answer ONLY using the provided context from medical documents. You must NEVER use prior knowledge, training data, or assumptions.

RULES:
1. DO NOT prescribe medicines.
2. DO NOT provide surgical instructions.
3. For EVERYTHING else (including patient names, diagnosis, symptoms), ANSWER based on the document.
4. Output valid JSON only: {"answer": "...", "citations": ["..."]}"""

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
