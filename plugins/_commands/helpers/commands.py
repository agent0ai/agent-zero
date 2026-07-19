from __future__ import annotations

import inspect
import json
import os
import re
import runpy
import shlex
from pathlib import Path
from typing import Any

import yaml

from agent import AgentContext
from helpers import files, plugins, projects, yaml as yaml_helper
from helpers.skills import split_frontmatter


PLUGIN_NAME = "_commands"
COMMANDS_DIR = "commands"
COMMAND_CONFIG_SUFFIX = ".command.yaml"
LEGACY_COMMAND_FILE_SUFFIX = ".command.md"
TEXT_TEMPLATE_SUFFIX = ".txt"
SCRIPT_TEMPLATE_SUFFIX = ".py"
STANDARD_CONFIG_KEYS = {
    "name",
    "description",
    "argument_hint",
    "type",
    "template_path",
    "script_path",
    "include_history",
}
_INVALID_COMMAND_CHARS_RE = re.compile(r"[^a-z0-9_-]+")
_MULTI_DASH_RE = re.compile(r"-{2,}")
_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_.-]+)\}")


def sanitize_command_name(raw_name: str) -> str:
    """Sanitize a raw command name to a lowercase, hyphen-separated slug.

        Strips whitespace, lowercases, replaces spaces and invalid characters with hyphens,
        collapses consecutive hyphens, and strips leading/trailing hyphens and underscores.

        Raises:
            ValueError: If the resulting name is empty.

    """
    raw = (raw_name or "").strip().lower()
    name = raw.replace(" ", "-")
    name = _INVALID_COMMAND_CHARS_RE.sub("-", name)
    name = _MULTI_DASH_RE.sub("-", name).strip("-_")
    if not name:
        raise ValueError("Command name must contain at least one letter or number")
    return name


def normalize_command_type(raw_type: str) -> str:
    """Normalize a command type string to either ``"text"`` or ``"script"``."""
    command_type = (raw_type or "text").strip().lower()
    if command_type not in {"text", "script"}:
        raise ValueError('Command type must be either "text" or "script"')
    return command_type


def command_file_name(command_name: str) -> str:
    """Return the ``.command.yaml`` config filename for *command_name*."""
    return f"{sanitize_command_name(command_name)}{COMMAND_CONFIG_SUFFIX}"


def command_content_file_name(command_name: str, command_type: str) -> str:
    """Return the content filename (``.txt`` or ``.py``) for *command_name* and *command_type*."""
    suffix = (
        TEXT_TEMPLATE_SUFFIX
        if normalize_command_type(command_type) == "text"
        else SCRIPT_TEMPLATE_SUFFIX
    )
    return f"{sanitize_command_name(command_name)}{suffix}"


def parse_slash_invocation(raw_message: str, *, fallback_command: str = "") -> dict[str, Any]:
    """Parse a raw slash-command message into its component parts.

        Returns a dict with keys: ``raw_text``, ``command_name``, ``raw_arguments``,
        and ``arguments`` (parsed by :func:`parse_arguments`).

        Args:
            raw_message: The full message string, e.g. ``"/scan --url https://example.com"``.
            fallback_command: Command name to use when no slash prefix is found.

    """
    text = (raw_message or "").strip()
    slash_match = re.match(r"^/([^\s]+)(?:\s+([\s\S]*))?$", text)
    postfix_match = (
        None
        if slash_match
        else re.match(r"^([\s\S]*\S)\s+/([^\s]+)\s*$", text)
    )
    if slash_match:
        try:
            command_name = sanitize_command_name(slash_match.group(1))
        except ValueError:
            command_name = sanitize_command_name(fallback_command) if fallback_command else ""
        raw_arguments = (slash_match.group(2) or "").strip()
    elif postfix_match:
        try:
            command_name = sanitize_command_name(postfix_match.group(2))
        except ValueError:
            command_name = sanitize_command_name(fallback_command) if fallback_command else ""
        raw_arguments = postfix_match.group(1).strip()
    else:
        command_name = sanitize_command_name(fallback_command) if fallback_command else ""
        raw_arguments = text

    parsed_arguments = parse_arguments(raw_arguments)
    return {
        "raw_text": text,
        "command_name": command_name,
        "raw_arguments": raw_arguments,
        "arguments": parsed_arguments,
    }


def parse_arguments(raw_arguments: str) -> dict[str, Any]:
    """Parse a raw argument string into positional args, flags, and tokens.

        Supports positional values, long flags (``--key value``, ``--key=value``),
        short flags (``-f``), and short flag bundles (``-vq``).

        Returns a dict with keys: ``raw``, ``tokens``, ``positional``, ``flags``.

    """
    normalized_arguments = (raw_arguments or "").strip()
    tokens = _split_arguments(normalized_arguments)
    positional: list[str] = []
    flags: dict[str, Any] = {}

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("--") and len(token) > 2:
            key, value, consumed = _parse_long_flag(token, tokens, index)
            _set_flag_value(flags, key, value)
            index += consumed
            continue

        if token.startswith("-") and len(token) > 1:
            consumed = _parse_short_flag_bundle(token, tokens, index, flags)
            index += consumed
            continue

        positional.append(token)
        index += 1

    return {
        "raw": normalized_arguments,
        "tokens": tokens,
        "positional": positional,
        "flags": flags,
    }


def render_command_body(
    body: str,
    raw_arguments: str,
    *,
    command_name: str = "",
    raw_message: str = "",
) -> str:
    """Render *body* as a text template substituting placeholders from *raw_arguments*.

        Args:
            body: Template string with ``{placeholder}`` markers.
            raw_arguments: Unparsed argument string from the command invocation.
            command_name: Optional command name used for slash-invocation parsing fallback.
            raw_message: Full original message; when provided takes precedence over raw_arguments.

    """
    invocation = parse_slash_invocation(
        raw_message or raw_arguments,
        fallback_command=command_name,
    )
    if not raw_message:
        invocation["raw_arguments"] = (raw_arguments or "").strip()
        invocation["arguments"] = parse_arguments(invocation["raw_arguments"])
    return render_text_template(body, invocation)


def render_text_template(body: str, invocation: dict[str, Any]) -> str:
    """Render *body* as a template substituting placeholders from *invocation* context.

        Unrecognised placeholders resolve to empty string. If *raw_arguments* is present
        and the template contains no argument references, the arguments are appended.

    """
    template = body or ""
    rendered = template

    context = _build_template_context(invocation)
    rendered = _PLACEHOLDER_RE.sub(
        lambda match: _resolve_placeholder(match.group(1), context),
        rendered,
    )
    rendered = _render_legacy_placeholders(rendered, invocation)
    rendered = rendered.strip()

    raw_arguments = invocation["raw_arguments"]
    if raw_arguments and not _template_references_arguments(template):
        suffix = f"Arguments:\n{raw_arguments}"
        rendered = f"{rendered}\n\n{suffix}" if rendered else suffix

    return rendered.strip()


def get_scope_key(project_name: str = "", agent_profile: str = "") -> str:
    """Return the scope identifier key: ``'project'`` when a project is active, else ``'global'``."""
    if project_name:
        return "project"
    return "global"


def get_scope_label(project_name: str = "", agent_profile: str = "") -> str:
    """Return the human-readable scope label: ``'Project'`` or ``'Global'``."""
    if project_name:
        return "Project"
    return "Global"


def get_scope_directory(project_name: str = "", agent_profile: str = "") -> str:
    """Return the absolute filesystem path to the commands directory for the given scope."""
    return plugins.determine_plugin_asset_path(
        PLUGIN_NAME,
        project_name,
        "",
        COMMANDS_DIR,
    )


def ensure_scope_directory(project_name: str = "", agent_profile: str = "") -> str:
    """Ensure the commands directory for the given scope exists, creating it when absent.

        Returns the absolute path to the directory.

    """
    directory = get_scope_directory(project_name, "")
    Path(directory).mkdir(parents=True, exist_ok=True)
    return directory


def get_scope_payload(
    project_name: str = "",
    agent_profile: str = "",
    *,
    ensure_directory: bool = False,
) -> dict[str, Any]:
    """Build a scope descriptor dict for the given project/agent context.

        Returns a dict containing ``project_name``, ``scope_key``, ``scope_label``,
        ``directory_path``, ``exists``, and the private ``_directory_abs_path`` key.

        Args:
            ensure_directory: When ``True``, create the directory if it does not exist.

    """
    directory_path = (
        ensure_scope_directory(project_name, "")
        if ensure_directory
        else get_scope_directory(project_name, "")
    )
    return {
        "project_name": project_name,
        "scope_key": get_scope_key(project_name, ""),
        "scope_label": get_scope_label(project_name, ""),
        "directory_path": _normalize_client_path(directory_path),
        "exists": os.path.isdir(directory_path),
        "_directory_abs_path": directory_path,
    }


def get_context_scope(context_id: str = "") -> dict[str, str]:
    """Resolve the active project name for *context_id* and return a scope mapping.

        Returns ``{"project_name": str}`` — empty string when no project is associated.

    """
    context = _get_context(context_id)
    if not context:
        return {"project_name": ""}

    return {
        "project_name": projects.get_context_project_name(context) or "",
    }


def list_scope_commands(
    project_name: str = "",
    agent_profile: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """List all commands defined in *project_name* scope (not merged with global).

        Each command entry includes ``override_scopes`` and ``override_count`` fields
        indicating lower-scoped commands with the same name.

        Returns:
            Tuple of (commands list, stripped scope payload dict).

    """
    scope = get_scope_payload(project_name, "")
    commands = _load_scope_commands(project_name)
    overrides = _collect_lower_scope_matches(project_name)

    for command in commands:
        override_scopes = overrides.get(command["name"], [])
        command["override_scopes"] = override_scopes
        command["override_count"] = len(override_scopes)

    return commands, strip_private_scope(scope)


def list_effective_commands(
    project_name: str = "",
    agent_profile: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return the merged effective command list for *project_name* scope.

        Project-scoped commands take precedence over global commands of the same name.
        Commands are sorted alphabetically by name.

        Returns:
            Tuple of (sorted commands list, stripped scope payload dict).

    """
    resolved_scope = get_scope_payload(project_name, "")
    merged: dict[str, dict[str, Any]] = {}

    for scope_project in _iter_precedence_scopes(project_name):
        for command in _load_scope_commands(scope_project):
            merged.setdefault(command["name"], command)

    for command in _discover_builtin_commands():
        merged.setdefault(command["name"], command)

    for command in _discover_plugin_commands():
        merged.setdefault(command["name"], command)

    effective = sorted(merged.values(), key=lambda item: item["name"])
    return effective, strip_private_scope(resolved_scope)


def list_builtin_commands() -> list[dict[str, Any]]:
    """Return bundled commands for display in the command manager."""
    return sorted(_discover_builtin_commands(), key=lambda item: item["name"])


def get_command(
    path: str,
    project_name: str = "",
    agent_profile: str = "",
) -> dict[str, Any]:
    """Load and return a single command by its config file *path*.

        Validates that *path* belongs to an effective scope for *project_name*.

        Raises:
            FileNotFoundError: If the command file does not exist.
            ValueError: If the path is outside all valid scopes, not a recognised
                config suffix, or the file content is invalid.

    """
    command_path = _validate_command_path(path, project_name, "", allow_plugin=True)
    # Determine actual scope from the resolved path to get correct metadata.
    # A global command loaded with a project context must report scope=global.
    actual_project = ""
    for scope in _iter_precedence_scopes(project_name):
        scope_dir = get_scope_directory(scope, "")
        if files.is_in_dir(command_path, scope_dir):
            actual_project = scope
            break
    command = _load_command_file(command_path, project_name=actual_project)
    if not command:
        raise ValueError("Command file is invalid or missing required configuration")
    if _is_builtin_command_path(command_path):
        return _mark_builtin_command(command)
    plugin_name = _plugin_name_for_commands_path(command_path)
    if plugin_name:
        _mark_plugin_command(command, plugin_name)
    return command


def save_command(
    *,
    project_name: str = "",
    agent_profile: str = "",
    existing_path: str = "",
    name: str,
    description: str,
    argument_hint: str = "",
    command_type: str = "text",
    body: str = "",
    include_history: bool = False,
    extra_frontmatter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create or update a command, writing both the config and content files.

        When *existing_path* is provided, the old files are removed after the new
        files are written (rename/move semantics).

        Returns:
            The fully-loaded command dict for the saved command.

        Raises:
            FileExistsError: If a command with the same name already exists in scope.
            ValueError: If required fields are missing or values are invalid.

    """
    command_name = sanitize_command_name(name)
    command_description = (description or "").strip()
    if not command_description:
        raise ValueError("Command description is required")

    normalized_type = normalize_command_type(command_type)
    scope_dir = ensure_scope_directory(project_name, "")
    target_config_path = files.get_abs_path(scope_dir, command_file_name(command_name))
    target_content_name = command_content_file_name(command_name, normalized_type)
    target_content_path = files.get_abs_path(scope_dir, target_content_name)
    existing_abs_path = ""
    existing_command: dict[str, Any] | None = None
    if existing_path:
        try:
            existing_abs_path = _validate_command_path(existing_path, project_name, "")
            existing_command = _load_command_file(existing_abs_path, project_name=project_name)
        except FileNotFoundError:
            existing_abs_path = ""
            existing_command = None

    if existing_abs_path and not os.path.exists(existing_abs_path):
        existing_abs_path = ""
        existing_command = None

    if os.path.exists(target_config_path) and not _paths_equal(
        target_config_path, existing_abs_path
    ):
        raise FileExistsError(f'A command named "{command_name}" already exists in this scope')

    existing_content_path = _to_abs_path(existing_command.get("content_path", "")) if existing_command else ""
    if os.path.exists(target_content_path) and not _paths_equal(
        target_content_path, existing_content_path
    ):
        raise FileExistsError(
            f'Command content file "{Path(target_content_path).name}" already exists in this scope'
        )

    content_key = "template_path" if normalized_type == "text" else "script_path"
    config = _build_command_config(
        name=command_name,
        description=command_description,
        argument_hint=argument_hint,
        command_type=normalized_type,
        content_path=target_content_name,
        include_history=include_history,
        extra_config=extra_frontmatter or {},
    )
    if content_key not in config:
        config[content_key] = target_content_name

    files.write_file(target_content_path, _normalize_command_body(body, normalized_type))
    files.write_file(target_config_path, _build_command_yaml(config))

    if existing_abs_path and not _paths_equal(existing_abs_path, target_config_path):
        files.delete_file(existing_abs_path)

    if (
        existing_content_path
        and os.path.exists(existing_content_path)
        and not _paths_equal(existing_content_path, target_content_path)
    ):
        files.delete_file(existing_content_path)

    return get_command(target_config_path, project_name, "")


def delete_command(
    path: str,
    project_name: str = "",
    agent_profile: str = "",
) -> None:
    """Delete the config file and associated content file for *path*.

        Raises:
            FileNotFoundError: If the command file does not exist.
            ValueError: If *path* is invalid or outside the allowed scope.

    """
    command = get_command(path, project_name, "")
    command_path = _validate_command_path(path, project_name, "")
    files.delete_file(command_path)

    content_path = _to_abs_path(command.get("content_path", ""))
    if content_path and os.path.exists(content_path):
        files.delete_file(content_path)


def duplicate_command(
    path: str,
    project_name: str = "",
    agent_profile: str = "",
) -> dict[str, Any]:
    """Duplicate a command, preserving built-in names so the copy overrides the default.

        Returns the newly created command dict.

        Raises:
            FileNotFoundError: If the source command does not exist.
            ValueError: If the source path is invalid.

    """
    command = get_command(path, project_name, "")
    duplicated_name = (
        command["name"]
        if command.get("scope_key") == "builtin"
        else _generate_duplicate_name(command["name"], project_name=project_name)
    )
    return save_command(
        project_name=project_name,
        name=duplicated_name,
        description=command["description"],
        argument_hint=command.get("argument_hint", ""),
        command_type=command.get("command_type", "text"),
        body=command.get("body", ""),
        include_history=bool(command.get("include_history", False)),
        extra_frontmatter=command.get("frontmatter_extra", {}),
    )


async def resolve_command_invocation(
    *,
    path: str,
    slash_text: str,
    project_name: str = "",
    context_id: str = "",
) -> dict[str, Any]:
    """Resolve a slash command invocation, executing text rendering or a Python script hook.

        Args:
            path: Path to the command config file.
            slash_text: The full slash text entered by the user.
            project_name: Active project name (empty string for global scope).'
            context_id: Agent context ID, used for script commands that request history.

        Returns:
            Dict with keys ``command``, ``invocation``, and ``result``
            (``{"text": str, "effects": list}``).

        Raises:
            FileNotFoundError: If the command file is not found.
            ValueError: If path or slash_text is invalid.

    """
    command = get_command(path, project_name, "")
    invocation = parse_slash_invocation(slash_text, fallback_command=command["name"])

    if command.get("command_type") == "script":
        result = await _run_script_command(
            command=command,
            invocation=invocation,
            project_name=project_name,
            context_id=context_id,
        )
    else:
        text = render_text_template(command.get("body", ""), invocation)
        result = {"text": text, "effects": []}

    return {
        "command": _public_command_payload(command),
        "invocation": invocation,
        "result": result,
    }


async def resolve_message_command(
    raw_message: str,
    *,
    context_id: str = "",
) -> dict[str, Any] | None:
    """Resolve a known prefix or postfix slash command from an incoming message."""
    invocation = parse_slash_invocation(raw_message)
    command_name = invocation["command_name"]
    if not command_name:
        return None

    project_name = get_context_scope(context_id)["project_name"]
    effective, _ = list_effective_commands(project_name)
    command = next((item for item in effective if item["name"] == command_name), None)
    if not command:
        return None

    return await resolve_command_invocation(
        path=command["path"],
        slash_text=raw_message,
        project_name=project_name,
        context_id=context_id,
    )


def _build_command_config(
    *,
    name: str,
    description: str,
    argument_hint: str,
    command_type: str,
    content_path: str,
    include_history: bool,
    extra_config: dict[str, Any],
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "name": name,
        "description": description,
        "type": command_type,
    }
    clean_argument_hint = (argument_hint or "").strip()
    if clean_argument_hint:
        config["argument_hint"] = clean_argument_hint

    if command_type == "text":
        config["template_path"] = content_path
    else:
        config["script_path"] = content_path
        if include_history:
            config["include_history"] = True

    for key, value in (extra_config or {}).items():
        if key in STANDARD_CONFIG_KEYS:
            continue
        config[key] = value

    return config


def _build_command_yaml(config: dict[str, Any]) -> str:
    return f"{yaml_helper.dumps(config).strip()}\n"


def _normalize_command_body(body: str, command_type: str) -> str:
    cleaned = (body or "").lstrip("\n").rstrip()
    if cleaned:
        return f"{cleaned}\n"
    return ""


def _load_command_file(
    file_path: str,
    *,
    project_name: str = "",
) -> dict[str, Any] | None:
    if file_path.endswith(COMMAND_CONFIG_SUFFIX):
        return _load_yaml_command_file(file_path, project_name=project_name)
    if file_path.endswith(LEGACY_COMMAND_FILE_SUFFIX):
        return _load_legacy_markdown_file(file_path, project_name=project_name)
    return None


def _load_yaml_command_file(
    file_path: str,
    *,
    project_name: str = "",
) -> dict[str, Any] | None:
    try:
        raw_content = files.read_file(file_path)
    except FileNotFoundError:
        return None

    try:
        parsed = yaml.safe_load(raw_content) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(parsed, dict):
        return None

    raw_name = str(parsed.get("name") or "").strip()
    description = str(parsed.get("description") or "").strip()
    if not raw_name or not description:
        return None

    try:
        command_name = sanitize_command_name(raw_name)
        command_type = normalize_command_type(str(parsed.get("type") or "text"))
    except ValueError:
        return None

    directory_path = str(Path(file_path).parent)
    content_key = "template_path" if command_type == "text" else "script_path"
    configured_content_path = str(parsed.get(content_key) or "").strip() or command_content_file_name(
        command_name, command_type
    )
    content_abs_path = files.get_abs_path(directory_path, configured_content_path)
    # Content file must live in the same directory as its config file.
    # Using directory_path (not the project scope root) allows global commands
    # to load correctly even when a project context is active.
    if not files.is_in_dir(content_abs_path, directory_path):
        return None

    try:
        body = files.read_file(content_abs_path)
    except FileNotFoundError:
        body = ""

    argument_hint = str(parsed.get("argument_hint") or "").strip()
    include_history = bool(parsed.get("include_history", False))
    extra_config = {
        key: value for key, value in parsed.items() if key not in STANDARD_CONFIG_KEYS
    }

    return {
        "name": command_name,
        "description": description,
        "argument_hint": argument_hint,
        "command_type": command_type,
        "include_history": include_history,
        "body": body,
        "path": _normalize_client_path(file_path),
        "config_path": _normalize_client_path(file_path),
        "content_path": _normalize_client_path(content_abs_path),
        "directory_path": _normalize_client_path(directory_path),
        "project_name": project_name,
        "scope_key": get_scope_key(project_name, ""),
        "scope_label": get_scope_label(project_name, ""),
        "source_scope_key": get_scope_key(project_name, ""),
        "source_scope_label": get_scope_label(project_name, ""),
        "frontmatter_extra": extra_config,
    }


def _load_legacy_markdown_file(
    file_path: str,
    *,
    project_name: str = "",
) -> dict[str, Any] | None:
    try:
        content = files.read_file(file_path)
    except FileNotFoundError:
        return None

    frontmatter, body, errors = split_frontmatter(content)
    if errors:
        return None

    raw_name = str(frontmatter.get("name") or "").strip()
    description = str(frontmatter.get("description") or "").strip()
    if not raw_name or not description:
        return None

    try:
        command_name = sanitize_command_name(raw_name)
    except ValueError:
        return None

    argument_hint = str(frontmatter.get("argument_hint") or "").strip()
    extra_frontmatter = {
        key: value for key, value in frontmatter.items() if key not in {"name", "description", "argument_hint"}
    }
    directory_path = str(Path(file_path).parent)
    return {
        "name": command_name,
        "description": description,
        "argument_hint": argument_hint,
        "command_type": "text",
        "include_history": False,
        "body": body,
        "path": _normalize_client_path(file_path),
        "config_path": _normalize_client_path(file_path),
        "content_path": _normalize_client_path(file_path),
        "directory_path": _normalize_client_path(directory_path),
        "project_name": project_name,
        "scope_key": get_scope_key(project_name, ""),
        "scope_label": get_scope_label(project_name, ""),
        "source_scope_key": get_scope_key(project_name, ""),
        "source_scope_label": get_scope_label(project_name, ""),
        "frontmatter_extra": extra_frontmatter,
    }


def _validate_command_path(
    path: str,
    project_name: str = "",
    agent_profile: str = "",
    *,
    allow_plugin: bool = False,
) -> str:
    command_path = _to_abs_path(path)
    # Allow commands from any effective scope (project overrides global, but global is also valid)
    valid_roots = [get_scope_directory(scope, "") for scope in _iter_precedence_scopes(project_name)]
    if not any(files.is_in_dir(command_path, scope_root) for scope_root in valid_roots):
        is_builtin = _is_builtin_command_path(command_path)
        plugin_name = "" if is_builtin else _plugin_name_for_commands_path(command_path)
        if plugin_name:
            if not allow_plugin:
                raise ValueError("Plugin commands are read-only")
        elif is_builtin:
            if not allow_plugin:
                raise ValueError("Built-in commands are read-only")
        else:
            raise ValueError("Command path is outside the selected scope")
    if not (
        command_path.endswith(COMMAND_CONFIG_SUFFIX)
        or command_path.endswith(LEGACY_COMMAND_FILE_SUFFIX)
    ):
        raise ValueError("Command path must point to a .command.yaml or .command.md file")
    if not os.path.exists(command_path):
        raise FileNotFoundError("Command file not found")
    return command_path


def _iter_precedence_scopes(project_name: str) -> list[str]:
    if project_name:
        return [project_name, ""]
    return [""]


def _list_scope_files(scope_dir: str) -> list[str]:
    if not os.path.isdir(scope_dir):
        return []
    files_in_scope = [
        str(path)
        for suffix in (COMMAND_CONFIG_SUFFIX, LEGACY_COMMAND_FILE_SUFFIX)
        for path in Path(scope_dir).glob(f"*{suffix}")
        if path.is_file()
    ]
    files_in_scope.sort(key=lambda item: Path(item).name.lower())
    return files_in_scope


def _load_scope_commands(project_name: str = "") -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    scope_dir = get_scope_directory(project_name, "")

    for file_path in _list_scope_files(scope_dir):
        command = _load_command_file(file_path, project_name=project_name)
        if command:
            commands.append(command)

    commands.sort(key=lambda item: item["name"])
    return commands


def _discover_plugin_commands() -> list[dict[str, Any]]:
    """Discover commands contributed by enabled plugins."""
    commands: list[dict[str, Any]] = []
    for plugin_name in plugins.get_enabled_plugins(None):
        if plugin_name == PLUGIN_NAME:
            continue
        plugin_dir = plugins.find_plugin_dir(plugin_name)
        if not plugin_dir:
            continue
        plugin_commands_dir = files.get_abs_path(plugin_dir, COMMANDS_DIR)
        if not os.path.isdir(plugin_commands_dir):
            continue
        for file_path in _list_scope_files(plugin_commands_dir):
            command = _load_command_file(file_path, project_name="")
            if command:
                commands.append(_mark_plugin_command(command, plugin_name))
    return commands


def _discover_builtin_commands() -> list[dict[str, Any]]:
    plugin_dir = plugins.find_plugin_dir(PLUGIN_NAME)
    if not plugin_dir:
        return []
    commands_dir = files.get_abs_path(plugin_dir, COMMANDS_DIR)
    commands: list[dict[str, Any]] = []
    for file_path in _list_scope_files(commands_dir):
        command = _load_command_file(file_path, project_name="")
        if command:
            commands.append(_mark_builtin_command(command))
    return commands


def _collect_lower_scope_matches(project_name: str = "") -> dict[str, list[str]]:
    lower_scope_matches: dict[str, list[str]] = {}
    if not project_name:
        return lower_scope_matches

    for command in _load_scope_commands(""):
        lower_scope_matches.setdefault(command["name"], []).append(get_scope_label("", ""))

    return lower_scope_matches


def _generate_duplicate_name(
    command_name: str,
    *,
    project_name: str = "",
) -> str:
    base_name = sanitize_command_name(f"{command_name}-copy")
    candidate = base_name
    counter = 2
    scope_dir = ensure_scope_directory(project_name, "")

    while os.path.exists(files.get_abs_path(scope_dir, command_file_name(candidate))):
        candidate = f"{base_name}-{counter}"
        counter += 1

    return candidate


def _build_template_context(invocation: dict[str, Any]) -> dict[str, Any]:
    arguments = invocation.get("arguments", {})
    return {
        "full": invocation.get("raw_text", ""),
        "raw": invocation.get("raw_arguments", ""),
        "command": invocation.get("command_name", ""),
        "args": {
            "raw": arguments.get("raw", ""),
            "tokens": arguments.get("tokens", []),
            "positional": arguments.get("positional", []),
            "flags": arguments.get("flags", {}),
        },
    }


def _resolve_placeholder(path: str, context: dict[str, Any]) -> str:
    resolved = _resolve_path(context, path)
    if resolved is None:
        return ""
    if isinstance(resolved, (dict, list)):
        return json.dumps(resolved, ensure_ascii=False)
    return str(resolved)


def _resolve_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, dict):
            if part in current:
                current = current[part]
                continue
            part_with_dash = part.replace("_", "-")
            if part_with_dash in current:
                current = current[part_with_dash]
                continue
            return None

        if isinstance(current, list):
            if not part.isdigit():
                return None
            index = int(part)
            if index < 0 or index >= len(current):
                return None
            current = current[index]
            continue

        return None
    return current


def _render_legacy_placeholders(template: str, invocation: dict[str, Any]) -> str:
    rendered = template
    arguments = invocation.get("arguments", {})
    positional = arguments.get("positional", [])
    for index in range(10):
        rendered = rendered.replace(f"${index}", positional[index] if index < len(positional) else "")
    rendered = rendered.replace("$ARGUMENTS", invocation.get("raw_arguments", ""))
    return rendered


def _template_references_arguments(template: str) -> bool:
    if "$ARGUMENTS" in template:
        return True
    if any(f"${index}" in template for index in range(10)):
        return True
    if "{raw}" in template:
        return True
    return "{args." in template


def _parse_long_flag(token: str, tokens: list[str], index: int) -> tuple[str, Any, int]:
    flag_token = token[2:]
    if "=" in flag_token:
        key, value = flag_token.split("=", 1)
        return _normalize_flag_name(key), value, 1

    key = _normalize_flag_name(flag_token)
    next_index = index + 1
    if next_index < len(tokens) and not tokens[next_index].startswith("-"):
        return key, tokens[next_index], 2
    return key, True, 1


def _parse_short_flag_bundle(
    token: str, tokens: list[str], index: int, flags: dict[str, Any]
) -> int:
    short_token = token[1:]
    if len(short_token) > 1 and "=" not in short_token:
        for char in short_token:
            _set_flag_value(flags, _normalize_flag_name(char), True)
        return 1

    if "=" in short_token:
        key, value = short_token.split("=", 1)
        _set_flag_value(flags, _normalize_flag_name(key), value)
        return 1

    key = _normalize_flag_name(short_token)
    _set_flag_value(flags, key, True)
    return 1


def _set_flag_value(flags: dict[str, Any], key: str, value: Any) -> None:
    if key in flags:
        current = flags[key]
        if isinstance(current, list):
            current.append(value)
        else:
            flags[key] = [current, value]
        return
    flags[key] = value


def _normalize_flag_name(raw_flag: str) -> str:
    return (raw_flag or "").strip().lower().replace("-", "_")


def _split_arguments(raw_arguments: str) -> list[str]:
    if not raw_arguments:
        return []
    try:
        return shlex.split(raw_arguments)
    except ValueError:
        return raw_arguments.split()


async def _run_script_command(
    *,
    command: dict[str, Any],
    invocation: dict[str, Any],
    project_name: str,
    context_id: str,
) -> dict[str, Any]:
    script_path = _to_abs_path(command.get("content_path", ""))
    if not script_path:
        raise ValueError("Script command is missing script_path")
    if not os.path.exists(script_path):
        raise ValueError("Script file not found for this command")

    module_globals = runpy.run_path(script_path)
    hook = module_globals.get("run")
    if not callable(hook):
        raise ValueError('Script command must expose a callable "run(payload)" function')

    context = _get_context(context_id)
    history = _extract_chat_history(context) if command.get("include_history") else []
    payload = {
        "command": _public_command_payload(command),
        "invocation": invocation,
        "arguments": invocation.get("arguments", {}),
        "context": {
            "context_id": context_id,
            "project_name": project_name,
            "agent": getattr(context, "agent0", None) if context else None,
            "chat_history": history,
        },
    }

    result = hook(payload)
    if inspect.isawaitable(result):
        result = await result
    return _normalize_script_result(result)


def _normalize_script_result(result: Any) -> dict[str, Any]:
    if isinstance(result, str):
        return {"text": result, "effects": []}

    if isinstance(result, dict):
        text = result.get("text")
        if text is None:
            text = result.get("replacement_text")

        effects = result.get("effects")
        if effects is None:
            effects = []
        if not isinstance(effects, list):
            raise ValueError("Script result.effects must be an array when provided")

        normalized_text = str(text) if text is not None else ""
        return {"text": normalized_text, "effects": effects}

    raise ValueError("Script run(payload) must return either a string or an object")


def _extract_chat_history(context: AgentContext | None) -> list[Any]:
    if not context:
        return []

    for attribute in ("chat_history", "history", "messages"):
        value = getattr(context, attribute, None)
        if isinstance(value, list):
            return value

    getter = getattr(context, "get_data", None)
    if callable(getter):
        for key in ("chat_history", "messages", "history"):
            value = getter(key)
            if isinstance(value, list):
                return value

    return []


def _public_command_payload(command: dict[str, Any]) -> dict[str, Any]:
    payload = dict(command)
    payload.pop("body", None)
    return payload


def _normalize_client_path(path: str) -> str:
    return files.normalize_a0_path(path).replace("\\", "/")


def _paths_equal(path_a: str, path_b: str) -> bool:
    if not path_a or not path_b:
        return False
    return os.path.normcase(os.path.normpath(path_a)) == os.path.normcase(
        os.path.normpath(path_b)
    )


def _get_context(context_id: str = "") -> AgentContext | None:
    if context_id:
        return AgentContext.get(context_id)
    return AgentContext.current() or AgentContext.first()


def _to_abs_path(path: str) -> str:
    return files.fix_dev_path(path)


def _plugin_scope_label(plugin_name: str) -> str:
    return f"Plugin: {plugin_name}"


def _mark_plugin_command(command: dict[str, Any], plugin_name: str) -> dict[str, Any]:
    scope_label = _plugin_scope_label(plugin_name)
    command["source_plugin"] = plugin_name
    command["scope_key"] = "plugin"
    command["scope_label"] = scope_label
    command["source_scope_key"] = "plugin"
    command["source_scope_label"] = scope_label
    return command


def _mark_builtin_command(command: dict[str, Any]) -> dict[str, Any]:
    command["source_plugin"] = PLUGIN_NAME
    command["scope_key"] = "builtin"
    command["scope_label"] = "Built-in"
    command["source_scope_key"] = "builtin"
    command["source_scope_label"] = "Built-in"
    return command


def _builtin_commands_dir() -> str:
    plugin_dir = plugins.find_plugin_dir(PLUGIN_NAME)
    return files.get_abs_path(plugin_dir, COMMANDS_DIR) if plugin_dir else ""


def _is_builtin_command_path(path: str) -> bool:
    commands_dir = _builtin_commands_dir()
    return bool(commands_dir and files.is_in_dir(_to_abs_path(path), commands_dir))


def _plugin_name_for_commands_path(path: str) -> str:
    abs_path = _to_abs_path(path)
    for plugin_name in plugins.get_enabled_plugins(None):
        if plugin_name == PLUGIN_NAME:
            continue
        plugin_dir = plugins.find_plugin_dir(plugin_name)
        if not plugin_dir:
            continue
        plugin_commands_dir = files.get_abs_path(plugin_dir, COMMANDS_DIR)
        if files.is_in_dir(abs_path, plugin_commands_dir):
            return plugin_name
    return ""


def _is_plugin_commands_dir(path: str) -> bool:
    """Check if a path is inside any installed plugin's commands/ subdirectory."""
    return bool(_plugin_name_for_commands_path(path))


def strip_private_scope(scope: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *scope* with all keys prefixed by ``_`` removed."""
    return {key: value for key, value in scope.items() if not key.startswith("_")}


def _strip_private_scope(scope: dict[str, Any]) -> dict[str, Any]:
    return strip_private_scope(scope)
