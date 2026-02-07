"""
Multi-model orchestration: call Groq and Gemini in parallel with identical context.
Returns both parsed outputs for validation and merging (done in pipeline).
"""
import asyncio
from typing import Any, Dict, List, Tuple

from app.services.llm.prompts import GROUNDING_SYSTEM, build_grounding_user, format_context
from app.services.llm.groq_client import groq_complete, parse_groq_json
from app.services.llm.gemini_client import gemini_complete, parse_gemini_json


async def llm_grounded_generate(
    query: str,
    chunks: List[dict],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Call Groq and Gemini in parallel with same context and grounding instructions.
    Returns (groq_parsed, gemini_parsed) for downstream validation and merge.
    """
    context = format_context(chunks)
    user_msg = build_grounding_user(context, query)

    async def groq_task() -> Dict[str, Any]:
        raw = await groq_complete(GROUNDING_SYSTEM, user_msg)
        return parse_groq_json(raw)

    async def gemini_task() -> Dict[str, Any]:
        raw = await gemini_complete(GROUNDING_SYSTEM, user_msg)
        return parse_gemini_json(raw)

    groq_out, gemini_out = await asyncio.gather(groq_task(), gemini_task())
    return groq_out, gemini_out
