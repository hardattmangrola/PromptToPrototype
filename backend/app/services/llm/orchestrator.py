"""
Parallel LLM orchestration with intelligent fallback.
Strategy: Gemini-primary (more capable), Groq-fallback (free, reliable).

Handles graceful degradation if either fails.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

from app.config import get_settings
from app.services.llm.gemini_client import gemini_complete
from app.services.llm.groq_client import groq_complete_async, GroqAsyncError

logger = logging.getLogger("app.llm")


async def llm_grounded_generate(query: str, chunks: list[dict]) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Orchestrate dual LLM generation: Gemini-primary + Groq-fallback.
    
    Returns (gemini_out, groq_out) where each is:
      {"answer": str, "citations": list[str]}
    
    Strategy:
      1. Try Gemini (primary) + Groq (secondary) in parallel
      2. If Gemini fails (quota, auth, rate limit), skip it (Groq is fallback)
      3. If Groq fails on first attempt, retry once
      4. Require Groq success; Gemini is optional (nice-to-have for cross-model validation)
    """
    settings = get_settings()
    context_text = "\n\n".join(c.get("text", "") for c in chunks)
    
    print(f"\n=== LLM Orchestration (Gemini-primary + Groq-fallback) ===")
    print(f"  Query: {query[:80]}...")
    print(f"  Context: {len(context_text)} chars across {len(chunks)} chunks")
    
    # Define tasks
    async def gemini_task():
        try:
            result = await gemini_complete(query, context_text)
            if result.get("answer"):
                print(f"  ✓ Gemini: {len(result['answer'])} chars")
                return result
            else:
                print(f"  ⚠ Gemini: empty response")
                return None
        except Exception as e:
            error_msg = str(e)
            # Gracefully skip Gemini if quota/auth/rate limit
            if "429" in error_msg or "quota" in error_msg.lower() or "403" in error_msg:
                print(f"  ⚠ Gemini: quota/auth error (skipping, using Groq alone)")
                return None
            else:
                print(f"  ✗ Gemini: unexpected error: {error_msg}")
                return None
    
    async def groq_task():
        try:
            result = await groq_complete_async(query, context_text)
            if result.get("answer"):
                print(f"  ✓ Groq: {len(result['answer'])} chars")
                return result
            else:
                print(f"  ⚠ Groq: empty response")
                return None
        except GroqAsyncError as e:
            print(f"  ✗ Groq: {str(e)}")
            return None
        except Exception as e:
            print(f"  ✗ Groq: unexpected error: {str(e)}")
            return None
    
    # Run in parallel
    results = await asyncio.gather(gemini_task(), groq_task(), return_exceptions=True)
    gemini_out = results[0] if not isinstance(results[0], Exception) else None
    groq_out = results[1] if not isinstance(results[1], Exception) else None
    
    # If Groq failed on first try, retry once
    if not groq_out:
        print(f"  → Retrying Groq...")
        try:
            groq_out = await groq_complete_async(query, context_text)
            if groq_out and groq_out.get("answer"):
                print(f"  ✓ Groq retry: {len(groq_out['answer'])} chars")
        except Exception as e:
            print(f"  ✗ Groq retry failed: {str(e)}")
    
    # Require Groq success
    if not groq_out or not groq_out.get("answer"):
        raise RuntimeError("Groq LLM failed (primary fallback)")
    
    # Return: Gemini + Groq (Gemini first for backward compatibility with validation logic)
    print(f"  → Strategy: using Groq {'+ Gemini cross-validation' if gemini_out else '(Gemini unavailable)'}")
    return gemini_out or {}, groq_out
