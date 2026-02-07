"""Groq API client for grounded completion."""
import asyncio
import json
from typing import Any, Dict, Optional

from app.config import get_settings


def _groq_sync(api_key: str, model: str, system: str, user: str, temp: float, max_tok: int) -> str:
    from groq import Groq
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temp,
        max_tokens=max_tok,
    )
    return (resp.choices[0].message.content or "").strip()


async def groq_complete(
    system: str,
    user: str,
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Call Groq chat completion. Returns raw response text (expect JSON from prompt).
    Uses AsyncGroq when available, else runs sync client in thread pool.
    """
    settings = get_settings()
    temp = temperature if temperature is not None else settings.llm_temperature
    max_tok = max_tokens or settings.llm_max_tokens
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.groq_api_key)
        resp = await client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temp,
            max_tokens=max_tok,
        )
        return (resp.choices[0].message.content or "").strip()
    except ImportError:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: _groq_sync(
                settings.groq_api_key,
                settings.groq_model,
                system,
                user,
                temp,
                max_tok,
            ),
        )


def parse_groq_json(raw: str) -> Dict[str, Any]:
    """Extract JSON from Groq response (handle markdown code blocks)."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                text = "\n".join(lines[i:])
                break
    if "```" in text:
        text = text.split("```")[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"answer": text, "citations": []}
