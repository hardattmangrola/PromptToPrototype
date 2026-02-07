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

    groq_out, gemini_out = {}, {}
    results = await asyncio.gather(groq_task(), gemini_task(), return_exceptions=True)
    
    # Handle Groq result
    if isinstance(results[0], Exception):
        print(f"Groq task failed: {results[0]}")
        groq_out = {}
    else:
        groq_out = results[0]

    # Handle Gemini result
    if isinstance(results[1], Exception):
        print(f"Gemini task failed: {results[1]}")
        gemini_out = {}
    else:
        gemini_out = results[1]

    # If both failed, raise an exception or handle it (though validation pipeline might handle empty dicts)
    if not groq_out and not gemini_out:
        raise RuntimeError("Both LLM providers failed to generate a response.")

    return groq_out, gemini_out
