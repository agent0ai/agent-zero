from __future__ import annotations

import threading

from helpers.extension import Extension
from helpers import plugins
from helpers.print_style import PrintStyle
from plugins._sandboxing.helpers.runtime import get_manager


_thread: threading.Thread | None = None


class PrepareSandboxRuntime(Extension):
    def execute(self, **kwargs) -> None:
        global _thread
        if _thread is not None and _thread.is_alive():
            return
        _thread = threading.Thread(
            target=_prepare,
            name="a0-sandbox-runtime-preparation",
            daemon=True,
        )
        _thread.start()


def _prepare() -> None:
    try:
        manager = get_manager()
        diagnostics = manager.doctor()
        errors = [line for line in diagnostics if line.startswith("ERROR:")]
        warnings = [line for line in diagnostics if line.startswith("WARNING:")]
        if errors:
            PrintStyle.warning("Sandbox runtime doctor reported errors:", errors)
        elif warnings:
            PrintStyle.warning("Sandbox runtime doctor reported warnings:", warnings)
        for info in manager.list():
            owner = info.ownership.get("plugin_id")
            if owner and plugins.get_toggle_state(owner) != "enabled" and info.desired_running:
                manager.stop(info.name)
        manager.restore_standalone()
        deleted = manager.cleanup_expired()
        deleted_images = manager.cleanup_images()
        if deleted:
            PrintStyle.info("Deleted expired temporary sandboxes:", deleted)
        if deleted_images:
            PrintStyle.info("Deleted old unused sandbox images:", deleted_images)
    except Exception as exc:
        PrintStyle.warning("Sandbox runtime preparation failed:", exc)
