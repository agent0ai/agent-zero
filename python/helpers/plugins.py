from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from python.helpers import files


# ============================================================================
# Core Data Structures
# ============================================================================

@dataclass(slots=True)
class Plugin:
    id: str
    name: str
    path: Path
    manifest_path: Path
    provides: Dict[str, Any] = field(default_factory=dict)  # capability map
    version: str = ""
    author: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Optional heavy fields
    raw_manifest: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Discovery & Loading
# ============================================================================

def get_plugin_roots() -> List[str]:
    """
    Get plugin root directories.
    Priority: project plugins > usr plugins > core plugins
    """
    # Project-specific plugins
    projects = files.find_existing_paths_by_pattern("usr/projects/*/.a0proj/plugins")
    
    return [
        *projects,
        files.get_abs_path("usr/plugins"),
        files.get_abs_path("plugins"),
    ]


def discover_plugin_manifests(root: str) -> List[Path]:
    """Recursively discover plugin.json files under a root directory."""
    root_path = Path(root)
    if not root_path.exists():
        return []
    
    results: List[Path] = []
    for p in root_path.rglob("plugin.json"):
        if p.is_file() and ".git" not in str(p):
            results.append(p)
    
    return sorted(results, key=lambda x: str(x))


def plugin_from_manifest(manifest_path: Path) -> Optional[Plugin]:
    """Load plugin from manifest file."""
    try:
        text = manifest_path.read_text(encoding="utf-8", errors="replace")
        manifest = json.loads(text)
    except Exception:
        return None
    
    if not isinstance(manifest, dict):
        return None
    
    plugin_dir = manifest_path.parent
    plugin_id = manifest.get("id", "").strip()
    
    if not plugin_id:
        return None
    
    plugin = Plugin(
        id=plugin_id,
        name=manifest.get("name", plugin_id),
        path=plugin_dir,
        manifest_path=manifest_path,
        provides=manifest.get("provides", {}),
        version=manifest.get("version", ""),
        author=manifest.get("author", ""),
        description=manifest.get("description", ""),
        tags=manifest.get("tags", []),
        raw_manifest=manifest,
    )
    
    return plugin


# ============================================================================
# Registry Access (List/Find)
# ============================================================================

def list_plugins() -> List[Plugin]:
    """List all discovered plugins."""
    plugins: List[Plugin] = []
    
    for root in get_plugin_roots():
        for manifest_path in discover_plugin_manifests(root):
            p = plugin_from_manifest(manifest_path)
            if p:
                plugins.append(p)
    
    # Dedupe by ID (earlier roots win)
    by_id: Dict[str, Plugin] = {}
    for p in plugins:
        if p.id not in by_id:
            by_id[p.id] = p
    
    return list(by_id.values())


def find_plugin(plugin_id: str) -> Optional[Plugin]:
    """Find a specific plugin by ID."""
    if not plugin_id:
        return None
    
    # Search roots in priority order (first one found wins)
    for root in get_plugin_roots():
        for manifest_path in discover_plugin_manifests(root):
            p = plugin_from_manifest(manifest_path)
            if p and p.id == plugin_id:
                return p
    
    return None


# ============================================================================
# Path Resolution & Import
# ============================================================================

def _extract_module_dir(module_path: str) -> str:
    """Extract directory from module path (e.g., 'tools/my_tool.py' -> 'tools')."""
    return str(Path(module_path).parent)


def get_plugin_paths(cap_type: str, *subpaths: str) -> List[str]:
    """
    Get all paths from loaded plugins for a given capability type.
    Supports both 'module' (parent dir used) and 'dir' (direct path used) in config.
    
    Args:
        cap_type: Capability type (e.g., "tool", "extension", "api", "agent")
        subpaths: Additional path components to append
    
    Returns:
        List of absolute paths matching the capability type
    """
    paths: List[str] = []
    
    for plugin in list_plugins():
        cap_config = plugin.provides.get(cap_type)
        if not cap_config:
            continue
        
        # Normalize to list for uniform processing
        items = []
        if isinstance(cap_config, list):
            items = [c for c in cap_config if isinstance(c, dict)]
        elif isinstance(cap_config, dict):
            items = [cap_config]
        
        # Build paths from items
        for item in items:
            path_to_add = ""
            
            # Priority 1: Explicit directory
            if item.get("dir"):
                path_to_add = item["dir"]
            # Priority 2: Module parent directory
            elif item.get("module"):
                path_to_add = _extract_module_dir(item["module"])
            
            if path_to_add:
                full_path = files.get_abs_path(str(plugin.path), path_to_add, *subpaths)
                if files.exists(full_path) and full_path not in paths:
                    paths.append(full_path)
    
    return paths


def import_plugin_module(plugin_id: str, module_path: str) -> Any:
    """
    Import a Python module from a plugin using importlib.
    
    Args:
        plugin_id: Plugin ID
        module_path: Relative path to module within plugin (e.g., "helpers/memory.py")
    
    Returns:
        The imported module object
    
    Raises:
        ImportError: If plugin or module not found
    """
    import importlib.util
    import sys
    
    plugin = find_plugin(plugin_id)
    if not plugin:
        raise ImportError(f"Plugin '{plugin_id}' not found")
    
    full_path = plugin.path / module_path
    if not full_path.exists():
        raise ImportError(f"Module '{module_path}' not found in plugin '{plugin_id}'")
    
    # Create a unique module name to avoid conflicts
    module_name = f"plugins.{plugin_id}.{module_path.replace('/', '.').replace('.py', '')}"
    
    # Check if already loaded
    if module_name in sys.modules:
        return sys.modules[module_name]
    
    # Load the module
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec from {full_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    return module


# ============================================================================
# API Helpers
# ============================================================================

def build_plugin_response_data(plugin: Plugin) -> dict:
    """
    Build normalized API response data for a plugin.
    Resolves URLs for UI capabilities.
    
    Args:
        plugin: Plugin object to serialize
    
    Returns:
        Dictionary with plugin data, component_url, module_url, and provides
    """
    base_url = f"/plugins/{plugin.id}/"
    
    response_data = {
        "id": plugin.id,
        "name": plugin.name,
        "base_url": base_url,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "tags": plugin.tags,
        "provides": plugin.provides,
    }
    
    # Resolve UI capability URLs from provides.ui
    if "ui" in plugin.provides:
        ui_config = plugin.provides["ui"]
        if isinstance(ui_config, dict):
            if ui_config.get("component"):
                response_data["component_url"] = f"{base_url}{ui_config['component']}"
            if ui_config.get("module"):
                response_data["module_url"] = f"{base_url}{ui_config['module']}"
            if ui_config.get("props"):
                response_data["props"] = ui_config["props"]
    
    return response_data
