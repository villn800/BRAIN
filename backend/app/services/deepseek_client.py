from __future__ import annotations

import json
import logging
import re
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


def _parse_deepseek_payload(raw: str) -> dict | None:
    cleaned = raw.strip()
    if not cleaned:
        logger.warning("DeepSeek response contained empty content.")
        return None

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            preview = cleaned[:200].replace("\n", " ")
            logger.warning(
                "DeepSeek response was not valid JSON; no JSON object found. content preview: %s",
                preview,
            )
            return None

        snippet = match.group(0)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError as exc:
            preview = cleaned[:200].replace("\n", " ")
            logger.warning(
                "DeepSeek response was not valid JSON: %s | content preview: %s",
                exc,
                preview,
            )
            return None


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


def _build_prompt(text: str, max_tags: int) -> list[dict[str, str]]:
    system_message = (
        "You are a tagging engine for short texts (tweets). "
        "You MUST respond with only a single JSON object, no markdown, no prose, no code fences. "
        'The JSON keys must be exactly: "tags", "summary", "category". '
        '"tags" must be an array of 3-7 short lowercase strings like "poster design", "productivity". '
        '"summary" must be a single sentence (max ~30 words). '
        '"category" must be a short string or null, e.g. "design", "fitness", or null. '
        'If you cannot tag the text, still respond with: {"tags": [], "summary": "Tagging unavailable.", "category": null}. '
        "Do NOT include any explanation, prefix, suffix, markdown, or backticks. "
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
        response = httpx.post(endpoint, headers=headers, json=payload, timeout=90)
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

    if not isinstance(content, str):
        logger.warning("DeepSeek response contained non-string content.")
        return _FALLBACK_RESULT

    payload = _parse_deepseek_payload(content)
    if payload is None:
        logger.warning("DeepSeek response could not be parsed as JSON.")
        return _FALLBACK_RESULT

    tags = _dedupe_tags(payload.get("tags") or [], max_tags)
    summary = payload.get("summary") or "No summary provided."
    category = payload.get("category") or None
    return DeepSeekTagResult(tags=tags, summary=summary, category=category)
