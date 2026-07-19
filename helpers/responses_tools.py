from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

from helpers import files, subagents


FUNCTION_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TOOL_NAME_EXAMPLE_PATTERN = re.compile(
    r"""["']tool_name["']\s*:\s*["']([A-Za-z0-9_-]{1,64})["']"""
)
TOOL_HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.MULTILINE)
TOOL_PROMPT_PREFIX = "agent.system.tool."
TOOL_PROMPT_SUFFIX = ".md"
MAX_TOOL_DESCRIPTION_CHARS = 1024


def build_responses_function_tools(agent: Any) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Build permissive Responses function tools from A0 tool prompts and MCP schemas."""

    tools: list[dict[str, Any]] = []
    name_map: dict[str, str] = {}

    for tool_name, prompt in _local_tool_prompts(agent):
        native_name = _native_tool_name(tool_name)
        name_map[native_name] = tool_name
        tools.append(
            {
                "type": "function",
                "name": native_name,
                "description": _description_from_prompt(prompt, fallback=tool_name),
                "parameters": _schema_from_prompt(prompt),
            }
        )

    for tool_name, tool in _mcp_tools(agent):
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
    result: list[tuple[str, str]] = []
    for tool_file in tool_files:
        basename = os.path.basename(tool_file)
        fallback_name = _tool_name_from_prompt_basename(basename)
        if not fallback_name:
            continue
        try:
            prompt = agent.read_prompt(basename)
        except Exception:
            try:
                prompt = files.read_file(tool_file)
            except Exception:
                prompt = ""
        tool_name = _tool_name_from_prompt(prompt, fallback=fallback_name)
        if not _include_local_tool_prompt(agent, tool_name):
            continue
        result.append((tool_name, prompt))
    return result


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

        raw_tools = mcp_helper.MCPConfig.get_instance().get_tools()
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
    if not basename.startswith(TOOL_PROMPT_PREFIX) or not basename.endswith(TOOL_PROMPT_SUFFIX):
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


def _description_from_prompt(prompt: str, *, fallback: str) -> str:
    lines: list[str] = []
    in_fence = False
    for raw_line in (prompt or "").splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line:
            continue
        if line.startswith("#"):
            line = line.lstrip("#").strip()
            if line.lower() == fallback.lower():
                continue
        lines.append(line)
        if sum(len(part) for part in lines) >= MAX_TOOL_DESCRIPTION_CHARS:
            break
    description = " ".join(lines).strip() or fallback
    return _truncate(description)


def _schema_from_prompt(prompt: str) -> dict[str, Any]:
    schema = _schema_from_embedded_json(prompt)
    if schema:
        return schema
    return _schema_from_args_line(prompt)


def _schema_from_embedded_json(prompt: str) -> dict[str, Any]:
    marker = "Input schema for tool_args:"
    index = (prompt or "").find(marker)
    if index == -1:
        return {}
    tail = prompt[index + len(marker) :].strip()
    match = re.search(r"\{(?:[^{}]|(?R))*\}", tail, flags=re.DOTALL) if hasattr(re, "VERSION1") else None
    candidate = match.group(0) if match else _balanced_json_object(tail)
    if not candidate:
        return {}
    try:
        return _schema_from_any(json.loads(candidate))
    except Exception:
        return {}


def _schema_from_args_line(prompt: str) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for line in (prompt or "").splitlines():
        normalized = line.strip()
        if "args:" not in normalized.lower() and "argument:" not in normalized.lower():
            continue
        for name in re.findall(r"`([A-Za-z_][A-Za-z0-9_-]*)`", normalized):
            properties.setdefault(name, {"type": "string"})
    if properties:
        return {
            "type": "object",
            "properties": properties,
            "additionalProperties": True,
        }
    return _permissive_schema()


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
