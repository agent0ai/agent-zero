from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

from python.helpers import files

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


SkillSource = Literal["custom", "builtin", "shared"]


@dataclass(slots=True)
class Skill:
    name: str
    description: str
    path: Path
    skill_md_path: Path
    source: SkillSource

    version: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    license: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional heavy fields (only set when requested)
    content: str = ""  # body content (markdown without frontmatter)
    raw_frontmatter: Dict[str, Any] = field(default_factory=dict)


def get_skills_base_dir() -> Path:
    return Path(files.get_abs_path("skills"))


def get_skill_roots(order: Optional[List[SkillSource]] = None) -> List[Tuple[SkillSource, Path]]:
    base = get_skills_base_dir()
    order = order or ["custom", "builtin", "shared"]
    return [(src, base / src) for src in order]


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
        # Support comma-separated strings
        parts = [p.strip() for p in value.split(",")]
        return [p for p in parts if p]
    return [str(value).strip()] if str(value).strip() else []


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", "-", (name or "").strip().lower())


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_frontmatter(markdown: str) -> Tuple[Dict[str, Any], str]:
    """
    Splits a SKILL.md into (frontmatter_dict, body_text).

    If no YAML frontmatter is present, returns ({}, full_text).
    """
    text = markdown or ""
    if not text.lstrip().startswith("---"):
        return {}, text.strip()

    # We require frontmatter fence at the start (allow leading whitespace/newlines).
    lines = text.splitlines()
    # find first '---' line
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            start_idx = i
            break
        if line.strip():  # non-empty before fence => not frontmatter
            return {}, text.strip()

    if start_idx is None:
        return {}, text.strip()

    end_idx = None
    for j in range(start_idx + 1, len(lines)):
        if lines[j].strip() == "---":
            end_idx = j
            break

    if end_idx is None:
        return {}, text.strip()

    fm_text = "\n".join(lines[start_idx + 1 : end_idx]).strip()
    body = "\n".join(lines[end_idx + 1 :]).strip()
    fm = parse_frontmatter(fm_text)
    return fm, body


def parse_frontmatter(frontmatter_text: str) -> Dict[str, Any]:
    """
    Parse YAML frontmatter. Uses PyYAML if available, otherwise a minimal fallback parser.
    """
    if not frontmatter_text.strip():
        return {}

    if yaml is not None:
        try:
            parsed = yaml.safe_load(frontmatter_text)  # type: ignore[attr-defined]
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    # Fallback: very small YAML subset (key: value, lists with '- item')
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
                # strip surrounding quotes
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


def skill_from_markdown(
    skill_md_path: Path,
    source: SkillSource,
    *,
    include_content: bool = False,
) -> Optional[Skill]:
    try:
        text = _read_text(skill_md_path)
    except Exception:
        return None

    fm, body = split_frontmatter(text)
    skill_dir = skill_md_path.parent

    name = str(fm.get("name") or fm.get("skill") or skill_dir.name).strip()
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
    allowed_tools = _coerce_list(fm.get("allowed_tools") or fm.get("tools"))

    version = str(fm.get("version") or "").strip()
    author = str(fm.get("author") or "").strip()
    license_ = str(fm.get("license") or "").strip()

    meta = fm.get("metadata")
    if not isinstance(meta, dict):
        meta = {}

    skill = Skill(
        name=name,
        description=description,
        path=skill_dir,
        skill_md_path=skill_md_path,
        source=source,
        version=version,
        author=author,
        tags=tags,
        triggers=triggers,
        allowed_tools=allowed_tools,
        license=license_,
        metadata=dict(meta),
        raw_frontmatter=fm if include_content else {},
        content=body if include_content else "",
    )
    return skill


def list_skills(
    *,
    include_content: bool = False,
    dedupe: bool = True,
    root_order: Optional[List[SkillSource]] = None,
) -> List[Skill]:
    skills: List[Skill] = []

    roots = get_skill_roots(order=root_order)
    for source, root in roots:
        for skill_md in discover_skill_md_files(root):
            s = skill_from_markdown(skill_md, source, include_content=include_content)
            if s:
                skills.append(s)

    if not dedupe:
        return skills

    # Dedupe by normalized name, preserving root_order priority (earlier wins)
    by_name: Dict[str, Skill] = {}
    for s in skills:
        key = _normalize_name(s.name) or _normalize_name(s.path.name)
        if key and key not in by_name:
            by_name[key] = s
    return list(by_name.values())


def find_skill(
    skill_name: str,
    *,
    include_content: bool = False,
    root_order: Optional[List[SkillSource]] = None,
) -> Optional[Skill]:
    target = _normalize_name(skill_name)
    if not target:
        return None

    roots = get_skill_roots(order=root_order)
    for source, root in roots:
        for skill_md in discover_skill_md_files(root):
            s = skill_from_markdown(skill_md, source, include_content=include_content)
            if not s:
                continue
            if _normalize_name(s.name) == target or _normalize_name(s.path.name) == target:
                return s
    return None


def search_skills(query: str, *, limit: int = 25) -> List[Skill]:
    q = (query or "").strip().lower()
    if not q:
        return []

    terms = [t for t in re.split(r"\s+", q) if t]
    candidates = list_skills(include_content=False, dedupe=True)

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


def safe_path_within_dir(base_dir: Path, rel_path: str) -> Path:
    """
    Resolve rel_path inside base_dir, preventing directory traversal.
    """
    base = base_dir.resolve()
    candidate = (base / rel_path).resolve()
    if os.path.commonpath([str(candidate), str(base)]) != str(base):
        raise ValueError("Path escapes skill directory")
    return candidate


