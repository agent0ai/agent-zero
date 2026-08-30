from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Any

from helpers import files, plugins, subagents
from helpers.errors import RepairableException


PLUGIN_NAME = "_tool_access"
PROMPT_PREFIX = "agent.system.tool."
PROMPT_SUFFIX = ".md"
NON_CONFIGURABLE_TOOLS = frozenset({"response", "vision_load"})


@dataclass(frozen=True)
class ToolPolicyDecision:
    allowed: bool
    tool_id: str
    source: str
    mode: str
    reason: str = ""


def normalize_policy(config: Any) -> dict[str, Any]:
    raw = dict(config) if isinstance(config, dict) else {}
    mode = str(raw.get("mode") or "inherit").strip().lower()
    default = str(raw.get("default") or "allow").strip().lower()
    mcp_default = str(raw.get("mcp_default") or "allow").strip().lower()
    raw["mode"] = "custom" if mode == "custom" else "inherit"
    raw["default"] = "block" if default == "block" else "allow"
    raw["mcp_default"] = "block" if mcp_default == "block" else "allow"
    raw["allowed"] = _normalize_ids(raw.get("allowed"))
    raw["blocked"] = _normalize_ids(raw.get("blocked"))
    return raw


def get_policy(agent: Any) -> dict[str, Any]:
    from helpers import projects

    project_name = projects.get_context_project_name(agent.context) or ""
    profile = str(getattr(agent.config, "profile", "") or "")
    for asset in plugins.find_plugin_assets(
        plugins.CONFIG_FILE_NAME,
        plugin_name=PLUGIN_NAME,
        project_name=project_name,
        agent_profile=profile,
        only_first=False,
    ):
        config = files.read_file_json(asset["path"])
        if not isinstance(config, dict) or not any(
            key in config
            for key in ("mode", "default", "mcp_default", "allowed", "blocked")
        ):
            continue
        policy = normalize_policy(config)
        if policy["mode"] == "custom":
            return policy
    return normalize_policy(plugins.get_default_plugin_config(PLUGIN_NAME))


def get_tool_catalog(agent: Any) -> list[dict[str, Any]]:
    tool_paths = _local_tool_paths(agent)
    descriptions = _tool_descriptions(agent, set(tool_paths))
    catalog: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name, tool_path in tool_paths.items():
        if name in NON_CONFIGURABLE_TOOLS:
            continue
        tool_id, origin = _canonical_from_path(tool_path, name)
        if tool_id in seen:
            continue
        seen.add(tool_id)
        catalog.append(
            {
                "id": tool_id,
                "name": name,
                "label": name.replace("_", " ").title(),
                "origin": origin,
                "description": descriptions.get(name, ""),
                "available": True,
            }
        )

    try:
        from helpers.mcp_handler import MCPConfig

        for item in MCPConfig.get_for_agent(agent).get_tools():
            qualified, tool = next(iter(item.items()))
            tool_id = canonical_mcp_id(qualified)
            if tool_id in seen:
                continue
            server_name, _, tool_name = qualified.partition(".")
            seen.add(tool_id)
            catalog.append(
                {
                    "id": tool_id,
                    "name": qualified,
                    "label": " · ".join(
                        part.replace("_", " ").strip().title()
                        for part in (
                            server_name,
                            str(tool.get("title") or tool.get("name") or tool_name),
                        )
                        if part
                    ),
                    "description": str(tool.get("description") or ""),
                    "origin": f"MCP · {str(tool.get('server') or '').strip()}",
                    "available": True,
                }
            )
    except Exception:
        pass

    policy = get_policy(agent)
    for tool_id in [*policy["allowed"], *policy["blocked"]]:
        if (
            tool_id in seen
            or _tool_name_from_id(tool_id) in NON_CONFIGURABLE_TOOLS
        ):
            continue
        seen.add(tool_id)
        name = _tool_name_from_id(tool_id)
        catalog.append(
            {
                "id": tool_id,
                "name": name,
                "label": name.replace("_", " ").title(),
                "description": "",
                "origin": "Unavailable",
                "available": False,
            }
        )

    catalog.sort(key=lambda item: (item["label"].casefold(), item["id"]))
    return catalog


def canonical_mcp_id(tool_name: str) -> str:
    server, separator, name = str(tool_name or "").partition(".")
    return f"mcp:{server}:{name}" if separator and server and name else ""


def _canonical_tool_id(agent: Any, tool_name: str) -> str:
    if mcp_id := canonical_mcp_id(tool_name):
        try:
            from helpers.mcp_handler import MCPConfig

            if MCPConfig.get_for_agent(agent).has_tool(tool_name):
                return mcp_id
        except Exception:
            pass

    paths = subagents.get_paths(agent, "tools", f"{tool_name}.py")
    path = next((candidate for candidate in paths if files.exists(candidate)), "")
    return _canonical_from_path(path, tool_name)[0] if path else f"local:{tool_name}"


def resolve_tool(
    agent: Any,
    tool_name: str,
    *,
    canonical_id: str = "",
    _policy: dict[str, Any] | None = None,
) -> ToolPolicyDecision:
    tool_id = canonical_id or _canonical_tool_id(agent, tool_name)
    requested = str(tool_name or "").strip()
    name = _tool_name_from_id(tool_id) if requested == tool_id else requested
    if name in NON_CONFIGURABLE_TOOLS:
        source = "framework-required" if name == "response" else "runtime-config"
        return ToolPolicyDecision(True, tool_id, source, "invariant")

    policy = _policy if _policy is not None else get_policy(agent)
    if policy["mode"] != "custom":
        return ToolPolicyDecision(True, tool_id, "inherited", "inherit")

    if tool_id in policy["blocked"]:
        return ToolPolicyDecision(
            False, tool_id, "scoped-policy", "custom", "blocked explicitly"
        )
    if tool_id in policy["allowed"]:
        return ToolPolicyDecision(True, tool_id, "scoped-policy", "custom")

    default_key = "mcp_default" if tool_id.startswith("mcp:") else "default"
    is_allowed = policy[default_key] == "allow"
    return ToolPolicyDecision(
        is_allowed,
        tool_id,
        "scoped-default",
        "custom",
        "blocked by default" if not is_allowed else "",
    )


def ensure_tool_allowed(
    agent: Any,
    tool_name: str,
    *,
    canonical_id: str = "",
) -> ToolPolicyDecision:
    decision = resolve_tool(agent, tool_name, canonical_id=canonical_id)
    if decision.allowed:
        return decision
    profile = str(getattr(getattr(agent, "config", None), "profile", "") or "default")
    raise RepairableException(
        f'Tool "{tool_name}" is blocked for agent profile "{profile}".'
    )


def filter_tool_prompt(agent: Any, prompt_file: str, prompt: str) -> str:
    return filter_tool_prompts(agent, [(prompt_file, prompt)])[0]


def filter_tool_prompts(
    agent: Any, prompts: list[tuple[str, str]]
) -> list[str]:
    policy = get_policy(agent)
    if policy["mode"] != "custom":
        return [prompt for _prompt_file, prompt in prompts]

    known_names = _policy_tool_names(agent, policy)
    prompt_names = {
        name
        for prompt_file, prompt in prompts
        for name in _prompt_tool_names(prompt_file, prompt, known_names)
    }
    allowed_names = {
        name
        for name in known_names | prompt_names
        if resolve_tool(agent, name, _policy=policy).allowed
    }
    return [
        _filter_tool_prompt(prompt_file, prompt, known_names, allowed_names)
        for prompt_file, prompt in prompts
    ]


def _filter_tool_prompt(
    prompt_file: str,
    prompt: str,
    known_names: set[str],
    allowed_names: set[str],
) -> str:
    names = _prompt_tool_names(prompt_file, prompt, known_names)
    if names and not any(name in allowed_names for name in names):
        return ""

    blocked_names = known_names - allowed_names
    if not blocked_names:
        return prompt
    patterns = [
        re.compile(
            rf"(?:`{re.escape(name)}`|[\"']{re.escape(name)}[\"']|"
            rf"(?<![A-Za-z0-9_-]){re.escape(name)}\s+tool\b)",
            re.IGNORECASE,
        )
        for name in sorted(blocked_names, key=len, reverse=True)
    ]
    prompt = re.sub(
        r"^[ \t]*(?P<fence>`{3,}|~{3,})[ \t]*json\b[^\r\n]*\r?\n"
        r".*?^[ \t]*(?P=fence)[ \t]*(?:\r?\n|$)",
        lambda match: (
            ""
            if any(pattern.search(match.group(0)) for pattern in patterns)
            else match.group(0)
        ),
        prompt,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return "".join(
        line
        for line in prompt.splitlines(keepends=True)
        if not any(pattern.search(line) for pattern in patterns)
    )


def _local_tool_paths(agent: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in files.get_unique_filenames_in_dirs(
        subagents.get_paths(agent, "tools"), "*.py"
    ):
        name = os.path.splitext(os.path.basename(path))[0]
        if name not in {"__init__", "unknown"}:
            result[name] = path
    return result


def _policy_tool_names(agent: Any, policy: dict[str, Any]) -> set[str]:
    names = set(_local_tool_paths(agent))
    names.update(
        _tool_name_from_id(tool_id)
        for tool_id in [*policy["allowed"], *policy["blocked"]]
        if not tool_id.startswith("mcp:")
    )
    return names


def _prompt_tool_names(
    prompt_file: str, prompt: str, known_names: set[str]
) -> list[str]:
    fallback = _prompt_name(prompt_file)
    declared = [
        name for name in sorted(known_names) if _prompt_declares_tool(prompt, name)
    ]
    if fallback in known_names:
        return list(dict.fromkeys([fallback, *declared]))
    return declared or ([fallback] if fallback else [])


def _prompt_declares_tool(prompt: str, name: str) -> bool:
    escaped = re.escape(name)
    return bool(
        re.search(
            rf"^\s{{0,3}}#{{1,6}}\s+`?{escaped}`?(?:\s|:|$)",
            prompt or "",
            re.IGNORECASE | re.MULTILINE,
        )
        or re.search(
            rf"^\s*-\s+`{escaped}`\s*:",
            prompt or "",
            re.IGNORECASE | re.MULTILINE,
        )
    )


def _prompt_name(prompt_file: str) -> str:
    basename = os.path.basename(prompt_file)
    if basename.startswith(PROMPT_PREFIX) and basename.endswith(PROMPT_SUFFIX):
        return basename[len(PROMPT_PREFIX) : -len(PROMPT_SUFFIX)]
    return ""


def _tool_descriptions(agent: Any, tool_names: set[str]) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    prompt_files = files.get_unique_filenames_in_dirs(
        subagents.get_paths(agent, "prompts"), f"{PROMPT_PREFIX}*{PROMPT_SUFFIX}"
    )
    for prompt_file in prompt_files:
        try:
            prompt = agent.read_prompt(os.path.basename(prompt_file))
        except Exception:
            continue
        for name in _prompt_tool_names(prompt_file, prompt, tool_names):
            if name in tool_names and name not in descriptions:
                descriptions[name] = tool_prompt_description(prompt, name)[:512]
    return descriptions


def _canonical_from_path(path: str, name: str) -> tuple[str, str]:
    if plugin_id := plugins.get_plugin_name_from_path(path):
        return f"plugin:{plugin_id}:{name}", f"Plugin · {plugin_id}"
    return f"local:{name}", "Agent Zero"


def _normalize_ids(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    result: list[str] = []
    for value in raw:
        tool_id = str(value or "").strip()
        if tool_id and tool_id not in result:
            result.append(tool_id)
    return result


def tool_prompt_description(
    prompt: str,
    name: str,
    *,
    fallback: str = "",
) -> str:
    declaration = re.search(
        rf"^\s*-\s+`{re.escape(name)}`:\s+(.+)$",
        prompt or "",
        re.IGNORECASE | re.MULTILINE,
    )
    if declaration:
        return declaration.group(1).strip()
    in_fence = False
    for raw_line in (prompt or "").splitlines():
        line = raw_line.strip()
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence or not line or line.startswith("#"):
            continue
        return line
    return fallback or name.replace("_", " ").strip().capitalize()


def _tool_name_from_id(tool_id: str) -> str:
    return str(tool_id or "").rsplit(":", 1)[-1]
