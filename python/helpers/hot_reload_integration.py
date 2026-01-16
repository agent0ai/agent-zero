"""
Hot-Reload Integration Module

Integrates hot-reload with Agent Zero's extension and tool system.
Handles reloading of tools, extensions, and cache invalidation.
"""

import os
from typing import Optional
from python.helpers.hot_reload import (
    HotReloadManager,
    FileChangeEvent,
    get_hot_reload_manager,
    initialize_hot_reload,
    start_hot_reload,
)
from python.helpers.module_cache import (
    get_module_cache,
    reload_module_safe,
)
from python.helpers.print_style import PrintStyle  # type: ignore[import]
# Note: extract_tools doesn't expose _cache, so we manage our own cache invalidation


class HotReloadIntegration:
    """Integrates hot-reload with Agent Zero systems"""

    def __init__(self):
        self.module_cache = get_module_cache()
        self.reload_manager: Optional[HotReloadManager] = None
        self._stats = {
            "reloads": 0,
            "successes": 0,
            "failures": 0,
        }

    def initialize(self, enabled: bool = True) -> None:
        """Initialize hot-reload integration"""
        if not enabled:
            PrintStyle.info("Hot-reload integration disabled")
            return

        # Initialize hot-reload manager
        self.reload_manager = initialize_hot_reload(enabled=True)

        # Register callback for file changes
        self.reload_manager.add_reload_callback(self._handle_file_change)

        PrintStyle.success("Hot-reload integration initialized")

    def start(self) -> None:
        """Start hot-reload system"""
        if self.reload_manager:
            start_hot_reload()
            PrintStyle.success("Hot-reload system started")

    def _handle_file_change(self, event: FileChangeEvent) -> None:
        """Handle file change event"""
        self._stats["reloads"] += 1

        file_path = event.path
        event_type = event.event_type

        PrintStyle(font_color="#00FFFF", bold=True).print(
            f"Hot-Reload: Detected {event_type} - {os.path.basename(file_path)}"
        )

        # Determine file type and handle accordingly
        if self._is_tool_file(file_path):
            self._reload_tool(file_path, event_type)
        elif self._is_extension_file(file_path):
            self._reload_extension(file_path, event_type)
        elif self._is_prompt_file(file_path):
            self._reload_prompt(file_path, event_type)
        else:
            self._reload_generic(file_path, event_type)

    def _is_tool_file(self, file_path: str) -> bool:
        """Check if file is a tool"""
        return "python/tools" in file_path.replace("\\", "/")

    def _is_extension_file(self, file_path: str) -> bool:
        """Check if file is an extension"""
        return "python/extensions" in file_path.replace("\\", "/")

    def _is_prompt_file(self, file_path: str) -> bool:
        """Check if file is a prompt"""
        return file_path.endswith((".md", ".txt"))

    def _reload_tool(self, file_path: str, event_type: str) -> None:
        """Reload a tool file"""
        try:
            if event_type == "deleted":
                self.module_cache.invalidate_module(file_path)
                self._invalidate_tools_cache()
                PrintStyle.warning(f"Tool deleted, cache invalidated")
                self._stats["successes"] += 1
                return

            # Reload the module
            module = reload_module_safe(file_path)

            if module is not None:
                # Invalidate tools cache to force re-discovery
                self._invalidate_tools_cache()

                PrintStyle.success(f"Tool reloaded: {os.path.basename(file_path)}")
                self._stats["successes"] += 1
            else:
                PrintStyle.error(f"Tool reload failed: {os.path.basename(file_path)}")
                self._stats["failures"] += 1

        except Exception as e:
            PrintStyle.error(f"Error reloading tool: {e}")
            self._stats["failures"] += 1

    def _reload_extension(self, file_path: str, event_type: str) -> None:
        """Reload an extension file"""
        try:
            if event_type == "deleted":
                self.module_cache.invalidate_module(file_path)
                self._invalidate_extension_cache()
                PrintStyle.warning(f"Extension deleted, cache invalidated")
                self._stats["successes"] += 1
                return

            # Reload the module
            module = reload_module_safe(file_path)

            if module is not None:
                # Invalidate extension cache
                self._invalidate_extension_cache()

                PrintStyle.success(f"Extension reloaded: {os.path.basename(file_path)}")
                self._stats["successes"] += 1
            else:
                PrintStyle.error(f"Extension reload failed: {os.path.basename(file_path)}")
                self._stats["failures"] += 1

        except Exception as e:
            PrintStyle.error(f"Error reloading extension: {e}")
            self._stats["failures"] += 1

    def _reload_prompt(self, file_path: str, event_type: str) -> None:
        """Handle prompt file changes"""
        # Prompts are read directly from disk, no caching needed
        PrintStyle.info(f"Prompt {event_type}: {os.path.basename(file_path)}")
        self._stats["successes"] += 1

    def _reload_generic(self, file_path: str, event_type: str) -> None:
        """Reload a generic Python module"""
        if not file_path.endswith(".py"):
            return

        try:
            if event_type == "deleted":
                self.module_cache.invalidate_module(file_path)
                PrintStyle.warning(f"Module deleted, cache invalidated")
                self._stats["successes"] += 1
                return

            module = reload_module_safe(file_path)

            if module is not None:
                PrintStyle.success(f"Module reloaded: {os.path.basename(file_path)}")
                self._stats["successes"] += 1
            else:
                PrintStyle.error(f"Module reload failed: {os.path.basename(file_path)}")
                self._stats["failures"] += 1

        except Exception as e:
            PrintStyle.error(f"Error reloading module: {e}")
            self._stats["failures"] += 1

    def _invalidate_tools_cache(self) -> None:
        """Invalidate tools cache to force re-discovery"""
        # Note: extract_tools doesn't expose a cache API
        # Tools will be re-discovered on next agent initialization
        PrintStyle.info("Tool reload triggered - will be re-discovered on next use")

    def _invalidate_extension_cache(self) -> None:
        """Invalidate extensions cache"""
        # Note: extension module doesn't expose a cache API
        # Extensions will be re-discovered on next agent initialization
        PrintStyle.info("Extension reload triggered - will be re-discovered on next use")

    def get_stats(self) -> dict:
        """Get reload statistics"""
        cache_stats = self.module_cache.get_stats()
        return {
            **self._stats,
            "cache_stats": cache_stats,
            "is_running": self.reload_manager.is_running() if self.reload_manager else False,
        }

    def is_running(self) -> bool:
        """Check if hot-reload is running"""
        return self.reload_manager.is_running() if self.reload_manager else False


# Global integration instance
_global_integration: Optional[HotReloadIntegration] = None


def get_hot_reload_integration() -> HotReloadIntegration:
    """Get global hot-reload integration instance"""
    global _global_integration
    if _global_integration is None:
        _global_integration = HotReloadIntegration()
    return _global_integration


def initialize_integration(enabled: bool = True) -> None:
    """Initialize hot-reload integration"""
    integration = get_hot_reload_integration()
    integration.initialize(enabled=enabled)


def start_integration() -> None:
    """Start hot-reload integration"""
    integration = get_hot_reload_integration()
    integration.start()
