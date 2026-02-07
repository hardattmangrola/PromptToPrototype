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
    If one fails, try the other as fallback. Returns (groq_parsed, gemini_parsed).
    
    Strategy:
    1. Try both in parallel (fast path)
    2. If one fails, retry the failed one sequentially
    3. If both fail after retry, raise error
    """
    context = format_context(chunks)
    user_msg = build_grounding_user(context, query)

    async def groq_task() -> Dict[str, Any]:
        raw = await groq_complete(GROUNDING_SYSTEM, user_msg)
        return parse_groq_json(raw)

    async def gemini_task() -> Dict[str, Any]:
        raw = await gemini_complete(GROUNDING_SYSTEM, user_msg)
        return parse_gemini_json(raw)

    # Try both in parallel first
    results = await asyncio.gather(groq_task(), gemini_task(), return_exceptions=True)
    
    groq_out = results[0] if not isinstance(results[0], Exception) else None
    gemini_out = results[1] if not isinstance(results[1], Exception) else None
    groq_error = results[0] if isinstance(results[0], Exception) else None
    gemini_error = results[1] if isinstance(results[1], Exception) else None
    
    # If one failed, try sequential fallback
    if groq_error and not gemini_out:
        print(f"Groq failed, retrying Gemini: {groq_error}")
        try:
            gemini_out = await gemini_task()
        except Exception as e:
            print(f"Gemini fallback also failed: {e}")
            gemini_out = None
    
    if gemini_error and not groq_out:
        print(f"Gemini failed, retrying Groq: {gemini_error}")
        try:
            groq_out = await groq_task()
        except Exception as e:
            print(f"Groq fallback also failed: {e}")
            groq_out = None
    
    # If still failing, try fallback a second time simultaneously
    if not groq_out and not gemini_out:
        print("Both LLM providers failed initially, attempting aggressive fallback...")
        fallback_results = await asyncio.gather(
            groq_task() if groq_error else asyncio.sleep(0),
            gemini_task() if gemini_error else asyncio.sleep(0),
            return_exceptions=True
        )
        if groq_error:
            groq_out = fallback_results[0] if not isinstance(fallback_results[0], Exception) else None
        if gemini_error:
            gemini_out = fallback_results[1] if not isinstance(fallback_results[1], Exception) else None
    
    # If both still failed after all retries, raise
    if not groq_out and not gemini_out:
        raise RuntimeError(f"Both LLM providers failed. Groq: {groq_error}, Gemini: {gemini_error}")
    
    # Return both (one or both may be populated)
    return groq_out or {}, gemini_out or {}
