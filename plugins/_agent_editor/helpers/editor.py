from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time
from types import SimpleNamespace
from typing import Any
import unicodedata
from urllib.parse import urlencode
from uuid import uuid4

from helpers import cache, files, plugins, projects, skills, subagents, tool_policy
from helpers import yaml as yaml_helper


PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$")
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
SPECIFICS_FILE = "agent.system.main.specifics.md"
METADATA_KEYS = ("title", "description", "context", "avatar")
MAX_PROMPT_BYTES = 512 * 1024
MAX_PROMPTS_BYTES = 2 * 1024 * 1024
MAX_AVATAR_BYTES = 8 * 1024 * 1024
MAX_AVATAR_DIMENSION = 4096
AVATAR_SIZE = 512
RESERVED_PROFILE_IDS = {"_example"}
NON_PROMPT_MARKDOWN = {"AGENTS.md"}
USER_AGENTS_ROOT = Path(files.get_abs_path(subagents.USER_AGENTS_DIR))
STAGED_AVATAR_ROOT = Path(files.get_abs_path("tmp", "agent-editor"))
_TOOL_POLICY_KEYS = ("mode", "default", "mcp_default", "allowed", "blocked")
_MUTATION_LOCK = threading.RLock()


class _EditorContext:
    def __init__(self, project_name: str = "") -> None:
        self.project_name = project_name

    def get_data(self, key: str, recursive: bool = True):
        return self.project_name if key == projects.CONTEXT_DATA_KEY_PROJECT else None


class EditorAgent:
    def __init__(self, profile_id: str, context: Any | None = None) -> None:
        self.config = SimpleNamespace(profile=profile_id)
        self.context = context or _EditorContext()
        self.data: dict[str, Any] = {}

    def get_data(self, key: str):
        return self.data.get(key)

    def read_prompt(self, filename: str, **kwargs: Any) -> str:
        path = files.find_file_in_dirs(filename, subagents.get_paths(self, "prompts"))
        return Path(path).read_text(encoding="utf-8")


@dataclass(frozen=True)
class ProfileLayer:
    kind: str
    metadata_path: Path | None
    data: dict[str, Any]


@dataclass(frozen=True)
class FileChange:
    action: str
    path: Path
    content: bytes | None = None

    @property
    def relative_path(self) -> str:
        return files.deabsolute_path(str(self.path)).replace(os.sep, "/")


@dataclass
class ChangePlan:
    changes: dict[Path, FileChange] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    staged_tokens: set[str] = field(default_factory=set)
    profile_id: str = ""
    project_name: str = ""
    creating: bool = False
    remove_empty_root: bool = False

    def write(self, path: Path, content: str | bytes) -> None:
        payload = content.encode("utf-8") if isinstance(content, str) else content
        if path.is_file() and path.read_bytes() == payload:
            self.changes.pop(path, None)
            return
        self.changes[path] = FileChange("write", path, payload)

    def delete(self, path: Path) -> None:
        if path.exists():
            self.changes[path] = FileChange("delete", path)
        else:
            self.changes.pop(path, None)

    def response(self) -> dict[str, Any]:
        ordered = sorted(self.changes.values(), key=lambda change: change.relative_path)
        return {
            "written": [
                change.relative_path for change in ordered if change.action == "write"
            ],
            "deleted": [
                change.relative_path for change in ordered if change.action == "delete"
            ],
            "warnings": list(self.warnings),
        }


def validate_profile_id(profile_id: Any) -> str:
    value = str(profile_id or "").strip()
    if value in RESERVED_PROFILE_IDS or not PROFILE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            "Profile ID must be 1–64 lowercase letters, numbers, hyphens, or underscores."
        )
    return value


def profile_id_from_title(title: Any) -> str:
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Agent name is required.")
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-z0-9_-]+", "-", value.lower())
    value = re.sub(r"[-_]{2,}", "-", value).strip("-_")[:64].rstrip("-_")
    if not value:
        raise ValueError("Agent name must contain at least one letter or number.")
    return validate_profile_id(value)


def save_easy_profile(
    title: Any,
    instructions: Any,
    context: Any | None = None,
    *,
    tool_policy: Any | None = None,
) -> tuple[str, dict[str, Any]]:
    if not isinstance(instructions, str) or not instructions.strip():
        raise ValueError("Instructions are required for a new agent.")
    profile_id = profile_id_from_title(title)
    patch: dict[str, Any] = {
        "profile_id": profile_id,
        "creating": True,
        "editor_mode": "easy",
        "metadata": {"set": {"title": title}, "reset": []},
        "prompts": {"set": {SPECIFICS_FILE: instructions}, "reset": []},
    }
    if tool_policy is not None:
        patch["tool_policy"] = _mapping(tool_policy, "tool_policy")
    return profile_id, apply_change_plan(build_change_plan(patch, context))


def _context_project_name(context: Any | None) -> str:
    return str(projects.get_context_project_name(context) or "") if context else ""


def _profile_root(profile_id: str, project_name: str = "") -> Path:
    return (
        Path(projects.get_project_meta(project_name, "agents", profile_id))
        if project_name
        else USER_AGENTS_ROOT / profile_id
    )


def _scope_owns_custom_profile(profile_id: str, project_name: str) -> bool:
    if not _profile_root(profile_id, project_name).is_dir():
        return False
    if (Path(files.get_abs_path(subagents.DEFAULT_AGENTS_DIR)) / profile_id).is_dir():
        return False
    if any(Path(path).is_dir() for path in plugins.get_plugin_paths("agents", profile_id)):
        return False
    return not project_name or not (USER_AGENTS_ROOT / profile_id).is_dir()


def profile_exists(profile_id: str, context: Any | None = None) -> bool:
    agent = EditorAgent(profile_id, context)
    if (Path(files.get_abs_path(subagents.DEFAULT_AGENTS_DIR)) / profile_id).is_dir():
        return True
    if (USER_AGENTS_ROOT / profile_id).is_dir():
        return True
    if any(Path(path).is_dir() for path in plugins.get_plugin_paths("agents", profile_id)):
        return True
    project_name = _context_project_name(agent.context)
    return bool(
        project_name
        and Path(projects.get_project_meta(project_name, "agents", profile_id)).is_dir()
    )


def list_profiles(context: Any | None = None) -> list[dict[str, Any]]:
    project_name = _context_project_name(context)
    resolved = subagents.get_agents_dict(project_name)
    enabled = subagents.get_available_agents_dict(project_name)
    names = set(resolved)
    roots = [Path(files.get_abs_path("agents")), USER_AGENTS_ROOT]
    if project_name:
        roots.append(Path(projects.get_project_meta(project_name, "agents")))
    for root in roots:
        if root.is_dir():
            names.update(path.name for path in root.iterdir() if path.is_dir())

    result: list[dict[str, Any]] = []
    for profile_id in sorted(names):
        if profile_id in RESERVED_PROFILE_IDS:
            continue
        state = metadata_state(profile_id, context)
        result.append(
            {
                "id": profile_id,
                "title": state["title"]["effective"] or profile_id,
                "description": state["description"]["effective"] or "",
                "origin": state["origin"],
                "origin_chain": state["origin_chain"],
                "built_in": state["built_in"],
                "scope_has_overrides": _scope_has_overrides(profile_id, context),
                "deletable": state["deletable"],
                "avatar": state["avatar"]["effective"],
                "avatar_url": effective_avatar_url(profile_id, context),
                "enabled": profile_id in enabled,
                "available": profile_exists(profile_id, context),
            }
        )
    return result


def build_editor_state(
    profile_id: str,
    context: Any | None = None,
) -> dict[str, Any]:
    profile_id = validate_profile_id(profile_id)
    agent = EditorAgent(profile_id, context)
    prompt_files = prompt_catalog(agent)
    tool_catalog = tool_policy.get_tool_catalog(agent)
    from plugins._model_config.helpers import model_config

    presets: list[dict[str, Any]] = []
    for preset in model_config.get_presets():
        name = str(preset.get("name") or "").strip()
        if not name:
            continue
        resolved = model_config.resolve_config_settings(
            {model_config.MODEL_PRESET_CONFIG_KEY: name}
        )
        presets.append(
            {
                "name": name,
                "main": _model_identity(resolved.get("chat_model")),
                "utility": _model_identity(resolved.get("utility_model")),
                "embedding": _model_identity(resolved.get("embedding_model")),
            }
        )
    project_name = _context_project_name(agent.context)
    model_path = _profile_config_path(profile_id, "_model_config", project_name)
    model_scope = _read_mapping(model_path)
    selected = model_config.get_configured_preset_name(agent=agent)

    tool_path = _profile_config_path(profile_id, tool_policy.PLUGIN_NAME, project_name)
    skill_path = _profile_config_path(
        profile_id,
        skills.ACTIVE_SKILLS_PLUGIN_NAME,
        project_name,
    )
    tool_scope = _read_mapping(tool_path)
    skill_scope = _read_mapping(skill_path)
    skill_policy = skills.normalize_visibility_policy(
        skill_scope.get("visibility_policy")
    )
    effective_skill_policy = skills.get_visibility_policy(agent)
    skill_catalog = [
        {**item, "available": True}
        for item in skills.list_skill_catalog(agent=agent)
    ]
    known_skill_ids = {
        value.casefold()
        for item in skill_catalog
        for value in (
            str(item.get("name") or ""),
            str(item.get("path") or ""),
            Path(str(item.get("path") or "")).name,
        )
        if value
    }
    for skill_id in [*skill_policy["allowed"], *skill_policy["blocked"]]:
        if skill_id.casefold() in known_skill_ids:
            continue
        known_skill_ids.add(skill_id.casefold())
        allowed = skills.is_skill_allowed(effective_skill_policy, skill_id)
        skill_catalog.append(
            {
                "name": skill_id,
                "description": "",
                "path": skill_id,
                "origin": "Unavailable",
                "hidden": not allowed,
                "tags": [],
                "allowed_tools": [],
                "available": False,
            }
        )
    skill_catalog.sort(
        key=lambda item: (
            str(item.get("name") or "").casefold(),
            str(item.get("path") or ""),
        )
    )
    return {
        "profile": build_profile_state(profile_id, context),
        "prompts": prompt_files,
        "tools": {
            "policy": tool_policy.normalize_policy(tool_scope),
            "effective_policy": tool_policy.get_policy(agent),
            "has_override": any(key in tool_scope for key in _TOOL_POLICY_KEYS),
            "catalog": tool_catalog,
        },
        "skills": {
            "policy": skill_policy,
            "effective_policy": effective_skill_policy,
            "has_override": "visibility_policy" in skill_scope,
            "catalog": skill_catalog,
        },
        "model_presets": presets,
        "model_preset": {
            "effective": selected,
            "override": model_scope.get(model_config.MODEL_PRESET_CONFIG_KEY),
            "has_override": model_config.MODEL_PRESET_CONFIG_KEY in model_scope,
        },
    }


def build_profile_state(
    profile_id: str,
    context: Any | None = None,
) -> dict[str, Any]:
    profile_id = validate_profile_id(profile_id)
    metadata = metadata_state(profile_id, context)
    return {
        "id": profile_id,
        "origin": metadata.pop("origin"),
        "origin_chain": metadata.pop("origin_chain"),
        "built_in": metadata.pop("built_in"),
        "scope_has_overrides": _scope_has_overrides(profile_id, context),
        "deletable": metadata.pop("deletable"),
        "metadata": metadata,
        "avatar_url": effective_avatar_url(profile_id, context),
    }


def metadata_state(profile_id: str, context: Any | None = None) -> dict[str, Any]:
    layers = _metadata_layers(profile_id, context)
    project_name = _context_project_name(context)
    scope_kind = "project" if project_name else "user"
    scope_layer = next((layer for layer in layers if layer.kind == scope_kind), None)
    lower_layers = [layer for layer in layers if layer.kind != scope_kind]
    state: dict[str, Any] = {}
    for key in METADATA_KEYS:
        effective, source, _ = _layer_value(layers, key)
        inherited, inherited_source, _ = _layer_value(lower_layers, key)
        state[key] = {
            "effective": effective,
            "override": (
                scope_layer.data.get(key)
                if scope_layer and key in scope_layer.data
                else None
            ),
            "has_override": bool(scope_layer and key in scope_layer.data),
            "source": _relative_source(source),
            "inherited": inherited,
            "inherited_source": _relative_source(inherited_source),
        }

    built_in = (Path(files.get_abs_path("agents")) / profile_id).is_dir()
    plugin_origin = any(layer.kind == "plugin" for layer in layers)
    state.update(
        {
            "origin": "Built-in" if built_in else "Plugin" if plugin_origin else "Custom",
            "origin_chain": list(dict.fromkeys(layer.kind for layer in layers)),
            "built_in": built_in,
            "deletable": _scope_owns_custom_profile(profile_id, project_name),
        }
    )
    return state


def _scope_has_overrides(profile_id: str, context: Any | None = None) -> bool:
    project_name = _context_project_name(context)
    root = _profile_root(profile_id, project_name)
    metadata = _read_mapping(
        root / "agent.yaml" if (root / "agent.yaml").is_file() else root / "agent.json"
    )
    if any(key in metadata for key in METADATA_KEYS):
        return True

    scope_prompts = root / "prompts"
    if scope_prompts.is_dir():
        inherited_roots = [
            directory / "prompts"
            for _, directory in _profile_directories(profile_id, context)
            if directory.absolute() != root.absolute()
        ]
        inherited_roots.append(Path(files.get_abs_path("prompts")))
        if any(
            path.name not in NON_PROMPT_MARKDOWN
            and any((inherited / path.name).is_file() for inherited in inherited_roots)
            for path in scope_prompts.glob("*.md")
            if path.is_file()
        ):
            return True

    from plugins._model_config.helpers import model_config

    checks = (
        (
            _profile_config_path(profile_id, "_model_config", project_name),
            (model_config.MODEL_PRESET_CONFIG_KEY,),
        ),
        (
            _profile_config_path(profile_id, tool_policy.PLUGIN_NAME, project_name),
            _TOOL_POLICY_KEYS,
        ),
        (
            _profile_config_path(
                profile_id,
                skills.ACTIVE_SKILLS_PLUGIN_NAME,
                project_name,
            ),
            ("visibility_policy",),
        ),
    )
    return any(any(key in _read_mapping(path) for key in keys) for path, keys in checks)


def prompt_catalog(agent: EditorAgent) -> list[dict[str, Any]]:
    roots = [Path(path) for path in subagents.get_paths(agent, "prompts")]
    names = {
        path.name
        for root in roots
        if root.is_dir()
        for path in root.glob("*.md")
        if path.is_file() and path.name not in NON_PROMPT_MARKDOWN
    }
    names.add(SPECIFICS_FILE)
    project_name = _context_project_name(agent.context)
    scope_prompt_dir = _profile_root(agent.config.profile, project_name) / "prompts"
    project_root = (
        Path(projects.get_project_meta(project_name)) if project_name else None
    )
    result: list[dict[str, Any]] = []
    for name in sorted(names, key=lambda value: (_prompt_group(value)[0], value)):
        occurrences: list[tuple[Path, str, str]] = []
        for root in roots:
            path = root / name
            if path.is_file():
                kind, label = _prompt_source(root, scope_prompt_dir, project_root)
                occurrences.append((path, kind, label))

        effective = occurrences[0] if occurrences else None
        override = next((item for item in occurrences if item[1] == "scope"), None)
        inherited = next(
            (
                item
                for item in occurrences
                if item[1] != "scope"
            ),
            None,
        )
        effective_text, effective_error = _prompt_text(effective[0] if effective else None)
        override_text, override_error = _prompt_text(override[0] if override else None)
        inherited_text, inherited_error = _prompt_text(
            inherited[0] if inherited else None
        )
        group_number, group_label = _prompt_group(name)
        source_kind = effective[1] if effective else ""
        if effective_error or override_error or inherited_error:
            state = "Conflict"
        elif override:
            state = (
                "Overridden here (empty)"
                if override_text == ""
                else "Overridden here"
            )
        elif source_kind == "plugin":
            state = "Plugin-provided"
        elif effective:
            state = "Inherited"
        else:
            state = "Unavailable"

        preview = _expand_static_prompt(name, roots, 0, set())

        result.append(
            {
                "filename": name,
                "group": group_number,
                "group_label": group_label,
                "state": state,
                "effective": effective_text,
                "override": override_text if override else None,
                "has_override": bool(override),
                "inherited": inherited_text,
                "source": _relative_source(effective[0] if effective else None),
                "inherited_source": _relative_source(
                    inherited[0] if inherited else None
                ),
                "source_chain": [
                    label for _, _, label in reversed(occurrences)
                ],
                "preview": preview,
                "error": effective_error or override_error or inherited_error,
                "dynamic_processor": any(
                    (root / f"{Path(name).stem}.py").is_file() for root in roots
                ),
            }
        )
    return result


def effective_avatar_path(profile_id: str, context: Any | None = None) -> Path | None:
    layers = _metadata_layers(profile_id, context)
    value, source, _ = _layer_value(layers, "avatar")
    if not isinstance(value, dict) or value.get("kind") != "image" or not source:
        return None
    relative = str(value.get("value") or "")
    candidate = (source.parent / relative).resolve()
    if not files.is_in_dir(str(candidate), str(source.parent)) or not candidate.is_file():
        return None
    return candidate


def effective_avatar_url(profile_id: str, context: Any | None = None) -> str:
    path = effective_avatar_path(profile_id, context)
    if not path:
        return ""
    query = {
        "profile_id": profile_id,
        "v": str(path.stat().st_mtime_ns),
    }
    project_name = _context_project_name(context)
    if project_name:
        query["project_name"] = project_name
    return "/api/plugins/_agent_editor/agent_editor_avatar?" + urlencode(query)


def _profile_directories(
    profile_id: str, context: Any | None
) -> list[tuple[str, Path]]:
    agent = EditorAgent(profile_id, context)
    directories: list[tuple[str, Path]] = [
        (
            "profile",
            Path(files.get_abs_path("agents", profile_id)),
        )
    ]
    for directory in plugins.get_enabled_plugin_paths(agent, "agents", profile_id):
        directories.append(("plugin", Path(directory)))
    directories.append(("user", USER_AGENTS_ROOT / profile_id))

    project_name = _context_project_name(agent.context)
    if project_name:
        directories.append(
            (
                "project",
                Path(projects.get_project_meta(project_name, "agents", profile_id)),
            )
        )
    return directories


def _metadata_layers(profile_id: str, context: Any | None) -> list[ProfileLayer]:
    return [
        layer
        for kind, directory in _profile_directories(profile_id, context)
        if (layer := _load_profile_layer(kind, directory)) is not None
    ]


def _load_profile_layer(kind: str, directory: Path) -> ProfileLayer | None:
    if not directory.is_dir():
        return None
    yaml_path = directory / "agent.yaml"
    json_path = directory / "agent.json"
    path = yaml_path if yaml_path.is_file() else json_path if json_path.is_file() else None
    data = _read_mapping(path) if path else {}
    return ProfileLayer(kind, path, data)


def _read_mapping(path: Path | None) -> dict[str, Any]:
    if not path or not path.is_file():
        return {}
    try:
        value = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.suffix.lower() == ".json"
            else yaml_helper.loads(path.read_text(encoding="utf-8"))
        )
    except Exception:
        return {}
    return dict(value) if isinstance(value, dict) else {}


def _layer_value(
    layers: list[ProfileLayer], key: str
) -> tuple[Any, Path | None, str]:
    for layer in reversed(layers):
        if key in layer.data:
            return layer.data[key], layer.metadata_path, layer.kind
    return None, None, ""


def _prompt_source(
    root: Path, scope_prompt_dir: Path, project_root: Path | None
) -> tuple[str, str]:
    if root.resolve() == scope_prompt_dir.resolve():
        return "scope", "Your override"
    if project_root and files.is_in_dir(str(root), str(project_root)):
        return "project", f"Project · {project_root.parent.name}"
    plugin = plugins.get_plugin_name_from_path(root)
    if plugin:
        return "plugin", f"Plugin · {plugin}"
    bundled_agents = Path(files.get_abs_path("agents"))
    if files.is_in_dir(str(root), str(bundled_agents)):
        return "profile", root.parent.name.replace("-", " ").title()
    if root.resolve() == Path(files.get_abs_path("prompts")).resolve():
        return "framework", "Framework"
    return "global", "Global"


def _prompt_group(filename: str) -> tuple[str, str]:
    if filename == SPECIFICS_FILE:
        return "2.1", "Agent instructions"
    if filename == "agent.system.main.role.md":
        return "2.2", "Role"
    if filename == "agent.system.main.environment.md":
        return "2.3", "Environment"
    if filename.startswith("agent.system.main.communication"):
        return "2.4", "Communication"
    if filename == "agent.system.main.solving.md":
        return "2.5", "Problem solving"
    if filename == "agent.system.main.tips.md":
        return "2.6", "Tips"
    if filename.startswith("fw."):
        return "2.7", "Framework messages"
    if filename.startswith("agent.system.tool.") or "tool" in filename:
        return "2.8", "Tool instructions"
    if filename.startswith(("agent.context.", "agent.system.projects.", "agent.system.skills")):
        return "2.9", "Context, projects & skills"
    return "2.10", "Other"


def _model_identity(value: Any) -> dict[str, str]:
    item = value if isinstance(value, dict) else {}
    return {
        "provider": str(item.get("provider") or ""),
        "name": str(item.get("name") or ""),
    }


def _profile_config_path(
    profile_id: str,
    plugin_name: str,
    project_name: str = "",
) -> Path:
    return Path(
        plugins.determine_plugin_asset_path(
            plugin_name,
            project_name,
            profile_id,
            plugins.CONFIG_FILE_NAME,
        )
    )


def _relative_source(path: Path | None) -> str:
    return files.deabsolute_path(str(path)).replace(os.sep, "/") if path else ""


def _prompt_text(path: Path | None) -> tuple[str, str]:
    if not path:
        return "", ""
    try:
        return path.read_text(encoding="utf-8"), ""
    except (OSError, UnicodeError) as exc:
        return "", f"Prompt is not readable UTF-8: {exc}"


_NAMED_INCLUDE = re.compile(r"{{\s*include\s*['\"](.*?)['\"]\s*}}")
_ORIGINAL_INCLUDE = re.compile(r"{{\s*include\s+original\s*}}")


def _expand_static_prompt(
    filename: str,
    roots: list[Path],
    start_index: int,
    seen: set[Path],
) -> str:
    relative = Path(filename)
    if relative.is_absolute() or ".." in relative.parts:
        return ""
    match = next(
        (
            (index, root / relative)
            for index, root in enumerate(roots[start_index:], start=start_index)
            if (root / relative).is_file()
        ),
        None,
    )
    if not match:
        return ""
    index, path = match
    resolved = path.resolve()
    if resolved in seen:
        return "{{ include cycle }}"
    text, error = _prompt_text(path)
    if error:
        return ""
    branch_seen = {*seen, resolved}
    text = _ORIGINAL_INCLUDE.sub(
        lambda _match: _expand_static_prompt(
            filename,
            roots,
            index + 1,
            branch_seen,
        ),
        text,
    )
    return _NAMED_INCLUDE.sub(
        lambda include: _expand_static_prompt(
            include.group(1),
            roots,
            0,
            branch_seen,
        ) or include.group(0),
        text,
    )
def build_change_plan(
    patch: dict[str, Any],
    context: Any | None = None,
) -> ChangePlan:
    if not isinstance(patch, dict):
        raise ValueError("The save patch must be an object.")

    profile_id = validate_profile_id(patch.get("profile_id"))
    project_name = _context_project_name(context)
    profile_root = _profile_root(profile_id, project_name)
    creating = bool(patch.get("creating"))
    easy = str(patch.get("editor_mode") or "advanced").lower() == "easy"
    exists = profile_exists(profile_id, context)
    if creating and exists:
        raise ValueError(
            f"An agent with the profile ID `{profile_id}` already exists. "
            "Open it to edit its user overrides or choose another name."
        )
    if not creating and not exists:
        raise ValueError(f'Agent profile "{profile_id}" does not exist.')

    plan = ChangePlan(
        profile_id=profile_id,
        project_name=project_name,
        creating=creating,
    )
    if "metadata" in patch:
        _plan_metadata(plan, patch["metadata"], context, creating=creating)
    if "prompts" in patch:
        _plan_prompts(
            plan,
            patch["prompts"],
            context,
            creating=creating,
            easy=easy,
        )
    if "model_preset" in patch:
        _plan_model_preset(plan, patch["model_preset"])
    if "tool_policy" in patch:
        _plan_tool_policy(plan, patch["tool_policy"])
    if "skill_policy" in patch:
        _plan_skill_policy(plan, patch["skill_policy"])

    if creating:
        metadata = _planned_mapping(plan, profile_root / "agent.yaml")
        if not str(metadata.get("title") or "").strip():
            raise ValueError("Agent name is required.")
        specifics = profile_root / "prompts" / SPECIFICS_FILE
        change = plan.changes.get(specifics)
        if not change or change.action != "write" or not (change.content or b"").strip():
            raise ValueError("Instructions are required for a new agent.")

    return plan


def plan_profile_enabled(
    profile_id: str,
    enabled: bool,
    context: Any | None = None,
) -> ChangePlan:
    profile_id = validate_profile_id(profile_id)
    if _context_project_name(context):
        raise ValueError("Project availability is stored in project settings.")
    if not profile_exists(profile_id, context):
        raise ValueError(f'Agent profile "{profile_id}" does not exist.')

    root = _profile_root(profile_id)
    yaml_path = root / "agent.yaml"
    legacy_path = root / "agent.json"
    data = _read_mapping_strict(
        yaml_path if yaml_path.is_file() else legacy_path,
        "profile metadata",
    )
    lower_layers = [
        layer for layer in _metadata_layers(profile_id, context)
        if layer.kind != "user"
    ]
    inherited, _, _ = _layer_value(lower_layers, "enabled")
    inherited = True if inherited is None else bool(inherited)
    if enabled == inherited:
        data.pop("enabled", None)
    else:
        data["enabled"] = enabled

    plan = ChangePlan(profile_id=profile_id)
    if data:
        plan.write(yaml_path, yaml_helper.dumps(data))
    else:
        plan.delete(yaml_path)
    return plan


def set_profile_enabled(
    profile_id: str,
    enabled: bool,
    context: Any | None = None,
) -> dict[str, Any]:
    profile_id = validate_profile_id(profile_id)
    project_name = _context_project_name(context)
    if not profile_exists(profile_id, context):
        raise ValueError(f'Agent profile "{profile_id}" does not exist.')

    with _MUTATION_LOCK:
        available = subagents.get_available_agents_dict(project_name or None)
        if not enabled and profile_id in available and len(available) == 1:
            raise ValueError("At least one agent profile must remain available.")

        if project_name:
            projects.set_project_subagent_enabled(project_name, profile_id, enabled)
            receipt = {
                "written": [
                    _relative_source(
                        Path(projects.get_project_meta(project_name, "agents.json"))
                    )
                ],
                "deleted": [],
                "warnings": [],
            }
        else:
            receipt = apply_change_plan(
                plan_profile_enabled(profile_id, enabled, context)
            )

    if not enabled:
        projects.reconcile_agent_profiles(
            project_name or None, all_scopes=not project_name
        )
    return receipt


def plan_duplicate_profile(
    profile_id: str,
    context: Any | None = None,
) -> tuple[ChangePlan, str]:
    profile_id = validate_profile_id(profile_id)
    if not profile_exists(profile_id, context):
        raise ValueError(f'Agent profile "{profile_id}" does not exist.')

    state = metadata_state(profile_id, context)
    source_title = str(state["title"]["effective"] or profile_id).strip() or profile_id
    index = 1
    while True:
        suffix = f"-{index}"
        stem = profile_id[: 64 - len(suffix)].rstrip("-_")
        target_id = f"{stem}{suffix}"
        if not profile_exists(target_id, context):
            break
        index += 1

    target_title = f"{source_title} {index}"
    project_name = _context_project_name(context)
    target_root = _profile_root(target_id, project_name)
    plan = ChangePlan(
        profile_id=target_id,
        project_name=project_name,
        creating=True,
    )

    metadata: dict[str, Any] = {}
    for layer in _metadata_layers(profile_id, context):
        metadata.update(layer.data)
    for key in ("name", "path", "origin", "prompts", "enabled"):
        metadata.pop(key, None)
    metadata["title"] = target_title
    plan.write(target_root / "agent.yaml", yaml_helper.dumps(metadata))

    skipped = {"agent.yaml", "agent.json", "AGENTS.md"}
    for _, source_root in _profile_directories(profile_id, context):
        if not source_root.is_dir():
            continue
        if source_root.is_symlink():
            raise ValueError("Profile symlinks must be removed before duplication.")
        for source in sorted(source_root.rglob("*")):
            if source.is_symlink():
                raise ValueError("Profile symlinks must be removed before duplication.")
            if source.is_file() and source.name not in skipped:
                plan.write(target_root / source.relative_to(source_root), source.read_bytes())

    return plan, target_title


def _plan_metadata(
    plan: ChangePlan,
    value: Any,
    context: Any | None,
    *,
    creating: bool,
) -> None:
    section = _mapping(value, "metadata")
    set_values = _mapping(section.get("set", {}), "metadata.set")
    reset_values = _string_list(section.get("reset", []), "metadata.reset")
    unknown = (set(set_values) | set(reset_values)) - set(METADATA_KEYS)
    if unknown:
        raise ValueError(f"Unknown metadata field: {sorted(unknown)[0]}")
    if set(set_values).intersection(reset_values):
        raise ValueError("A metadata field cannot be set and reset in one save.")

    profile_id = plan.profile_id
    profile_root = _profile_root(profile_id, plan.project_name)
    yaml_path = profile_root / "agent.yaml"
    legacy_path = profile_root / "agent.json"
    data = _read_mapping_strict(
        yaml_path if yaml_path.is_file() else legacy_path,
        "profile metadata",
    )
    state = metadata_state(profile_id, context)
    current_user_avatar = data.get("avatar")

    for key in reset_values:
        data.pop(key, None)
        if key == "avatar" and _editor_image_avatar(current_user_avatar):
            plan.delete(profile_root / "assets" / "avatar.webp")

    for key, raw in set_values.items():
        if key in {"title", "description", "context"}:
            if not isinstance(raw, str):
                raise ValueError(f"Metadata field {key} must be text.")
            normalized: Any = raw
            if key == "title" and not raw.strip():
                raise ValueError("Agent name is required.")
        else:
            normalized = _normalize_avatar(plan, raw)
            if normalized.get("kind") == "color" and _editor_image_avatar(
                current_user_avatar
            ):
                plan.delete(profile_root / "assets" / "avatar.webp")

        inherited = state[key]["inherited"]
        if not creating and normalized == inherited:
            data.pop(key, None)
        else:
            data[key] = normalized

    if data:
        plan.write(yaml_path, yaml_helper.dumps(data))
    else:
        plan.delete(yaml_path)


def _plan_prompts(
    plan: ChangePlan,
    value: Any,
    context: Any | None,
    *,
    creating: bool,
    easy: bool,
) -> None:
    section = _mapping(value, "prompts")
    set_values = _mapping(section.get("set", {}), "prompts.set")
    reset_values = _string_list(section.get("reset", []), "prompts.reset")
    if set(set_values).intersection(reset_values):
        raise ValueError("A prompt cannot be set and reset in one save.")

    agent = EditorAgent(plan.profile_id, context)
    catalog = {item["filename"]: item for item in prompt_catalog(agent)}
    for filename in [*set_values, *reset_values]:
        if filename not in catalog:
            raise ValueError(f'Prompt file "{filename}" is not in the editor catalog.')

    total = 0
    for filename, content in set_values.items():
        if not isinstance(content, str):
            raise ValueError(f'Prompt file "{filename}" must contain UTF-8 text.')
        if "\x00" in content:
            raise ValueError(f'Prompt file "{filename}" contains a NUL character.')
        payload_size = len(content.encode("utf-8"))
        if payload_size > MAX_PROMPT_BYTES:
            raise ValueError(f'Prompt file "{filename}" is too large.')
        total += payload_size
        if easy and filename == SPECIFICS_FILE and not content.strip():
            raise ValueError(
                "Instructions can’t be empty. To remove your changes, use "
                "Restore original instructions."
            )
        item = catalog[filename]
        path = _profile_root(plan.profile_id, plan.project_name) / "prompts" / filename
        if (
            not creating
            and item.get("inherited_source")
            and content == item.get("inherited", "")
        ):
            plan.delete(path)
        else:
            plan.write(path, content)

    if total > MAX_PROMPTS_BYTES:
        raise ValueError("The combined prompt changes are too large.")
    for filename in reset_values:
        plan.delete(
            _profile_root(plan.profile_id, plan.project_name) / "prompts" / filename
        )


def _plan_model_preset(plan: ChangePlan, value: Any) -> None:
    section = _mapping(value, "model_preset")
    mode = str(section.get("mode") or "inherit").strip().lower()
    path = _profile_config_path(plan.profile_id, "_model_config", plan.project_name)
    data = _read_mapping_strict(path, "model preset configuration")

    from plugins._model_config.helpers import model_config

    if mode == "inherit":
        data.pop(model_config.MODEL_PRESET_CONFIG_KEY, None)
    elif mode == "preset":
        requested = str(section.get("name") or "").strip()
        preset = model_config.resolve_preset(requested)
        if not preset:
            raise ValueError(f'Model preset "{requested}" does not exist.')
        data[model_config.MODEL_PRESET_CONFIG_KEY] = str(preset.get("name") or requested)
    else:
        raise ValueError("Model preset mode must be inherit or preset.")
    _plan_json_mapping(plan, path, data)


def _plan_tool_policy(plan: ChangePlan, value: Any) -> None:
    section = _mapping(value, "tool_policy")
    mode = str(section.get("mode") or "inherit").strip().lower()
    path = _profile_config_path(
        plan.profile_id,
        tool_policy.PLUGIN_NAME,
        plan.project_name,
    )
    data = _read_mapping_strict(path, "tool policy configuration")

    if mode == "inherit":
        for key in _TOOL_POLICY_KEYS:
            data.pop(key, None)
    else:
        if mode == "off":
            policy = {
                "mode": "custom",
                "default": "block",
                "mcp_default": "block",
                "allowed": [],
                "blocked": [],
            }
        elif mode == "custom":
            policy = tool_policy.normalize_policy(section)
            allowed = set(policy["allowed"])
            blocked = set(policy["blocked"])
            if allowed.intersection(blocked):
                raise ValueError("A tool cannot be both allowed and blocked.")
            for tool_id in [*policy["allowed"], *policy["blocked"]]:
                if not _valid_tool_id(tool_id):
                    raise ValueError(f'Invalid canonical tool ID "{tool_id}".')
        else:
            raise ValueError("Tool policy mode must be inherit, off, or custom.")
        data.update({key: policy[key] for key in _TOOL_POLICY_KEYS})
    _plan_json_mapping(plan, path, data)


def _plan_skill_policy(plan: ChangePlan, value: Any) -> None:
    section = _mapping(value, "skill_policy")
    mode = str(section.get("mode") or "inherit").strip().lower()
    path = _profile_config_path(
        plan.profile_id,
        skills.ACTIVE_SKILLS_PLUGIN_NAME,
        plan.project_name,
    )
    data = _read_mapping_strict(path, "skill policy configuration")

    if mode == "inherit":
        data.pop("visibility_policy", None)
    else:
        raw = (
            {"mode": "custom", "default": "block", "allowed": [], "blocked": []}
            if mode == "off"
            else section
        )
        if mode not in {"off", "custom"}:
            raise ValueError("Skill policy mode must be inherit, off, or custom.")
        policy = skills.normalize_visibility_policy(raw)
        if set(policy["allowed"]).intersection(policy["blocked"]):
            raise ValueError("A skill cannot be both allowed and blocked.")
        for skill_id in [*policy["allowed"], *policy["blocked"]]:
            if not skill_id or len(skill_id) > 512 or "\x00" in skill_id:
                raise ValueError("Invalid skill ID.")
        data["visibility_policy"] = policy
    _plan_json_mapping(plan, path, data)


def _normalize_avatar(plan: ChangePlan, value: Any) -> dict[str, str]:
    avatar = _mapping(value, "metadata.set.avatar")
    kind = str(avatar.get("kind") or "").strip().lower()
    if kind == "color":
        color = str(avatar.get("value") or "").strip().upper()
        if not COLOR_PATTERN.fullmatch(color):
            raise ValueError("Avatar color must be a six-digit hex color.")
        return {"kind": "color", "value": color}
    if kind == "image":
        token = str(avatar.get("token") or "").strip()
        if token:
            source = staged_avatar_path(token)
            if not source.is_file():
                raise ValueError("The staged avatar has expired. Upload it again.")
            plan.write(
                _profile_root(plan.profile_id, plan.project_name)
                / "assets"
                / "avatar.webp",
                source.read_bytes(),
            )
            plan.staged_tokens.add(token)
            return {"kind": "image", "value": "assets/avatar.webp"}
    raise ValueError("Avatar must be a color or a staged image.")


def _plan_json_mapping(plan: ChangePlan, path: Path, data: dict[str, Any]) -> None:
    if data:
        plan.write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    else:
        plan.delete(path)


def _planned_mapping(plan: ChangePlan, path: Path) -> dict[str, Any]:
    change = plan.changes.get(path)
    if change and change.action == "delete":
        return {}
    if change and change.content is not None:
        value = yaml_helper.loads(change.content.decode("utf-8"))
        return dict(value) if isinstance(value, dict) else {}
    return _read_mapping(path)


def _read_mapping_strict(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.suffix.lower() == ".json"
            else yaml_helper.loads(path.read_text(encoding="utf-8"))
        )
    except Exception as exc:
        raise ValueError(f"Existing {label} is invalid and was not changed: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Existing {label} must be an object and was not changed.")
    return dict(value)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object.")
    return dict(value)


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be an array of strings.")
    return list(dict.fromkeys(value))


def _valid_tool_id(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"(?:local:[^\s/:]+|(?:mcp|plugin):[^\s/:]+:[^\s/:]+)",
            value,
        )
    )


def _editor_image_avatar(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("kind") == "image"
        and value.get("value") == "assets/avatar.webp"
    )


def apply_change_plan(plan: ChangePlan) -> dict[str, Any]:
    project_name = (
        projects.validate_project_name(plan.project_name) if plan.project_name else ""
    )
    if project_name and not Path(projects.get_project_folder(project_name)).is_dir():
        raise ValueError("Project not found.")
    root = _profile_root(
        validate_profile_id(plan.profile_id),
        project_name,
    )
    changes = sorted(plan.changes.values(), key=lambda item: str(item.path))
    _validate_plan_paths(root, changes)
    receipt = plan.response()

    with _MUTATION_LOCK:
        if plan.creating and profile_exists(
            plan.profile_id,
            _EditorContext(project_name),
        ):
            raise ValueError(
                f'Agent profile "{plan.profile_id}" was created before this save completed.'
            )
        snapshots = {
            change.path: change.path.read_bytes() if change.path.is_file() else None
            for change in changes
        }
        staged: dict[Path, Path] = {}
        created_dirs: set[Path] = set()
        try:
            for change in changes:
                if change.action != "write":
                    continue
                _ensure_parent(change.path.parent, created_dirs)
                staged[change.path] = _stage_bytes(
                    change.path.parent,
                    change.path.name,
                    change.content or b"",
                )

            for change in changes:
                if change.action == "write":
                    os.replace(staged.pop(change.path), change.path)
                    _fsync_directory(change.path.parent)
                elif change.path.is_file() or change.path.is_symlink():
                    change.path.unlink()
                    _fsync_directory(change.path.parent)

            if plan.remove_empty_root:
                _prune_empty_directories(root)
                if root.is_dir() and not any(root.iterdir()):
                    root.rmdir()
        except Exception:
            for temporary in staged.values():
                temporary.unlink(missing_ok=True)
            _restore_snapshots(snapshots, root)
            for directory in sorted(created_dirs, key=lambda path: len(path.parts), reverse=True):
                try:
                    directory.rmdir()
                except OSError:
                    pass
            raise

    for token in plan.staged_tokens:
        staged_avatar_path(token).unlink(missing_ok=True)
    _invalidate_profile_caches()
    return receipt


def plan_remove_changes(
    profile_id: str,
    context: Any | None = None,
    *,
    destructive: bool = False,
) -> ChangePlan:
    profile_id = validate_profile_id(profile_id)
    if not profile_exists(profile_id, context):
        raise ValueError(f'Agent profile "{profile_id}" does not exist.')
    if destructive:
        return _full_delete_plan(profile_id, context)

    catalog = prompt_catalog(EditorAgent(profile_id, context))
    prompt_resets = [
        item["filename"]
        for item in catalog
        if item.get("has_override") and item.get("inherited_source")
    ]
    plan = build_change_plan(
        {
            "profile_id": profile_id,
            "metadata": {"set": {}, "reset": list(METADATA_KEYS)},
            "prompts": {"set": {}, "reset": prompt_resets},
            "model_preset": {"mode": "inherit"},
            "tool_policy": {"mode": "inherit"},
            "skill_policy": {"mode": "inherit"},
        },
        context,
    )
    return plan


def plan_delete_custom(profile_id: str, context: Any | None = None) -> ChangePlan:
    profile_id = validate_profile_id(profile_id)
    state = metadata_state(profile_id, context)
    if not state["deletable"]:
        raise ValueError("Only custom agents created in this scope can be deleted.")
    return _full_delete_plan(profile_id, context)


def delete_impact(profile_id: str, context: Any | None = None) -> dict[str, Any]:
    profile_id = validate_profile_id(profile_id)
    state = metadata_state(profile_id, context)
    project_name = _context_project_name(context)
    root = _profile_root(profile_id, project_name)
    file_paths = [
        _relative_source(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() or path.is_symlink()
    ] if root.is_dir() else []
    references = _profile_reference_paths(profile_id, project_name)
    sessions: list[str] = []
    try:
        from agent import AgentContext

        sessions = [
            str(item.id)
            for item in AgentContext.all()
            if str(getattr(getattr(item.agent0, "config", None), "profile", ""))
            == profile_id
            and (
                not project_name
                or projects.get_context_project_name(item) == project_name
            )
        ]
    except Exception:
        pass

    model_config = _read_mapping(
        _profile_config_path(profile_id, "_model_config", project_name)
    )
    return {
        "profile_id": profile_id,
        "deletable": state["deletable"],
        "origin": state["origin"],
        "project_name": project_name,
        "files": file_paths,
        "project_references": references,
        "active_sessions": sessions,
        "model_preset": str(model_config.get("model_preset") or ""),
        "contains": {
            name: (root / name).is_dir()
            for name in ("tools", "extensions", "skills", "assets", "plugins")
        },
    }


def stage_avatar(upload: Any) -> dict[str, Any]:
    if upload is None:
        raise ValueError("Choose an image to upload.")
    payload = upload.stream.read(MAX_AVATAR_BYTES + 1)
    if len(payload) > MAX_AVATAR_BYTES:
        raise ValueError("Avatar images must be 8 MB or smaller.")
    if not payload:
        raise ValueError("The uploaded image is empty.")

    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        with Image.open(BytesIO(payload)) as source:
            source_format = str(source.format or "").upper()
            if source_format not in {"PNG", "JPEG", "WEBP"}:
                raise ValueError("Avatar must be a PNG, JPEG, or WebP image.")
            if max(source.size) > MAX_AVATAR_DIMENSION:
                raise ValueError("Avatar dimensions must not exceed 4096 pixels.")
            source.load()
            normalized = ImageOps.exif_transpose(source)
            mode = "RGBA" if "A" in normalized.getbands() else "RGB"
            square = ImageOps.fit(
                normalized.convert(mode),
                (AVATAR_SIZE, AVATAR_SIZE),
                method=Image.Resampling.LANCZOS,
            )
            output = BytesIO()
            square.save(output, format="WEBP", quality=88, method=6)
    except UnidentifiedImageError as exc:
        raise ValueError("Avatar must be a valid PNG, JPEG, or WebP image.") from exc
    except Image.DecompressionBombError as exc:
        raise ValueError("Avatar dimensions are too large.") from exc
    except OSError as exc:
        raise ValueError("Avatar must be a valid PNG, JPEG, or WebP image.") from exc

    _cleanup_staged_avatars()
    STAGED_AVATAR_ROOT.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    path = staged_avatar_path(token)
    temporary = _stage_bytes(path.parent, path.name, output.getvalue())
    os.replace(temporary, path)
    return {"token": token}


def staged_avatar_path(token: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", str(token or "")):
        raise ValueError("Invalid staged avatar token.")
    return STAGED_AVATAR_ROOT / f"{token}.webp"


def _full_delete_plan(
    profile_id: str,
    context: Any | None = None,
) -> ChangePlan:
    project_name = _context_project_name(context)
    root = _profile_root(profile_id, project_name)
    plan = ChangePlan(
        profile_id=profile_id,
        project_name=project_name,
        remove_empty_root=True,
    )
    if not root.is_dir():
        return plan
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Profile symlinks must be removed manually before deletion.")
        if path.is_file():
            plan.delete(path)
    return plan


def _validate_plan_paths(root: Path, changes: list[FileChange]) -> None:
    intended_root = root.absolute()
    if root.is_symlink():
        raise ValueError("The profile directory cannot be a symlink.")
    for change in changes:
        if change.action not in {"write", "delete"}:
            raise ValueError("Invalid change-plan action.")
        resolved = change.path.resolve(strict=False)
        if not files.is_in_dir(str(resolved), str(intended_root)):
            raise ValueError("A planned path is outside the selected profile directory.")
        cursor = change.path.parent
        while files.is_in_dir(str(cursor), str(intended_root)):
            if cursor.is_symlink():
                raise ValueError("Profile paths cannot traverse symlinks.")
            if cursor == root:
                break
            cursor = cursor.parent
        if change.action == "delete" and change.path.exists() and not (
            change.path.is_file() or change.path.is_symlink()
        ):
            raise ValueError("Change plans delete files, not directories.")


def _ensure_parent(parent: Path, created: set[Path]) -> None:
    missing: list[Path] = []
    cursor = parent
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    for directory in reversed(missing):
        directory.mkdir(exist_ok=True)
        created.add(directory)


def _stage_bytes(directory: Path, name: str, content: bytes) -> Path:
    target = directory / name
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{name}.", suffix=".tmp", dir=directory
    )
    path = Path(temporary)
    try:
        os.fchmod(
            descriptor,
            target.stat().st_mode & 0o777 if target.exists() else 0o644,
        )
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _restore_snapshots(snapshots: dict[Path, bytes | None], root: Path) -> None:
    for path, content in snapshots.items():
        if content is None:
            if path.is_file() or path.is_symlink():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = _stage_bytes(path.parent, path.name, content)
        os.replace(temporary, path)


def _prune_empty_directories(root: Path) -> None:
    if not root.is_dir():
        return
    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _invalidate_profile_caches() -> None:
    cache.clear(subagents.PATHS_CACHE_AREA)
    plugins.clear_plugin_cache(
        ["_agent_editor", "_model_config", tool_policy.PLUGIN_NAME, skills.ACTIVE_SKILLS_PLUGIN_NAME]
    )


def _cleanup_staged_avatars() -> None:
    if not STAGED_AVATAR_ROOT.is_dir():
        return
    cutoff = time.time() - 3600
    for path in STAGED_AVATAR_ROOT.glob("*.webp"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            pass


def _profile_reference_paths(profile_id: str, project_name: str = "") -> list[str]:
    root = (
        Path(projects.get_project_meta(project_name))
        if project_name
        else Path(files.get_abs_path("usr", "projects"))
    )
    if not root.is_dir():
        return []
    references: list[str] = []
    for suffix in ("*.json", "*.yaml", "*.yml"):
        pattern = f"**/{suffix}" if project_name else f"*/.a0proj/**/{suffix}"
        for path in root.glob(pattern):
            try:
                if profile_id in path.read_text(encoding="utf-8"):
                    references.append(_relative_source(path))
            except (OSError, UnicodeError):
                pass
    return sorted(set(references))
