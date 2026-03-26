from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from python.helpers import files

# Extracts target selector from <meta name="plugin-target" content="...">
_META_TARGET_RE = re.compile(
    r'<meta\s+name=["\']plugin-target["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


@dataclass(slots=True)
class Plugin:
    id: str
    name: str
    path: Path


def get_plugin_roots() -> List[str]:
    """Plugin root directories, ordered by priority (user first)."""
    # Project-specific plugins (commented out for now, will add project/agent plugins later)
    # projects = files.find_existing_paths_by_pattern("usr/projects/*/.a0proj/plugins")
    return [
        # *projects,
        files.get_abs_path("usr/plugins"),
        files.get_abs_path("plugins"),
    ]


def list_plugins() -> List[Plugin]:
    """Discover plugins by directory convention. First root wins on ID conflict."""
    by_id: Dict[str, Plugin] = {}
    for root in get_plugin_roots():
        root_path = Path(root)
        if not root_path.exists():
            continue
        for d in sorted(root_path.iterdir(), key=lambda p: p.name):
            if not d.is_dir() or d.name.startswith("."):
                continue
            if d.name not in by_id:
                by_id[d.name] = Plugin(id=d.name, name=d.name, path=d)
    return list(by_id.values())


def find_plugin(plugin_id: str) -> Optional[Plugin]:
    """Find a single plugin by ID."""
    if not plugin_id:
        return None
    for p in list_plugins():
        if p.id == plugin_id:
            return p
    return None


def get_plugin_paths(*subpaths: str) -> List[str]:
    """
    Resolve existing directories under each plugin matching subpaths.

    Example:
        get_plugin_paths("extensions", "backend", "monologue_end")
        -> ["/abs/plugins/memory/extensions/backend/monologue_end", ...]
    """
    sub = "/".join(subpaths) if subpaths else ""
    paths: List[str] = []
    for plugin in list_plugins():
        candidate = str(plugin.path / sub) if sub else str(plugin.path)
        if Path(candidate).is_dir() and candidate not in paths:
            paths.append(candidate)
    return paths


def get_frontend_components() -> List[Dict[str, Any]]:
    """
    Return all injectable plugin frontend components.
    Convention: plugins/*/extensions/frontend/**/*.html
    The backend reads each file to extract the optional
    <meta name="plugin-target" content=".css-selector"> tag so the
    frontend never needs to fetch component HTML just to discover targets.
    """
    entries: List[Dict[str, Any]] = []
    for plugin in list_plugins():
        frontend_dir = plugin.path / "extensions" / "frontend"
        if not frontend_dir.is_dir():
            continue
        for html_file in sorted(frontend_dir.rglob("*.html"), key=lambda p: p.name):
            rel_path = html_file.relative_to(plugin.path).as_posix()
            entry: Dict[str, Any] = {
                "plugin_id": plugin.id,
                "component_url": f"/plugins/{plugin.id}/{rel_path}",
            }
            # Extract injection target from meta tag (if present)
            try:
                content = html_file.read_text(encoding="utf-8")
                m = _META_TARGET_RE.search(content)
                if m:
                    entry["target"] = m.group(1)
            except Exception:
                pass
            entries.append(entry)
    return entries
