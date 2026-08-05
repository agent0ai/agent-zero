from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

from helpers import files, subagents, tool_policy


FUNCTION_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TOOL_NAME_EXAMPLE_PATTERN = re.compile(
    r"""["']tool_name["']\s*:\s*["']([A-Za-z0-9_-]{1,64})["']"""
)
TOOL_HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.MULTILINE)
TOOL_DECLARATION_PATTERN = re.compile(
    r"^\s*-\s+`([A-Za-z0-9_-]{1,64})`:\s+(args?\b.*)$",
    re.IGNORECASE | re.MULTILINE,
)
SIMPLE_ARGS_PATTERN = re.compile(
    r"^\s*args?:\s*`([A-Za-z_][A-Za-z0-9_-]*)`\s*$",
    re.IGNORECASE | re.MULTILINE,
)
TOOL_PROMPT_PREFIX = "agent.system.tool."
TOOL_PROMPT_SUFFIX = ".md"
MAX_TOOL_DESCRIPTION_CHARS = 1024
TOOL_PROMPT_KWARGS_KEY = "_tool_prompt_kwargs"


def build_responses_function_tools(agent: Any) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Build permissive Responses function tools from A0 tool prompts and MCP schemas."""

    tools: list[dict[str, Any]] = []
    name_map: dict[str, str] = {}

    for tool_name, prompt in _local_tool_prompts(agent):
        if not tool_policy.resolve_tool(agent, tool_name).allowed:
            continue
        native_name = _native_tool_name(tool_name)
        name_map[native_name] = tool_name
        tools.append(
            {
                "type": "function",
                "name": native_name,
                "description": _truncate(
                    tool_policy.tool_prompt_description(
                        prompt,
                        tool_name,
                        fallback=tool_name,
                    )
                ),
                "parameters": _schema_from_prompt(prompt),
            }
        )

    for tool_name, tool in _mcp_tools(agent):
        if not tool_policy.resolve_tool(
            agent,
            tool_name,
            canonical_id=tool_policy.canonical_mcp_id(tool_name),
        ).allowed:
            continue
        native_name = _native_tool_name(tool_name)
        name_map[native_name] = tool_name
        tools.append(
            {
                "type": "function",
                "name": native_name,
                "description": _truncate(str(tool.get("description") or tool_name)),
                "parameters": _schema_from_any(tool.get("input_schema")),
            }
        )

    return _dedupe_tools(tools), name_map


def original_tool_name(native_name: str, name_map: dict[str, str] | None) -> str:
    if not name_map:
        return native_name
    return name_map.get(native_name, native_name)


def _local_tool_prompts(agent: Any) -> list[tuple[str, str]]:
    prompt_dirs = subagents.get_paths(agent, "prompts")
    tool_files = files.get_unique_filenames_in_dirs(
        prompt_dirs, f"{TOOL_PROMPT_PREFIX}*{TOOL_PROMPT_SUFFIX}"
    )
    get_data = getattr(agent, "get_data", None)
    tool_kwargs = get_data(TOOL_PROMPT_KWARGS_KEY) if callable(get_data) else {}
    tool_kwargs = tool_kwargs if isinstance(tool_kwargs, dict) else {}
    result: list[tuple[str, str]] = []
    for tool_file in tool_files:
        basename = os.path.basename(tool_file)
        fallback_name = _tool_name_from_prompt_basename(basename)
        if not fallback_name:
            continue
        try:
            prompt = agent.read_prompt(basename, **tool_kwargs.get(basename, {}))
        except Exception:
            try:
                prompt = files.read_file(tool_file)
            except Exception:
                prompt = ""
        for tool_name in _tool_names_from_prompt(prompt, fallback=fallback_name):
            if _include_local_tool_prompt(agent, tool_name):
                result.append((tool_name, prompt))

    vision_prompt = _vision_tool_prompt(agent)
    if vision_prompt:
        result.append(("vision_load", vision_prompt))
    return result


def _vision_tool_prompt(agent: Any) -> str:
    try:
        from plugins._model_config.helpers.model_config import get_chat_model_config

        if not get_chat_model_config(agent).get("vision", False):
            return ""
        return agent.read_prompt("agent.system.tools_vision.md")
    except Exception:
        return ""


def _include_local_tool_prompt(agent: Any, tool_name: str) -> bool:
    try:
        from plugins._a0_connector.helpers.remote_tool_prompts import (
            should_include_remote_tool_prompt,
        )
    except Exception:
        return True

    return should_include_remote_tool_prompt(agent, tool_name)


def _mcp_tools(agent: Any) -> list[tuple[str, dict[str, Any]]]:
    try:
        import helpers.mcp_handler as mcp_helper

        raw_tools = mcp_helper.MCPConfig.get_for_agent(agent).get_tools()
    except Exception:
        return []

    result: list[tuple[str, dict[str, Any]]] = []
    for entry in raw_tools or []:
        if not isinstance(entry, dict):
            continue
        for tool_name, tool in entry.items():
            if isinstance(tool, dict):
                result.append((str(tool_name), tool))
    return result


def _tool_name_from_prompt_basename(basename: str) -> str:
    if not basename.startswith(TOOL_PROMPT_PREFIX) or not basename.endswith(
        TOOL_PROMPT_SUFFIX
    ):
        return ""
    name = basename[len(TOOL_PROMPT_PREFIX) : -len(TOOL_PROMPT_SUFFIX)]
    if not name or name in {"tools", "tools_vision"}:
        return ""
    return name


def _tool_name_from_prompt(prompt: str, *, fallback: str) -> str:
    for match in TOOL_NAME_EXAMPLE_PATTERN.finditer(prompt or ""):
        name = match.group(1).strip()
        if FUNCTION_NAME_PATTERN.fullmatch(name):
            return name

    for match in TOOL_HEADING_PATTERN.finditer(prompt or ""):
        name = _tool_name_from_heading(match.group(1))
        if name:
            return name

    return fallback


def _tool_names_from_prompt(prompt: str, *, fallback: str) -> list[str]:
    declarations = [
        match.group(1) for match in TOOL_DECLARATION_PATTERN.finditer(prompt or "")
    ]
    if declarations:
        return list(dict.fromkeys(declarations))
    return [_tool_name_from_prompt(prompt, fallback=fallback)]


def _tool_name_from_heading(heading: str) -> str:
    token = (heading or "").strip().split(None, 1)[0] if heading else ""
    name = token.strip("`'\" :")
    if FUNCTION_NAME_PATTERN.fullmatch(name):
        return name
    return ""


def _native_tool_name(tool_name: str) -> str:
    if FUNCTION_NAME_PATTERN.fullmatch(tool_name):
        return tool_name
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", tool_name).strip("_")
    digest = hashlib.sha1(tool_name.encode("utf-8")).hexdigest()[:8]
    native = f"{slug[:52]}_{digest}" if slug else f"a0_tool_{digest}"
    return native[:64]


def _schema_from_prompt(prompt: str) -> dict[str, Any]:
    schema = _schema_from_embedded_json(prompt)
    if schema:
        return schema
    match = SIMPLE_ARGS_PATTERN.search(prompt or "")
    if match:
        return {
            "type": "object",
            "properties": {match.group(1): {"type": "string"}},
            "additionalProperties": True,
        }
    return _permissive_schema()


def _schema_from_embedded_json(prompt: str) -> dict[str, Any]:
    marker = "Input schema for tool_args:"
    index = (prompt or "").find(marker)
    if index == -1:
        return {}
    tail = prompt[index + len(marker) :].strip()
    candidate = _balanced_json_object(tail)
    if not candidate:
        return {}
    try:
        return _schema_from_any(json.loads(candidate))
    except Exception:
        return {}


def _schema_from_any(schema: Any) -> dict[str, Any]:
    if isinstance(schema, dict):
        normalized = dict(schema)
        normalized.setdefault("type", "object")
        if normalized.get("type") == "object" and not isinstance(
            normalized.get("properties"), dict
        ):
            normalized["properties"] = {}
        normalized.setdefault("additionalProperties", True)
        return normalized
    return _permissive_schema()


def _permissive_schema() -> dict[str, Any]:
    return {"type": "object", "properties": {}, "additionalProperties": True}


def _balanced_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return ""
    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return ""


def _dedupe_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for tool in tools:
        name = str(tool.get("name") or "")
        if not name or name in seen:
            continue
        seen.add(name)
        result.append(tool)
    return result


def _truncate(text: str) -> str:
    if len(text) <= MAX_TOOL_DESCRIPTION_CHARS:
        return text
    return text[: MAX_TOOL_DESCRIPTION_CHARS - 3].rstrip() + "..."
