from __future__ import annotations

import shutil
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Tuple

from python.helpers import files
from python.helpers.skills import discover_skill_md_files

ConflictPolicy = Literal["skip", "overwrite", "rename"]

# Project skills folder name (inside .a0proj)
PROJECT_SKILLS_DIR = "skills"


@dataclass(slots=True)
class ImportPlanItem:
    src_root: Path
    src_skill_dir: Path
    dest_skill_dir: Path


@dataclass(slots=True)
class ImportResult:
    imported: List[Path]
    skipped: List[Path]
    source_root: Path
    destination_root: Path
    namespace: str


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def _derive_namespace(source: Path) -> str:
    # Use stem for zip, name for directory
    return (source.stem or source.name or "import").strip()


def _candidate_skill_roots(source_dir: Path) -> List[Path]:
    """
    Heuristics to find likely skill roots inside a repo/pack:
    - <source>/skills
    - <source>/plugins/*/skills (Claude Code style)
    - fallback: <source>
    """
    candidates: List[Path] = []

    direct = source_dir / "skills"
    if direct.is_dir() and discover_skill_md_files(direct):
        candidates.append(direct)

    plugins = source_dir / "plugins"
    if plugins.is_dir():
        for child in plugins.iterdir():
            if not child.is_dir():
                continue
            skills_dir = child / "skills"
            if skills_dir.is_dir() and discover_skill_md_files(skills_dir):
                candidates.append(skills_dir)

    # Deduplicate while preserving order
    unique: List[Path] = []
    seen = set()
    for c in candidates:
        key = str(c.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique or [source_dir]


def _unzip_to_temp_dir(zip_path: Path) -> Path:
    """
    Extract a zip into a temp folder under tmp/skill_imports (inside Apollos AI base dir).
    Returns the extraction root folder.
    """
    base_tmp = Path(files.get_abs_path("tmp", "skill_imports"))
    base_tmp.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    target = base_tmp / f"import_{zip_path.stem}_{stamp}"
    target.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(target)

    # If zip contains a single top-level folder, treat that as the root
    children = [p for p in target.iterdir()]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return target


def build_import_plan(
    source: Path,
    dest_root: Path,
    *,
    namespace: Optional[str] = None,
) -> Tuple[List[ImportPlanItem], Path]:
    """
    Build a copy plan for importing skills from a source folder.

    Returns: (plan_items, source_root_dir_used_for_scan)
    """
    source_dir = source
    roots = _candidate_skill_roots(source_dir)
    plan: List[ImportPlanItem] = []
    ns = (namespace or _derive_namespace(source)).strip()
    dest_ns_root = dest_root / ns

    for root in roots:
        for skill_md in discover_skill_md_files(root):
            skill_dir = skill_md.parent
            # Skip if the skill dir is already inside destination (prevents recursive import)
            if _is_within(skill_dir, dest_root):
                continue
            try:
                rel = skill_dir.resolve().relative_to(root.resolve())
            except Exception:
                # If relative fails due to symlink oddities, just use leaf folder name
                rel = Path(skill_dir.name)
            dest_dir = dest_ns_root / rel
            plan.append(
                ImportPlanItem(
                    src_root=root, src_skill_dir=skill_dir, dest_skill_dir=dest_dir
                )
            )

    # Deduplicate by destination path (keep first occurrence)
    seen_dest = set()
    deduped: List[ImportPlanItem] = []
    for item in plan:
        key = str(item.dest_skill_dir.resolve())
        if key in seen_dest:
            continue
        seen_dest.add(key)
        deduped.append(item)

    return deduped, roots[0]


def _resolve_conflict(dest: Path, policy: ConflictPolicy) -> Tuple[Path, bool]:
    """
    Returns (final_dest_path, should_copy).
    """
    if not dest.exists():
        return dest, True

    if policy == "skip":
        return dest, False

    if policy == "overwrite":
        shutil.rmtree(dest)
        return dest, True

    # rename
    i = 2
    while True:
        candidate = dest.with_name(f"{dest.name}_{i}")
        if not candidate.exists():
            return candidate, True
        i += 1


def get_project_skills_folder(project_name: str) -> Path:
    """Get the skills folder path for a project."""
    from python.helpers.projects import get_project_meta_folder

    return Path(get_project_meta_folder(project_name, PROJECT_SKILLS_DIR))


def get_agent_profile_skills_folder(profile_name: str) -> Path:
    return Path(files.get_abs_path("usr", "agents", profile_name, "skills"))


def get_project_agent_profile_skills_folder(
    project_name: str, profile_name: str
) -> Path:
    from python.helpers.projects import get_project_meta_folder

    return Path(get_project_meta_folder(project_name, "agents", profile_name, "skills"))


def resolve_skills_destination_root(
    project_name: Optional[str],
    agent_profile: Optional[str],
) -> Path:
    if project_name and agent_profile:
        return get_project_agent_profile_skills_folder(project_name, agent_profile)
    if project_name:
        return get_project_skills_folder(project_name)
    if agent_profile:
        return get_agent_profile_skills_folder(agent_profile)
    return Path(files.get_abs_path("usr", "skills"))


def import_skills(
    source_path: str,
    *,
    namespace: Optional[str] = None,
    conflict: ConflictPolicy = "skip",
    dry_run: bool = False,
    project_name: Optional[str] = None,
    agent_profile: Optional[str] = None,
) -> ImportResult:
    """
    Import external Skills into usr/skills/<namespace>/...

    - source_path can be a directory or a .zip file
    - Uses heuristics to detect the Skills root(s)
    - Copies each skill folder (parent of SKILL.md) as-is
    """
    src = Path(source_path).expanduser()
    if not src.is_absolute():
        src = (Path.cwd() / src).resolve()

    if not src.exists():
        raise FileNotFoundError(f"Source not found: {src}")

    dest_root = resolve_skills_destination_root(project_name, agent_profile)
    dest_root.mkdir(parents=True, exist_ok=True)

    extracted_root: Optional[Path] = None
    source_dir: Path
    if src.is_file() and src.suffix.lower() == ".zip":
        extracted_root = _unzip_to_temp_dir(src)
        source_dir = extracted_root
    elif src.is_dir():
        source_dir = src
    else:
        raise ValueError("Source must be a directory or a .zip file")

    ns = (namespace or _derive_namespace(src)).strip()
    if not ns:
        ns = "import"

    plan, root_used = build_import_plan(source_dir, dest_root, namespace=ns)
    imported: List[Path] = []
    skipped: List[Path] = []

    for item in plan:
        final_dest, should_copy = _resolve_conflict(item.dest_skill_dir, conflict)
        if not should_copy:
            skipped.append(item.dest_skill_dir)
            continue
        if dry_run:
            imported.append(final_dest)
            continue
        final_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(item.src_skill_dir, final_dest)
        imported.append(final_dest)

    return ImportResult(
        imported=imported,
        skipped=skipped,
        source_root=root_used,
        destination_root=dest_root,
        namespace=ns,
    )
