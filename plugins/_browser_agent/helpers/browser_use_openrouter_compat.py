from __future__ import annotations

import copy
import json
from typing import Any

def is_openrouter_request(provider: str | None, model_name: str | None) -> bool:
    provider_name = (provider or "").lower()
    model = (model_name or "").lower()
    return provider_name == "openrouter" or model.startswith("openrouter/")


def has_json_schema_response_format(kwargs: dict[str, Any]) -> bool:
    response_format = kwargs.get("response_format")
    return isinstance(response_format, dict) and (
        response_format.get("type") == "json_schema" or "json_schema" in response_format
    )


def should_use_openrouter_prompt_schema_fallback(
    provider: str | None, model_name: str | None, kwargs: dict[str, Any]
) -> bool:
    """
    OpenRouter sometimes routes browser-use structured output through providers
    that reject large compiled grammars. Avoid the hard error entirely by
    downgrading to `json_object` before the first request.
    """
    return is_openrouter_request(provider, model_name) and has_json_schema_response_format(kwargs)


def relax_strict_tool_schemas(tools: Any) -> Any:
    """
    Disable strict tool grammar on fallback while keeping tool definitions intact.
    """
    if not isinstance(tools, list):
        return tools

    relaxed = copy.deepcopy(tools)
    for tool in relaxed:
        if not isinstance(tool, dict):
            continue
        function_spec = tool.get("function")
        if isinstance(function_spec, dict) and function_spec.get("strict") is True:
            function_spec["strict"] = False
    return relaxed


def _schema_hint_text(response_format: dict[str, Any]) -> str | None:
    schema_payload = response_format.get("json_schema")
    if not isinstance(schema_payload, dict):
        return None

    compact_schema = json.dumps(
        schema_payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (
        "Return only a single JSON object with no markdown fences, prose, or extra text. "
        "Follow this schema exactly: "
        f"{compact_schema}"
    )


def prepend_schema_hint_to_messages(
    messages: list[Any], response_format: dict[str, Any]
) -> list[Any]:
    hint = _schema_hint_text(response_format)
    if not hint:
        return list(messages)
    return [{"role": "system", "content": hint}, *list(messages)]


def build_json_object_fallback_request(
    messages: list[Any],
    kwargs: dict[str, Any],
) -> tuple[list[Any], dict[str, Any]] | None:
    """
    Replace strict json_schema with json_object and move schema guidance into the prompt.

    This keeps browser-use's local validation path while avoiding provider-side
    grammar compilation limits on OpenRouter.
    """
    response_format = kwargs.get("response_format")
    if not isinstance(response_format, dict):
        return None

    updated_kwargs = copy.deepcopy(kwargs)
    updated_kwargs["response_format"] = {"type": "json_object"}
    if "tools" in updated_kwargs:
        updated_kwargs["tools"] = relax_strict_tool_schemas(updated_kwargs["tools"])
    updated_messages = prepend_schema_hint_to_messages(messages, response_format)
    return updated_messages, updated_kwargs
