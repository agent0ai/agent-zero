"""
Utilities to normalize LLM replies before browser-use parses them into AgentOutput.

Some models (e.g. via OpenRouter) emit extra JSON keys such as "" : "", which
Pydantic rejects as extra_forbidden on strict action union members.
"""

from __future__ import annotations

from typing import Any

from helpers import dirty_json


def deep_strip_empty_string_keys(obj: Any) -> Any:
    """
    Recursively remove dict entries whose key is the empty string.

    Browser-use action objects must be discriminated unions with a single
    action key; spurious "" keys break validation for every union variant.
    """
    if isinstance(obj, dict):
        return {
            k: deep_strip_empty_string_keys(v)
            for k, v in obj.items()
            if k != ""
        }
    if isinstance(obj, list):
        return [deep_strip_empty_string_keys(item) for item in obj]
    return obj


def normalize_parsed_browser_use_output(obj: dict) -> dict:
    """Apply all normalizations safe for a parsed AgentOutput-shaped dict."""
    out = deep_strip_empty_string_keys(obj)
    if not isinstance(out, dict):
        return obj
    return out


def parse_and_sanitize_llm_json(text: str) -> str | None:
    """
    Parse message content and return JSON text safe for AgentOutput parsing.

    Returns None if the string is not a JSON object.
    """
    try:
        obj = dirty_json.parse(text)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    return dirty_json.stringify(normalize_parsed_browser_use_output(obj))


def sanitize_llm_message_content_for_browser_use(content: str | None) -> str | None:
    """
    Best-effort sanitize assistant message content in place for browser-use.

    - If content parses as a dict: strip bad keys and re-serialize.
    - If content is non-JSON or trailing garbage: try dirty_json parse; if dict, sanitize.
    - Otherwise return the original string.
    """
    if content is None:
        return None
    stripped = content.strip()
    if not stripped:
        return content
    sanitized = parse_and_sanitize_llm_json(stripped)
    if sanitized is not None:
        return sanitized
    if not stripped.startswith("{"):
        try:
            obj = dirty_json.parse(stripped)
        except Exception:
            return content
        if isinstance(obj, dict):
            return dirty_json.stringify(normalize_parsed_browser_use_output(obj))
    return content
