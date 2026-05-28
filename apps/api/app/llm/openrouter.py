"""OpenRouter LLM client using the OpenAI-compatible chat completions API."""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterError(Exception):
    """Raised when the OpenRouter API returns an error."""


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    """Send a chat completion request to OpenRouter and return the assistant text.

    Raises:
        OpenRouterError: if API key is missing, or the API returns an error.
    """
    api_key = settings.openrouter_api_key
    model = settings.openrouter_model

    if not api_key:
        raise OpenRouterError(
            "OPENROUTER_API_KEY is not set. Configure it as a backend environment variable."
        )

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{_OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers={
                    "Authorization": "Bearer " + api_key,
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://velaris.ai",
                    "X-Title": "Velaris AI",
                },
            )
        except httpx.RequestError as exc:
            raise OpenRouterError(f"Network error contacting OpenRouter: {exc}") from exc

    if response.status_code != 200:
        body = response.text[:500]
        raise OpenRouterError(f"OpenRouter returned HTTP {response.status_code}: {body}")

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise OpenRouterError(f"Unexpected OpenRouter response format: {exc}") from exc
