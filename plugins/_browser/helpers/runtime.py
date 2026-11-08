from __future__ import annotations

import atexit
import asyncio
import contextlib
import re
import threading
from pathlib import Path
from typing import Any

from helpers import files, kvp
from helpers.defer import DeferredTask
from helpers.print_style import PrintStyle
from plugins._browser.helpers.config import DEFAULT_BROWSER_TAB_SCOPE, TAB_SCOPE_KEY, get_browser_config
from plugins._browser.helpers.url import normalize_url
from plugins._browser.helpers.calls import run_browser_calls
from plugins._browser.helpers.sandbox import BrowserConnection

PLUGIN_DIR = Path(__file__).resolve().parents[1]
SHARED_RUNTIME_ID = 'shared'
BROWSER_TABS_KEY = 'browser_open_tabs'
BROWSER_TABS_VERSION = 1
_SAFE_CONTEXT_RE = re.compile(r'[^a-zA-Z0-9_.-]+')

def _safe_context_id(context_id: str) -> str:
    return _SAFE_CONTEXT_RE.sub("_", str(context_id or "default")).strip("._") or "default"


def _load_browser_tabs() -> tuple[bool, list[dict[str, Any]]]:
    try:
        payload = kvp.get_persistent(BROWSER_TABS_KEY, None)
    except Exception as exc:
        PrintStyle.warning(f"Browser tab recovery state could not be read: {exc}")
        return False, []
    if payload is None:
        return False, []
    if not isinstance(payload, dict) or not isinstance(payload.get("tabs"), list):
        PrintStyle.warning("Browser tab recovery state is invalid; starting without it.")
        return False, []

    tabs: list[dict[str, Any]] = []
    for entry in payload["tabs"]:
        if not isinstance(entry, dict):
            continue
        context_id = str(entry.get("context_id") or "").strip()
        url = str(entry.get("url") or "").strip()
        if not context_id or not url:
            continue
        tabs.append(
            {
                "context_id": context_id,
                "url": url,
                "active": bool(entry.get("active")),
            }
        )
    return True, tabs


def _save_browser_tabs(tabs: list[dict[str, Any]]) -> None:
    kvp.set_persistent(
        BROWSER_TABS_KEY,
        {"version": BROWSER_TABS_VERSION, "tabs": tabs},
    )


def _forget_browser_context(context_id: str) -> None:
    exists, tabs = _load_browser_tabs()
    if not exists:
        return
    remaining = [entry for entry in tabs if entry["context_id"] != context_id]
    if len(remaining) != len(tabs):
        try:
            _save_browser_tabs(remaining)
        except Exception as exc:
            PrintStyle.warning(f"Browser tab recovery state could not be updated: {exc}")


def has_restorable_browser_tabs(context_id: str) -> bool:
    exists, tabs = _load_browser_tabs()
    if not exists:
        for runtime_id in (SHARED_RUNTIME_ID, _safe_context_id(context_id)):
            session_dir = Path(
                files.get_abs_path(
                    "tmp",
                    "browser",
                    "sessions",
                    runtime_id,
                    "Default",
                    "Sessions",
                )
            )
            try:
                if any(session_dir.glob("Session_*")) or any(session_dir.glob("Tabs_*")):
                    return True
            except OSError:
                continue
        return False
    if not tabs:
        return False
    if str(
        get_browser_config().get(TAB_SCOPE_KEY, DEFAULT_BROWSER_TAB_SCOPE)
        or DEFAULT_BROWSER_TAB_SCOPE
    ) == "shared":
        return True
    return any(entry["context_id"] == str(context_id) for entry in tabs)


class BrowserRuntime:
    def __init__(self, context_id: str):
        self.context_id = str(context_id)
        self._core = BrowserConnection(self.context_id)
        self._worker = DeferredTask(thread_name=f"BrowserRuntime-{self.context_id}")
        self._closed = False

    async def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        return await self.call_for(self.context_id, method, *args, **kwargs)

    async def call_for(
        self,
        context_id: str,
        method: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if self._closed and method != "close":
            raise RuntimeError("Browser runtime is closed.")

        running_task = None

        async def runner():
            nonlocal running_task
            running_task = asyncio.current_task()
            return await self._core.call(str(context_id or self.context_id), method, *args, **kwargs)

        future = self._worker.event_loop_thread.run_coroutine(runner())
        result = asyncio.wrap_future(future)
        try:
            return await asyncio.shield(result)
        except asyncio.CancelledError:
            async def cancel_and_wait():
                if running_task is not None:
                    running_task.cancel()
                    await asyncio.gather(running_task, return_exceptions=True)

            cleanup = asyncio.wrap_future(
                self._worker.event_loop_thread.run_coroutine(cancel_and_wait())
            )
            while not cleanup.done():
                try:
                    await asyncio.shield(cleanup)
                except asyncio.CancelledError:
                    pass
            await asyncio.gather(result, return_exceptions=True)
            raise

    async def close(self, delete_profile: bool = False) -> None:
        if self._closed:
            return
        try:
            await asyncio.wrap_future(self._worker.event_loop_thread.run_coroutine(self._core.close(delete_profile)))
        finally:
            self._closed = True
            try:
                self._worker.kill(terminate_thread=True)
            finally:
                pass


class BrowserRuntimeSession:
    def __init__(self, context_id: str, runtime: BrowserRuntime):
        self.context_id = str(context_id)
        self._runtime = runtime

    async def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        return await self._runtime.call_for(self.context_id, method, *args, **kwargs)


_runtimes: dict[str, BrowserRuntimeSession] = {}
_shared_runtime: BrowserRuntime | None = None
_runtime_lock = threading.RLock()


async def get_runtime(
    context_id: str,
    *,
    create: bool = True,
) -> BrowserRuntimeSession | None:
    global _shared_runtime
    context_id = str(context_id or "").strip()
    if not context_id:
        raise ValueError("context_id is required")
    with _runtime_lock:
        runtime = _runtimes.get(context_id)
        if runtime is None and _shared_runtime is not None:
            runtime = BrowserRuntimeSession(context_id, _shared_runtime)
            if create:
                _runtimes[context_id] = runtime
        elif runtime is None and create:
            if _shared_runtime is None:
                _shared_runtime = BrowserRuntime(SHARED_RUNTIME_ID)
            runtime = BrowserRuntimeSession(context_id, _shared_runtime)
            _runtimes[context_id] = runtime
        return runtime


async def close_runtime(context_id: str, *, delete_profile: bool = True) -> None:
    context_id = str(context_id or "").strip()
    if not context_id:
        return
    _forget_browser_context(context_id)
    with _runtime_lock:
        runtime = _runtimes.pop(context_id, None)
        shared_runtime = _shared_runtime
    if runtime:
        await runtime.call("close_context")
    elif shared_runtime:
        await shared_runtime.call_for(context_id, "close_context")


def close_runtime_sync(context_id: str, *, delete_profile: bool = True) -> None:
    task = DeferredTask(thread_name="BrowserCleanup")
    task.start_task(close_runtime, context_id, delete_profile=delete_profile)
    try:
        task.result_sync(timeout=30)
    finally:
        task.kill()


async def close_all_runtimes(*, delete_profiles: bool = False) -> None:
    global _shared_runtime
    with _runtime_lock:
        _runtimes.clear()
        runtime = _shared_runtime
        _shared_runtime = None
    if delete_profiles:
        with contextlib.suppress(Exception):
            kvp.remove_persistent(BROWSER_TABS_KEY)
    if runtime:
        try:
            await runtime.close(delete_profile=delete_profiles)
        except Exception as exc:
            PrintStyle.warning(f"Browser runtime cleanup failed: {exc}")


def close_all_runtimes_sync() -> None:
    task = DeferredTask(thread_name="BrowserCleanupAll")
    task.start_task(close_all_runtimes, delete_profiles=False)
    try:
        task.result_sync(timeout=30)
    finally:
        task.kill(terminate_thread=True)


def known_context_ids() -> list[str]:
    with _runtime_lock:
        return sorted(_runtimes)


async def list_runtime_sessions() -> list[dict[str, Any]]:
    with _runtime_lock:
        runtimes = list(_runtimes.items())
        shared_runtime = _shared_runtime

    if shared_runtime and str(
        get_browser_config().get(TAB_SCOPE_KEY, DEFAULT_BROWSER_TAB_SCOPE)
        or DEFAULT_BROWSER_TAB_SCOPE
    ) == "shared":
        request_context_id = runtimes[0][0] if runtimes else SHARED_RUNTIME_ID
        try:
            listing = await shared_runtime.call_for(request_context_id, "list_all")
        except Exception as exc:
            PrintStyle.warning(f"Shared Browser runtime list failed: {exc}")
            return []
        grouped: dict[str, list[dict[str, Any]]] = {}
        for browser in listing.get("browsers") or []:
            context_id = str(browser.get("context_id") or SHARED_RUNTIME_ID)
            grouped.setdefault(context_id, []).append(browser)
        active_ids = listing.get("last_interacted_browser_ids") or {}
        return [
            {
                "context_id": context_id,
                "browsers": browsers,
                "last_interacted_browser_id": active_ids.get(context_id),
            }
            for context_id, browsers in grouped.items()
        ]

    sessions: list[dict[str, Any]] = []
    for context_id, runtime in runtimes:
        try:
            listing = await runtime.call("list")
        except Exception as exc:
            PrintStyle.warning(f"Browser runtime list failed for context {context_id}: {exc}")
            continue
        sessions.append(
            {
                "context_id": context_id,
                "browsers": listing.get("browsers") or [],
                "last_interacted_browser_id": listing.get("last_interacted_browser_id"),
            }
        )
    return sessions


atexit.register(close_all_runtimes_sync)
