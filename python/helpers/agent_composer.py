"""Agent profile composition and inheritance resolution.

Loads manifest.yaml files from agent profile directories, resolves
inheritance chains, merges capabilities/tools/memory/behavior, and
validates the resulting configuration.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from typing import Any

import yaml

from python.helpers import files

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class AgentProfileConfig:
    """Resolved configuration produced by composing one or more profiles."""

    name: str = ""
    capabilities: set[str] = field(default_factory=set)
    tools: dict[str, list[str]] = field(default_factory=lambda: {"include": [], "exclude": []})
    prompts: list[str] = field(default_factory=list)
    memory_areas: list[str] = field(default_factory=list)
    behavior: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Composer
# ---------------------------------------------------------------------------


class AgentComposer:
    """Loads, inherits, and merges agent profile manifests."""

    _manifest_cache: dict[str, dict[str, Any]] = {}

    # -- public API ---------------------------------------------------------

    def load_manifest(self, profile: str) -> dict[str, Any]:
        """Load and return the raw manifest dict for *profile*.

        Returns an empty dict when the manifest file does not exist so that
        callers never have to handle ``None``.
        """
        if profile in self._manifest_cache:
            return self._manifest_cache[profile]

        manifest_path = files.get_abs_path("agents", profile, "manifest.yaml")
        if not os.path.isfile(manifest_path):
            self._manifest_cache[profile] = {}
            return {}

        with open(manifest_path, encoding="utf-8") as fh:
            data: dict[str, Any] = yaml.safe_load(fh) or {}

        self._manifest_cache[profile] = data
        return data

    def resolve_inheritance(self, profile: str) -> list[str]:
        """Return the inheritance chain for *profile* (root-first).

        Example: ``["default", "developer"]`` means *default* is the base
        and *developer* overrides it.
        """
        chain: list[str] = []
        visited: set[str] = set()
        current = profile

        while current and current not in visited:
            visited.add(current)
            chain.append(current)
            manifest = self.load_manifest(current)
            current = manifest.get("inherits", "")

        chain.reverse()  # root-first
        return chain

    def compose(self, profiles: list[str]) -> AgentProfileConfig:
        """Compose multiple profiles into a single :class:`AgentProfileConfig`.

        Each profile's inheritance chain is resolved first, then all layers
        are merged left-to-right (later profiles win on conflicts).
        """
        layers: list[dict[str, Any]] = []
        for profile in profiles:
            for ancestor in self.resolve_inheritance(profile):
                manifest = self.load_manifest(ancestor)
                if manifest and manifest not in layers:
                    layers.append(manifest)

        return self._merge_layers(layers)

    def validate_config(self, config: AgentProfileConfig) -> list[str]:
        """Return a list of human-readable warnings (empty == valid)."""
        warnings: list[str] = []

        if not config.capabilities:
            warnings.append("No capabilities declared.")

        includes = config.tools.get("include", [])
        excludes = config.tools.get("exclude", [])
        for exc in excludes:
            for inc in includes:
                if fnmatch.fnmatch(exc, inc):
                    warnings.append(f"Tool '{exc}' is both included (via '{inc}') and excluded.")
                    break

        if not config.memory_areas:
            warnings.append("No memory areas configured.")

        max_iter = config.behavior.get("max_iterations", 0)
        if max_iter <= 0:
            warnings.append("max_iterations is not set or is non-positive.")

        return warnings

    def tool_allowed(self, config: AgentProfileConfig, tool_name: str) -> bool:
        """Check whether *tool_name* is permitted by the tool include/exclude rules."""
        excludes = config.tools.get("exclude", [])
        for pattern in excludes:
            if fnmatch.fnmatch(tool_name, pattern):
                return False

        includes = config.tools.get("include", [])
        if not includes:
            return True  # no include list means everything is allowed

        return any(fnmatch.fnmatch(tool_name, pattern) for pattern in includes)

    # -- internal helpers ---------------------------------------------------

    def _merge_layers(self, layers: list[dict[str, Any]]) -> AgentProfileConfig:
        """Merge a list of raw manifest dicts into a single config."""
        cfg = AgentProfileConfig()

        for layer in layers:
            cfg.name = layer.get("name", cfg.name)
            cfg.raw = {**cfg.raw, **layer}

            # capabilities: union
            caps = layer.get("capabilities", [])
            cfg.capabilities.update(caps)

            # tools: merge include/exclude lists
            tools = layer.get("tools", {})
            if "include" in tools:
                cfg.tools["include"] = list(tools["include"])
            if "exclude" in tools:
                cfg.tools["exclude"] = list(set(cfg.tools["exclude"]) | set(tools["exclude"]))

            # prompts: profile directory
            profile_name = layer.get("name", "")
            if profile_name:
                prompt_dir = files.get_abs_path("agents", profile_name, "prompts")
                if os.path.isdir(prompt_dir) and prompt_dir not in cfg.prompts:
                    cfg.prompts.append(prompt_dir)

            # memory
            mem = layer.get("memory", {})
            if "areas" in mem:
                cfg.memory_areas = list(dict.fromkeys(cfg.memory_areas + mem["areas"]))

            # behavior: deep-merge one level
            beh = layer.get("behavior", {})
            for k, v in beh.items():
                if isinstance(v, dict) and isinstance(cfg.behavior.get(k), dict):
                    cfg.behavior[k] = {**cfg.behavior[k], **v}
                else:
                    cfg.behavior[k] = v

        return cfg

    def clear_cache(self) -> None:
        """Drop all cached manifests (useful after profile edits)."""
        self._manifest_cache.clear()


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_default_composer: AgentComposer | None = None


def get_composer() -> AgentComposer:
    """Return (and lazily create) the singleton :class:`AgentComposer`."""
    global _default_composer
    if _default_composer is None:
        _default_composer = AgentComposer()
    return _default_composer
