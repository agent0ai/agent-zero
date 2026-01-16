"""
Hot-Reload System: File Monitoring Module

Watches for changes in tools/, extensions/, and prompts/ directories
and triggers automatic reloading without Docker restart.

Dependencies: watchdog
"""

import asyncio
import os
from pathlib import Path
from typing import Callable, Set, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from watchdog.observers import Observer  # type: ignore[import]
from watchdog.events import FileSystemEventHandler, FileSystemEvent  # type: ignore[import]
from python.helpers.print_style import PrintStyle  # type: ignore[import]
from python.helpers.files import get_abs_path  # type: ignore[import]


@dataclass
class FileChangeEvent:
    """Represents a file change event"""
    path: str
    event_type: str  # 'created', 'modified', 'deleted'
    timestamp: datetime
    module_path: Optional[str] = None


@dataclass
class WatchConfig:
    """Configuration for directory watching"""
    path: str
    patterns: list[str] = field(default_factory=lambda: ["*.py"])
    recursive: bool = True
    enabled: bool = True


class HotReloadHandler(FileSystemEventHandler):
    """Handles file system events for hot-reload"""

    def __init__(self, callback: Callable[[FileChangeEvent], None], patterns: list[str]):
        super().__init__()
        self.callback = callback
        self.patterns = patterns
        self._debounce_cache: Dict[str, float] = {}
        self._debounce_delay = 0.5  # seconds

    def _should_process(self, path: str) -> bool:
        """Check if file matches patterns and debounce"""
        # Check file extension
        if not any(path.endswith(pattern.replace("*", "")) for pattern in self.patterns):
            return False

        # Debounce: ignore rapid repeated events for same file
        now = datetime.now().timestamp()
        last_time = self._debounce_cache.get(path, 0)

        if now - last_time < self._debounce_delay:
            return False

        self._debounce_cache[path] = now
        return True

    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._should_process(event.src_path):
            self._handle_event(event.src_path, "created")

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._should_process(event.src_path):
            self._handle_event(event.src_path, "modified")

    def on_deleted(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._should_process(event.src_path):
            self._handle_event(event.src_path, "deleted")

    def _handle_event(self, path: str, event_type: str):
        """Process file event and invoke callback"""
        change_event = FileChangeEvent(
            path=path,
            event_type=event_type,
            timestamp=datetime.now()
        )
        try:
            self.callback(change_event)
        except Exception as e:
            PrintStyle.error(f"Error handling file event: {e}")


class FileWatcher:
    """Manages file watching for multiple directories"""

    def __init__(self):
        self._observers: Dict[str, Observer] = {}
        self._watch_configs: Dict[str, WatchConfig] = {}
        self._callbacks: list[Callable[[FileChangeEvent], None]] = []
        self._running = False

    def add_watch(self, config: WatchConfig) -> None:
        """Add a directory to watch"""
        abs_path = get_abs_path(config.path)

        if not os.path.exists(abs_path):
            PrintStyle.warning(f"Watch path does not exist: {abs_path}")
            return

        self._watch_configs[abs_path] = config
        PrintStyle.info(f"Added watch for: {abs_path}")

    def add_callback(self, callback: Callable[[FileChangeEvent], None]) -> None:
        """Add a callback to be invoked on file changes"""
        self._callbacks.append(callback)

    def _notify_callbacks(self, event: FileChangeEvent) -> None:
        """Notify all callbacks about file change"""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                PrintStyle.error(f"Callback error: {e}")

    def start(self) -> None:
        """Start watching all configured directories"""
        if self._running:
            PrintStyle.warning("File watcher already running")
            return

        for abs_path, config in self._watch_configs.items():
            if not config.enabled:
                continue

            handler = HotReloadHandler(
                callback=self._notify_callbacks,
                patterns=config.patterns
            )

            observer = Observer()
            observer.schedule(handler, abs_path, recursive=config.recursive)
            observer.start()

            self._observers[abs_path] = observer
            PrintStyle.success(f"Watching: {abs_path}")

        self._running = True
        PrintStyle.success("Hot-reload file watcher started")

    def stop(self) -> None:
        """Stop all observers"""
        if not self._running:
            return

        for observer in self._observers.values():
            observer.stop()
            observer.join()

        self._observers.clear()
        self._running = False
        PrintStyle.info("Hot-reload file watcher stopped")

    def is_running(self) -> bool:
        """Check if watcher is running"""
        return self._running


class HotReloadManager:
    """Main hot-reload manager - singleton"""

    _instance: Optional["HotReloadManager"] = None

    def __init__(self):
        self.watcher = FileWatcher()
        self._reload_callbacks: list[Callable[[FileChangeEvent], None]] = []
        self._enabled = False

    @classmethod
    def get_instance(cls) -> "HotReloadManager":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self, enabled: bool = True) -> None:
        """Initialize hot-reload system"""
        self._enabled = enabled

        if not enabled:
            PrintStyle.info("Hot-reload disabled")
            return

        # Configure default watch directories
        self.watcher.add_watch(WatchConfig(
            path="python/tools",
            patterns=["*.py"],
            recursive=True
        ))

        self.watcher.add_watch(WatchConfig(
            path="python/extensions",
            patterns=["*.py"],
            recursive=True
        ))

        self.watcher.add_watch(WatchConfig(
            path="prompts",
            patterns=["*.md", "*.txt"],
            recursive=True
        ))

        # Add internal callback
        self.watcher.add_callback(self._on_file_change)

        PrintStyle.success("Hot-reload manager initialized")

    def start(self) -> None:
        """Start hot-reload system"""
        if not self._enabled:
            return

        self.watcher.start()

    def stop(self) -> None:
        """Stop hot-reload system"""
        self.watcher.stop()

    def add_reload_callback(self, callback: Callable[[FileChangeEvent], None]) -> None:
        """Add callback for reload events"""
        self._reload_callbacks.append(callback)

    def _on_file_change(self, event: FileChangeEvent) -> None:
        """Handle file change event"""
        PrintStyle(font_color="#FFA500", bold=True).print(
            f"Hot-Reload: {event.event_type.upper()} - {os.path.basename(event.path)}"
        )

        # Notify all reload callbacks
        for callback in self._reload_callbacks:
            try:
                callback(event)
            except Exception as e:
                PrintStyle.error(f"Reload callback error: {e}")

    def is_running(self) -> bool:
        """Check if hot-reload is running"""
        return self.watcher.is_running()


# Convenience functions
def initialize_hot_reload(enabled: bool = True) -> HotReloadManager:
    """Initialize and return hot-reload manager"""
    manager = HotReloadManager.get_instance()
    manager.initialize(enabled=enabled)
    return manager


def start_hot_reload() -> None:
    """Start hot-reload system"""
    manager = HotReloadManager.get_instance()
    manager.start()


def stop_hot_reload() -> None:
    """Stop hot-reload system"""
    manager = HotReloadManager.get_instance()
    manager.stop()


def get_hot_reload_manager() -> HotReloadManager:
    """Get hot-reload manager instance"""
    return HotReloadManager.get_instance()
