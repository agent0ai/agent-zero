from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from python.helpers import file_tree, files, runtime, subagents

if TYPE_CHECKING:
    from agent import Agent

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


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
    agent: Agent | None = None,
) -> List[str]:

    if agent:
        # skill roots available to agent
        paths = subagents.get_paths(agent, "skills")
    else:
        # skill roots available globally
        project_agents = files.find_existing_paths_by_pattern(
            "usr/projects/*/.a0proj/agents/*/skills"
        )  # agents in projects
        projects = files.find_existing_paths_by_pattern(
            "usr/projects/*/.a0proj/skills"
        )  # projects
        usr_agents = files.find_existing_paths_by_pattern(
            "usr/agents/*/skills"
        )  # agents
        agents = files.find_existing_paths_by_pattern("agents/*/skills")  # agents
        paths = [
            files.get_abs_path("skills"),
            files.get_abs_path("usr/skills"),
            *project_agents,
            *projects,
            *usr_agents,
            *agents,
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
        except Exception:
            parsed = None
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
    agent: Agent | None = None,
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
    agent: Agent | None = None,
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
            if (
                _normalize_name(s.name) == target
                or _normalize_name(s.path.name) == target
            ):
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
        (
            "Allowed tools",
            ", ".join(skill.allowed_tools) if skill.allowed_tools else None,
        ),
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
        lines.append("Files (use skills_tool method=read_file to open):")
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
    agent: Agent | None = None,
) -> List[Skill]:
    q = (query or "").strip().lower()
    if not q:
        return []

    terms = [t for t in re.split(r"\s+", q) if t]
    candidates = list_skills(agent)

    scored: List[Tuple[int, Skill]] = []
    for s in candidates:
        name = s.name.lower()
        desc = (s.description or "").lower()
        tags = [t.lower() for t in s.tags]

        score = 0
        for term in terms:
            if term in name:
                score += 3
            if term in desc:
                score += 2
            if any(term in tag for tag in tags):
                score += 1

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

    skill = skill_from_markdown(skill_md_path, include_content=False, validate=False)
    if not skill:
        return ["Unable to parse SKILL.md frontmatter"]
    return validate_skill(skill)
