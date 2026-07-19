from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, TYPE_CHECKING, TypedDict

from helpers import files, subagents, projects, file_tree, runtime
from helpers import plugins as plugin_helpers

if TYPE_CHECKING:
    from agent import Agent

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


MAX_ACTIVE_SKILLS = 20
ACTIVE_SKILLS_PLUGIN_NAME = "_skills"
AGENT_DATA_NAME_LOADED_SKILLS = "loaded_skills"
CONTEXT_DATA_NAME_CHAT_ACTIVE_SKILLS = "skills_chat_active"
CONTEXT_DATA_NAME_CHAT_DISABLED_SKILLS = "skills_chat_disabled"


class ActiveSkillEntry(TypedDict, total=False):
    name: str
    path: str


class CatalogSkill(TypedDict):
    name: str
    description: str
    path: str
    origin: str


@dataclass(slots=True)
class Skill:
    name: str
    description: str
    path: Path
    skill_md_path: Path
    version: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    license: str = ""
    compatibility: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional heavy fields (only set when requested)
    content: str = ""  # body content (markdown without frontmatter)
    raw_frontmatter: Dict[str, Any] = field(default_factory=dict)


def get_skills_base_dir() -> Path:
    return Path(files.get_abs_path("usr", "skills"))


def get_skill_roots(
    agent: Agent|None=None,
) -> List[str]:

    if agent:
        # skill roots available to agent
        paths = subagents.get_paths(agent, "skills")
    else:
        # skill roots available globally
        project_agents = files.find_existing_paths_by_pattern("usr/projects/*/.a0proj/agents/*/skills") # agents in projects
        projects = files.find_existing_paths_by_pattern("usr/projects/*/.a0proj/skills") # projects
        usr_agents = files.find_existing_paths_by_pattern("usr/agents/*/skills") # agents
        agents = files.find_existing_paths_by_pattern("agents/*/skills") # agents
        plugins = files.find_existing_paths_by_pattern("plugins/*/skills") # plugins
        usr_plugins = files.find_existing_paths_by_pattern("usr/plugins/*/skills") # plugins
        plugins_agents = files.find_existing_paths_by_pattern("plugins/*/agents/*/skills") # agents in plugins
        usr_plugins_agents = files.find_existing_paths_by_pattern("usr/plugins/*/agents/*/skills") # agents in plugins
        paths = [
            files.get_abs_path("skills"), 
            files.get_abs_path("usr/skills"),
            *project_agents,
            *projects,
            *usr_agents,
            *agents,
            *plugins,
            *usr_plugins,
            *plugins_agents,
            *usr_plugins_agents,
        ]
    return paths


def _is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def discover_skill_md_files(root: Path) -> List[Path]:
    """
    Recursively discover SKILL.md files under a root directory.
    Hidden folders/files are ignored.
    """
    if not root.exists():
        return []

    results: List[Path] = []
    for p in root.rglob("SKILL.md"):
        try:
            if not p.is_file():
                continue
            if _is_hidden_path(p.relative_to(root)):
                continue
            results.append(p)
        except Exception:
            # If relative_to fails (weird symlink), fall back to conservative checks
            if p.is_file() and ".git" not in str(p):
                results.append(p)
    results.sort(key=lambda x: str(x))
    return results


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, tuple):
        return [str(v).strip() for v in list(value) if str(v).strip()]
    if isinstance(value, str):
        # Support comma-separated or space-delimited strings
        if "," in value:
            parts = [p.strip() for p in value.split(",")]
        else:
            parts = [p.strip() for p in re.split(r"\s+", value)]
        return [p for p in parts if p]
    return [str(value).strip()] if str(value).strip() else []


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", "-", (name or "").strip().lower())


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_frontmatter(markdown: str) -> Tuple[Dict[str, Any], str, List[str]]:
    """
    Splits a SKILL.md into (frontmatter_dict, body_text, errors).
    Enforces YAML frontmatter at the top for spec compatibility.
    """
    errors: List[str] = []
    text = markdown or ""
    lines = text.splitlines()

    # Require frontmatter fence at the start (allow leading whitespace/newlines).
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            start_idx = i
            break
        if line.strip():  # non-empty before fence => invalid
            errors.append("Frontmatter must start at the top of the file")
            return {}, text.strip(), errors

    if start_idx is None:
        errors.append("Missing YAML frontmatter")
        return {}, text.strip(), errors

    end_idx = None
    for j in range(start_idx + 1, len(lines)):
        if lines[j].strip() == "---":
            end_idx = j
            break

    if end_idx is None:
        errors.append("Unterminated YAML frontmatter")
        return {}, text.strip(), errors

    fm_text = "\n".join(lines[start_idx + 1 : end_idx]).strip()
    body = "\n".join(lines[end_idx + 1 :]).strip()
    fm, fm_errors = parse_frontmatter(fm_text)
    errors.extend(fm_errors)
    return fm, body, errors


def _parse_frontmatter_fallback(frontmatter_text: str) -> Dict[str, Any]:
    # Minimal YAML subset: key: value, lists with "- item"
    data: Dict[str, Any] = {}
    current_key: Optional[str] = None
    for raw in frontmatter_text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue

        m = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            current_key = key
            if val == "":
                data[key] = []
            else:
                if (val.startswith('"') and val.endswith('"')) or (
                    val.startswith("'") and val.endswith("'")
                ):
                    val = val[1:-1]
                data[key] = val
            continue

        m_list = re.match(r"^\s*-\s*(.*)$", line)
        if m_list and current_key:
            item = m_list.group(1).strip()
            if (item.startswith('"') and item.endswith('"')) or (
                item.startswith("'") and item.endswith("'")
            ):
                item = item[1:-1]
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(item)
            continue
    return data


def parse_frontmatter(frontmatter_text: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    Parse YAML frontmatter with PyYAML when available,
    falling back to a minimal subset parser.
    """
    errors: List[str] = []
    if not frontmatter_text.strip():
        return {}, errors

    if yaml is not None:
        try:
            parsed = yaml.safe_load(frontmatter_text)  # type: ignore[attr-defined]
        except Exception as exc:
            errors.append(f"Invalid YAML frontmatter: {exc}")
            return {}, errors
        if parsed is not None:
            if not isinstance(parsed, dict):
                errors.append("Frontmatter must be a mapping")
                return {}, errors
            return parsed, errors

    parsed = _parse_frontmatter_fallback(frontmatter_text)
    if not parsed:
        errors.append("Invalid YAML frontmatter")
    return parsed, errors


def skill_from_markdown(
    skill_md_path: Path,
    *,
    include_content: bool = False,
    validate: bool = True,
) -> Optional[Skill]:
    try:
        text = _read_text(skill_md_path)
    except Exception:
        return None

    fm, body, fm_errors = split_frontmatter(text)
    if fm_errors:
        return None
    skill_dir = Path(files.normalize_a0_path(str(skill_md_path.parent)))

    name = str(fm.get("name") or fm.get("skill") or "").strip()
    description = str(
        fm.get("description") or fm.get("when_to_use") or fm.get("summary") or ""
    ).strip()

    # Cross-platform aliases:
    # - Claude Code leans on description (triggers may be embedded there)
    # - Some repos use triggers/trigger_patterns
    triggers = _coerce_list(
        fm.get("triggers")
        or fm.get("trigger_patterns")
        or fm.get("trigger")
        or fm.get("activation")
    )

    tags = _coerce_list(fm.get("tags") or fm.get("tag"))
    allowed_tools = _coerce_list(
        fm.get("allowed-tools") or fm.get("allowed_tools") or fm.get("tools")
    )

    version = str(fm.get("version") or "").strip()
    author = str(fm.get("author") or "").strip()
    license_ = str(fm.get("license") or "").strip()
    compatibility = str(fm.get("compatibility") or "").strip()

    meta = fm.get("metadata")
    if not isinstance(meta, dict):
        meta = {}

    skill = Skill(
        name=name,
        description=description,
        path=skill_dir,
        skill_md_path=skill_md_path,
        version=version,
        author=author,
        tags=tags,
        triggers=triggers,
        allowed_tools=allowed_tools,
        license=license_,
        metadata=dict(meta),
        compatibility=compatibility,
        raw_frontmatter=fm if include_content else {},
        content=body if include_content else "",
    )
    if validate:
        issues = validate_skill(skill)
        if issues:
            return None
    return skill


def list_skills(
    agent:Agent|None=None,
    include_content: bool = False,
) -> List[Skill]:
    """List skills, optionally filtered by agent scope."""
    skills: List[Skill] = []

    roots = get_skill_roots(agent)

    for root in roots:
        for skill_md in discover_skill_md_files(Path(root)):
            s = skill_from_markdown(skill_md, include_content=include_content)
            if s:
                skills.append(s)

    # no deduplication for global skills
    if not agent:
        return skills

    # Dedupe by normalized name, preserving root_order priority (earlier wins)
    by_name: Dict[str, Skill] = {}
    for s in skills:
        key = _normalize_name(s.name) or _normalize_name(s.path.name)
        if key and key not in by_name:
            by_name[key] = s
    
    return list(by_name.values())


def delete_skill(
    skill_path: str,
) -> None:
    """Delete a skill directory."""

    skill_path = files.get_abs_path(skill_path)
    if runtime.is_development():
        skill_path = files.fix_dev_path(skill_path)

    normalized_path = files.normalize_a0_path(skill_path)
    if "/plugins/" in normalized_path and "/usr/plugins/" not in normalized_path:
        raise PermissionError("Built-in plugin skills cannot be deleted")

    allowed_roots = get_skill_roots()
    for root in allowed_roots:
        if files.is_in_dir(skill_path, root):
            break
    else:
        raise ValueError("Skill root not in current scope")

        
    if not os.path.isdir(skill_path):
        raise FileNotFoundError("Skill directory not found")

    # delete directory
    files.delete_dir(skill_path)


def find_skill(
    skill_name: str,
    agent:Agent|None=None,
    include_content: bool = False,
) -> Optional[Skill]:
    target = _normalize_name(skill_name)
    if not target:
        return None

    roots = get_skill_roots(agent)

    for root in roots:
        for skill_md in discover_skill_md_files(Path(root)):
            s = skill_from_markdown(skill_md, include_content=include_content)
            if not s:
                continue
            if _normalize_name(s.name) == target or _normalize_name(s.path.name) == target:
                return s
    return None

def load_skill_for_agent(
    skill_name: str,
    agent: Agent | None = None,
) -> str:
    """Load skill and format it as a complete string for agent context."""
    skill = find_skill(skill_name, agent=agent, include_content=True)
    if not skill:
        return f"Error: skill '{skill_name}' not found"

    # Get runtime path
    runtime_path = str(skill.path)
    if runtime.is_development():
        runtime_path = files.normalize_a0_path(str(skill.path))

    lines = [f"Skill: {skill.name}", f"Path: {runtime_path}"]

    # Metadata
    metadata = [
        ("Version", skill.version),
        ("Author", skill.author),
        ("License", skill.license),
        ("Compatibility", skill.compatibility),
        ("Tags", ", ".join(skill.tags) if skill.tags else None),
        ("Allowed tools", ", ".join(skill.allowed_tools) if skill.allowed_tools else None),
        ("Triggers", ", ".join(skill.triggers) if skill.triggers else None),
    ]
    lines.extend(f"{label}: {value}" for label, value in metadata if value)

    # Description and content
    if skill.description:
        lines.extend(["", "Description:", skill.description.strip()])

    lines.extend(["", "Content (SKILL.md body):", skill.content.strip() or "(empty)"])

    # File tree
    files_tree = _get_skill_files(skill.path)
    lines.append("")
    if files_tree:
        lines.append("Files (use skills_tool action=read_file to open):")
        lines.append(files_tree)
    else:
        lines.append("No additional files found.")

    return "\n".join(lines)


def _get_skill_files(skill_dir: Path) -> str:
    """Get file tree for skill directory."""
    if not skill_dir.exists():
        return ""

    tree = str(
        file_tree.file_tree(
            str(skill_dir),
            max_depth=10,
            folders_first=True,
            max_files=100,
            max_folders=100,
            output_mode="string",
            max_lines=300,
            ignore=files.read_file("conf/skill.default.gitignore"),
        )
    )

    if tree and runtime.is_development():
        runtime_path = files.normalize_a0_path(str(skill_dir))
        tree = tree.replace(str(skill_dir), runtime_path)

    return str(tree)

def search_skills(
    query: str,
    limit: int = 25,
    agent: Agent|None=None,
) -> List[Skill]:
    q = (query or "").strip().lower()
    if not q:
        return []

    raw_terms = [t for t in re.split(r"\s+", q) if t]
    terms = [
        t for t in raw_terms
        if len(t) >= 3 or any(ch.isdigit() for ch in t)
    ] or raw_terms
    candidates = list_skills(agent)

    scored: List[Tuple[int, Skill]] = []
    for s in candidates:
        name = s.name.lower()
        desc = (s.description or "").lower()
        tags = [t.lower() for t in s.tags]
        triggers = [t.lower() for t in s.triggers]

        score = 0
        if q == name:
            score += 10
        if any(q == trigger for trigger in triggers):
            score += 9
        if q in name:
            score += 6
        if q in desc:
            score += 4
        if any(q in tag for tag in tags):
            score += 3
        if any(q in trigger for trigger in triggers):
            score += 8

        for term in terms:
            if term in name:
                score += 3
            if term in desc:
                score += 2
            if any(term in tag for tag in tags):
                score += 1
            if any(term in trigger for trigger in triggers):
                score += 4

        if score > 0:
            scored.append((score, s))

    scored.sort(key=lambda pair: (-pair[0], pair[1].name))
    return [s for _score, s in scored[:limit]]


_NAME_RE = re.compile(r"^[a-z0-9-]+$")


def validate_skill(skill: Skill) -> List[str]:
    issues: List[str] = []
    name = (skill.name or "").strip()
    desc = (skill.description or "").strip()

    if not name:
        issues.append("Missing required field: name")
    else:
        if not (1 <= len(name) <= 64):
            issues.append("name must be 1-64 characters")
        if not _NAME_RE.match(name):
            issues.append("name must use lowercase letters, numbers, and hyphens only")
        if name.startswith("-") or name.endswith("-"):
            issues.append("name must not start or end with a hyphen")
        if "--" in name:
            issues.append("name must not contain consecutive hyphens")
        # if skill.path and _normalize_name(skill.path.name) != _normalize_name(name):
        #     issues.append("name should match the parent directory name")

    if not desc:
        issues.append("Missing required field: description")
    elif len(desc) > 1024:
        issues.append("description must be <= 1024 characters")

    if skill.compatibility and len(skill.compatibility) > 500:
        issues.append("compatibility must be <= 500 characters")

    return issues


def validate_skill_md(skill_md_path: Path) -> List[str]:
    try:
        text = _read_text(skill_md_path)
    except Exception:
        return ["Unable to read SKILL.md"]

    _fm, _body, fm_errors = split_frontmatter(text)
    if fm_errors:
        return fm_errors

    skill = skill_from_markdown(
        skill_md_path, include_content=False, validate=False
    )
    if not skill:
        return ["Unable to parse SKILL.md frontmatter"]
    return validate_skill(skill)


def get_max_active_skills() -> int:
    return MAX_ACTIVE_SKILLS


def normalize_skills_config(config: dict[str, Any] | None) -> dict[str, Any]:
    normalized = dict(config or {})
    normalized["active_skills"] = normalize_active_skills(
        normalized.get("active_skills")
    )
    return normalized


def normalize_active_skills(raw: Any) -> list[ActiveSkillEntry]:
    if not isinstance(raw, list):
        return []

    normalized: list[ActiveSkillEntry] = []
    seen: set[str] = set()

    for item in raw:
        entry = _normalize_active_skill_entry(item)
        if not entry:
            continue

        key = _entry_key(entry)
        if not key or key in seen:
            continue

        seen.add(key)
        normalized.append(entry)
        if len(normalized) >= get_max_active_skills():
            break

    return normalized


def list_skill_catalog(
    project_name: str = "",
    agent: Agent | None = None,
) -> list[CatalogSkill]:
    if not project_name:
        project_name = _get_agent_project_name(agent)

    catalog: list[CatalogSkill] = []
    seen_paths: set[str] = set()

    for root in _get_catalog_roots(project_name=project_name, agent=agent):
        root_path = Path(root)
        for skill_md in discover_skill_md_files(root_path):
            skill = skill_from_markdown(skill_md, include_content=False)
            if not skill:
                continue

            runtime_path = files.normalize_a0_path(str(skill.path))
            if runtime_path in seen_paths:
                continue

            seen_paths.add(runtime_path)
            catalog.append(
                {
                    "name": skill.name or skill.path.name,
                    "description": skill.description or "",
                    "path": runtime_path,
                    "origin": _get_skill_origin(
                        runtime_path,
                        project_name=project_name,
                    ),
                }
            )

    catalog.sort(key=lambda item: (item["name"].lower(), item["path"]))
    return catalog


def get_scope_active_skills(agent: Agent | None) -> list[ActiveSkillEntry]:
    if not agent:
        return []

    project_name = _get_agent_project_name(agent)
    config = (
        plugin_helpers.get_plugin_config(
            ACTIVE_SKILLS_PLUGIN_NAME,
            agent=agent,
            project_name=project_name,
            agent_profile="",
        )
        or {}
    )
    return normalize_active_skills(config.get("active_skills"))


def get_chat_active_skills(context: Any | None) -> list[ActiveSkillEntry]:
    if not context:
        return []
    return normalize_active_skills(context.get_data(CONTEXT_DATA_NAME_CHAT_ACTIVE_SKILLS))


def get_chat_disabled_skills(context: Any | None) -> list[ActiveSkillEntry]:
    if not context:
        return []
    return normalize_active_skills(
        context.get_data(CONTEXT_DATA_NAME_CHAT_DISABLED_SKILLS)
    )


def _build_active_skills(
    agent: Agent | None,
    *,
    chat_entries: list[ActiveSkillEntry] | None = None,
    disabled_entries: list[ActiveSkillEntry] | None = None,
    limit: int | None = None,
) -> list[ActiveSkillEntry]:
    if not agent:
        return []

    context = getattr(agent, "context", None)
    effective_limit = get_max_active_skills() if limit is None else limit
    scope_entries = get_scope_active_skills(agent)
    current_chat_entries = list(
        chat_entries if chat_entries is not None else get_chat_active_skills(context)
    )
    current_disabled_entries = list(
        disabled_entries
        if disabled_entries is not None
        else get_chat_disabled_skills(context)
    )
    return _merge_active_skill_entries(
        scope_entries,
        current_chat_entries,
        current_disabled_entries,
        limit=effective_limit,
    )


def get_active_skills(agent: Agent | None) -> list[ActiveSkillEntry]:
    return _build_active_skills(agent, limit=get_max_active_skills())


def get_loaded_skill_entries(agent: Agent | None) -> list[ActiveSkillEntry]:
    if not agent:
        return []

    loaded = getattr(agent, "data", {}).get(AGENT_DATA_NAME_LOADED_SKILLS)
    if not isinstance(loaded, list):
        return []

    return [
        {"name": str(skill_name).strip()}
        for skill_name in loaded
        if str(skill_name).strip()
    ]


def unload_agent_skill(agent: Agent | None, entry: Any) -> bool:
    normalized = _normalize_active_skill_entry(entry)
    if not agent or not normalized:
        return False

    data = getattr(agent, "data", None)
    if not isinstance(data, dict):
        return False

    loaded = data.get(AGENT_DATA_NAME_LOADED_SKILLS)
    if not isinstance(loaded, list):
        return False

    next_loaded: list[str] = []
    removed = False
    for skill_name in loaded:
        loaded_entry = _normalize_active_skill_entry(str(skill_name))
        if loaded_entry and _entries_match(loaded_entry, normalized):
            removed = True
            continue
        next_loaded.append(skill_name)

    if removed:
        data[AGENT_DATA_NAME_LOADED_SKILLS] = next_loaded
    return removed


def activate_chat_skill(agent: Agent, entry: Any) -> list[ActiveSkillEntry]:
    normalized = _normalize_active_skill_entry(entry)
    if not normalized:
        raise ValueError("A skill name or path is required.")

    context = getattr(agent, "context", None)
    if not context:
        raise ValueError("A chat context is required.")

    scope_entries = get_scope_active_skills(agent)
    chat_entries = [
        item
        for item in get_chat_active_skills(context)
        if not _entries_match(item, normalized)
    ]
    disabled_entries = [
        item
        for item in get_chat_disabled_skills(context)
        if not _entries_match(item, normalized)
    ]

    if not any(_entries_match(item, normalized) for item in scope_entries):
        chat_entries.append(normalized)

    merged_entries = _build_active_skills(
        agent,
        chat_entries=chat_entries,
        disabled_entries=disabled_entries,
        limit=-1,
    )
    if len(merged_entries) > get_max_active_skills():
        raise ValueError(
            f"You can activate at most {get_max_active_skills()} skills."
        )

    _store_context_active_skill_entries(
        context,
        CONTEXT_DATA_NAME_CHAT_ACTIVE_SKILLS,
        chat_entries,
    )
    _store_context_active_skill_entries(
        context,
        CONTEXT_DATA_NAME_CHAT_DISABLED_SKILLS,
        disabled_entries,
    )
    return get_active_skills(agent)


def deactivate_chat_skill(agent: Agent, entry: Any) -> list[ActiveSkillEntry]:
    normalized = _normalize_active_skill_entry(entry)
    if not normalized:
        raise ValueError("A skill name or path is required.")

    context = getattr(agent, "context", None)
    if not context:
        raise ValueError("A chat context is required.")

    chat_entries = [
        item
        for item in get_chat_active_skills(context)
        if not _entries_match(item, normalized)
    ]
    disabled_entries = [
        item
        for item in get_chat_disabled_skills(context)
        if not _entries_match(item, normalized)
    ]

    is_scope_default = any(
        _entries_match(item, normalized) for item in get_scope_active_skills(agent)
    )
    if is_scope_default:
        disabled_entries.append(normalized)

    _store_context_active_skill_entries(
        context,
        CONTEXT_DATA_NAME_CHAT_ACTIVE_SKILLS,
        chat_entries,
    )
    _store_context_active_skill_entries(
        context,
        CONTEXT_DATA_NAME_CHAT_DISABLED_SKILLS,
        disabled_entries,
    )
    return get_active_skills(agent)


def clear_chat_skill_overrides(agent: Agent) -> list[ActiveSkillEntry]:
    context = getattr(agent, "context", None)
    if not context:
        raise ValueError("A chat context is required.")

    _store_context_active_skill_entries(context, CONTEXT_DATA_NAME_CHAT_ACTIVE_SKILLS, [])
    _store_context_active_skill_entries(context, CONTEXT_DATA_NAME_CHAT_DISABLED_SKILLS, [])
    return get_active_skills(agent)


def build_active_skills_prompt(agent: Agent | None) -> str:
    items = _resolve_active_skill_entries(agent, get_active_skills(agent))
    return "\n\n".join(item["content"] for item in items if item.get("content")).strip()


def _format_skill_prompt(skill: Skill) -> str:
    lines = [
        f"Skill: {skill.name or skill.path.name}",
        f"Path: {files.normalize_a0_path(str(skill.path))}",
    ]

    if skill.description:
        lines.extend(["", "Description:", skill.description.strip()])

    lines.extend(["", "Instructions:", (skill.content or "").strip() or "(empty)"])
    return "\n".join(lines)


def _get_skill_origin(skill_path: str, project_name: str = "") -> str:
    abs_path = files.fix_dev_path(skill_path)

    if project_name:
        project_root = projects.get_project_meta(project_name, "skills")
        if files.exists(project_root) and files.is_in_dir(abs_path, project_root):
            return "Project"

    user_root = files.get_abs_path("usr", "skills")
    if files.exists(user_root) and files.is_in_dir(abs_path, user_root):
        return "User"

    normalized_path = files.normalize_a0_path(abs_path)
    if "/usr/plugins/" in normalized_path:
        return "Community plugin"
    if "/plugins/" in normalized_path:
        return "Built-in plugin"
    return "Built-in"


def _normalize_active_skill_entry(item: Any) -> ActiveSkillEntry | None:
    if isinstance(item, str):
        stripped = item.strip()
        if not stripped:
            return None
        if "/" in stripped:
            return {"path": _normalize_active_skill_path(stripped)}
        return {"name": stripped}

    if not isinstance(item, dict):
        return None

    name = str(item.get("name") or "").strip()
    path = str(item.get("path") or "").strip()

    if path:
        path = _normalize_active_skill_path(path)
    if not (path or name):
        return None

    entry: ActiveSkillEntry = {}
    if name:
        entry["name"] = name
    if path:
        entry["path"] = path
    return entry


def _normalize_active_skill_path(path: str) -> str:
    fixed = path.strip().replace("\\", "/")
    if fixed.startswith("/a0/"):
        return fixed.rstrip("/")
    if fixed.startswith("/"):
        return files.normalize_a0_path(fixed).rstrip("/")
    return files.normalize_a0_path(files.get_abs_path(fixed)).rstrip("/")


def _entry_key(entry: ActiveSkillEntry) -> str:
    return str(entry.get("path") or entry.get("name") or "").strip().lower()


def _entry_keys(entry: ActiveSkillEntry) -> set[str]:
    keys: set[str] = set()
    for value in (entry.get("path"), entry.get("name")):
        key = str(value or "").strip().lower()
        if key:
            keys.add(key)
    return keys


def _entries_match(left: ActiveSkillEntry, right: ActiveSkillEntry) -> bool:
    return bool(_entry_keys(left) & _entry_keys(right))


def _get_agent_project_name(agent: Agent | None) -> str:
    context = getattr(agent, "context", None)
    if not context:
        return ""
    return projects.get_context_project_name(context) or ""


def _get_catalog_roots(
    project_name: str = "",
    agent: Agent | None = None,
) -> list[str]:
    roots: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if not path:
            return
        fixed = files.fix_dev_path(path)
        if not files.exists(fixed) or fixed in seen:
            return
        seen.add(fixed)
        roots.append(fixed)

    if agent is not None:
        for path in get_skill_roots(agent):
            add(path)
        return roots

    if project_name:
        add(projects.get_project_meta(project_name, "skills"))

    add(files.get_abs_path("usr", "skills"))
    for path in plugin_helpers.get_enabled_plugin_paths(None, "skills"):
        add(path)
    add(files.get_abs_path("skills"))

    return roots


def _merge_active_skill_entries(
    scope_entries: list[ActiveSkillEntry],
    dynamic_entries: list[ActiveSkillEntry],
    disabled_entries: list[ActiveSkillEntry],
    *,
    limit: int | None,
) -> list[ActiveSkillEntry]:
    merged: list[ActiveSkillEntry] = []
    seen: set[str] = set()
    disabled_keys = {
        key for entry in disabled_entries for key in _entry_keys(entry)
    }

    for entry in [*scope_entries, *dynamic_entries]:
        keys = _entry_keys(entry)
        key = _entry_key(entry)
        if not key or keys & seen or keys & disabled_keys:
            continue

        seen.update(keys)
        merged.append(entry)
        if limit is not None and limit >= 0 and len(merged) >= limit:
            break

    return merged


def _store_context_active_skill_entries(
    context: Any,
    key: str,
    entries: list[ActiveSkillEntry],
) -> None:
    normalized_entries = normalize_active_skills(entries)
    context.set_data(key, normalized_entries or None)


def _resolve_active_skill_entries(
    agent: Agent | None,
    entries: list[ActiveSkillEntry],
) -> list[dict[str, str]]:
    if not agent:
        return []

    visible_roots = [files.fix_dev_path(root) for root in get_skill_roots(agent)]
    resolved: list[dict[str, str]] = []
    seen_paths: set[str] = set()

    for entry in entries:
        skill = _resolve_active_skill_entry(entry, visible_roots)
        if not skill:
            continue

        runtime_path = files.normalize_a0_path(str(skill.path))
        if runtime_path in seen_paths:
            continue

        seen_paths.add(runtime_path)
        resolved.append(
            {
                "name": skill.name or skill.path.name,
                "path": runtime_path,
                "content": _format_skill_prompt(skill),
            }
        )

    return resolved


def _resolve_active_skill_entry(
    entry: ActiveSkillEntry,
    visible_roots: list[str],
) -> Skill | None:
    skill_path = str(entry.get("path") or "").strip()
    if skill_path:
        skill = _load_skill_from_runtime_path(skill_path, visible_roots)
        if skill:
            return skill

    skill_name = str(entry.get("name") or "").strip()
    if not skill_name:
        return None

    target = skill_name.lower().strip()
    for root in visible_roots:
        for skill_md in discover_skill_md_files(Path(root)):
            skill = skill_from_markdown(skill_md, include_content=True)
            if not skill:
                continue
            candidates = {
                (skill.name or "").strip().lower(),
                skill.path.name.strip().lower(),
            }
            if target in candidates:
                return skill

    return None


def _load_skill_from_runtime_path(
    skill_path: str,
    visible_roots: list[str],
) -> Skill | None:
    abs_path = files.fix_dev_path(skill_path)
    if not any(files.is_in_dir(abs_path, root) for root in visible_roots):
        return None

    skill_md = Path(abs_path) / "SKILL.md"
    if not skill_md.is_file():
        return None

    return skill_from_markdown(skill_md, include_content=True)
