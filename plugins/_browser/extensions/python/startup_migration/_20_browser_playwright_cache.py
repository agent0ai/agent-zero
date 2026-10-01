from __future__ import annotations

import threading
from typing import Any

from helpers import virtual_desktop_routes
from helpers.extension import Extension
from helpers.print_style import PrintStyle
from plugins._browser import hooks


_startup_migration_thread: threading.Thread | None = None


class BrowserPlaywrightCacheMigration(Extension):
    def execute(self, **kwargs):
        virtual_desktop_routes.install_route_hooks()
        _start_background_cache_migration()


def _start_background_cache_migration() -> threading.Thread:
    global _startup_migration_thread

    if _startup_migration_thread and _startup_migration_thread.is_alive():
        return _startup_migration_thread

    _startup_migration_thread = threading.Thread(
        target=_migrate_cache_safely,
        name="a0-browser-playwright-cache-migration",
        daemon=True,
    )
    _startup_migration_thread.start()
    return _startup_migration_thread


def _migrate_cache_safely() -> None:
    try:
        _log_cache_migration_result(hooks.prepare_playwright_cache())
    except Exception as exc:
        PrintStyle.warning("Browser Playwright cache migration failed:", exc)


def _log_cache_migration_result(result: dict[str, Any]) -> None:
    if result.get("errors"):
        PrintStyle.warning("Browser Playwright cache migration reported errors:", result["errors"])
    elif result.get("migrated") or result.get("removed"):
        PrintStyle.info("Browser Playwright cache prepared:", result)
