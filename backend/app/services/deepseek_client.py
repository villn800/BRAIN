from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import List

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class DeepSeekTagResult:
    tags: List[str]
    summary: str
    category: str | None = None


_FALLBACK_RESULT = DeepSeekTagResult(tags=[], summary="Tagging unavailable.", category=None)


def _dedupe_tags(tags: list[str], max_tags: int) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for tag in tags:
        if not isinstance(tag, str):
            continue
        name = tag.strip()
        key = name.lower()
        if not name or key in seen:
            continue
        seen.add(key)
        cleaned.append(name)
        if len(cleaned) >= max_tags:
            break
    return cleaned


def _parse_response(content: str, max_tags: int) -> DeepSeekTagResult:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning("DeepSeek response was not valid JSON: %s", exc)
        return _FALLBACK_RESULT

    tags = _dedupe_tags(payload.get("tags") or [], max_tags)
    summary = payload.get("summary") or "No summary provided."
    category = payload.get("category") or None
    return DeepSeekTagResult(tags=tags, summary=summary, category=category)


def _build_prompt(text: str, max_tags: int) -> list[dict[str, str]]:
    system_message = (
        "You are a tagging assistant for an inspiration vault. "
        "Given tweet content, return STRICT JSON with 3-7 concise, user-visible tags, a short one-line summary (<=30 words), "
        "and an optional coarse category. "
        "Do not include any prose outside the JSON. "
        "Schema: {\"tags\": [\"tag1\", \"tag2\"], \"summary\": \"...\", \"category\": \"optional\"}. "
        f"Limit tags to at most {max_tags}."
    )
    user_message = f"Tweet text:\n{text.strip()}"
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def generate_tags_for_text(text: str, *, max_tags: int = 6) -> DeepSeekTagResult:
    """Call DeepSeek to generate tags/summary for the provided text."""
    settings = get_settings()
    if not settings.DEEPSEEK_API_KEY:
        logger.error("DeepSeek API key is missing; skipping tag generation.")
        return _FALLBACK_RESULT

    base_url = (settings.DEEPSEEK_API_BASE_URL or "").rstrip("/")
    endpoint = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": _build_prompt(text, max_tags),
        "temperature": 0.3,
    }

    try:
        response = httpx.post(endpoint, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("DeepSeek request failed: %s", exc)
        return _FALLBACK_RESULT

    try:
        data = response.json()
    except ValueError as exc:
        logger.warning("DeepSeek response could not be decoded: %s", exc)
        return _FALLBACK_RESULT

    try:
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
    except (AttributeError, IndexError, TypeError) as exc:
        logger.warning("DeepSeek response missing expected structure: %s", exc)
        return _FALLBACK_RESULT

    if not isinstance(content, str) or not content.strip():
        logger.warning("DeepSeek response contained empty content.")
        return _FALLBACK_RESULT

    return _parse_response(content, max_tags)
