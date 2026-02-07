"""Google Gemini API client for grounded completion."""
import asyncio
import json
from typing import Any, Dict, Optional

from app.config import get_settings


def _gemini_sync(system: str, user: str, temp: float, max_tok: int, model_name: str, api_key: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name,
        generation_config=genai.types.GenerationConfig(
            temperature=temp,
            max_output_tokens=max_tok,
        ),
        system_instruction=system,
    )
    resp = model.generate_content(user)
    if not resp or not resp.text:
        return "{}"
    return resp.text.strip()


async def gemini_complete(
    system: str,
    user: str,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Call Gemini chat completion. Returns raw response text (expect JSON from prompt).
    Runs sync SDK in thread pool to avoid blocking.
    """
    settings = get_settings()
    temp = temperature if temperature is not None else settings.llm_temperature
    max_tok = max_tokens or settings.llm_max_tokens
    try:
        import google.generativeai as genai  # noqa: F401
    except ImportError:
        raise RuntimeError("google-generativeai is required for Gemini. pip install google-generativeai")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: _gemini_sync(system, user, temp, max_tok, settings.gemini_model, settings.gemini_api_key),
    )


def parse_gemini_json(raw: str) -> Dict[str, Any]:
    """Extract JSON from Gemini response."""
    text = raw.strip()
    if "```" in text:
        for part in text.split("```"):
            part = part.strip()
            if part.startswith("{"):
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"answer": text, "citations": []}
