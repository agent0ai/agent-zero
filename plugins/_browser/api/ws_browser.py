from __future__ import annotations

import asyncio
import base64
import contextlib
import time
from typing import Any, ClassVar

from agent import AgentContext
from helpers.ws import WsHandler
from helpers.ws_manager import WsResult
from plugins._browser.helpers.config import (
    DEFAULT_BROWSER_TAB_SCOPE,
    TAB_SCOPE_KEY,
    get_browser_config,
)
from plugins._browser.helpers.runtime import get_runtime, list_runtime_sessions


FRAME_READ_TIMEOUT_SECONDS = 0.5
FRAME_RETRY_DELAY_SECONDS = 0.5
FRAME_STATE_REFRESH_SECONDS = 0.75
SNAPSHOT_STATE_POLL_SECONDS = 0.75
SCREENCAST_STREAM_QUALITY = 80
SCREENSHOT_QUALITY = 92
VIEWER_TRANSPORT_SCREENCAST = "screencast"
VIEWER_TRANSPORT_SNAPSHOT = "snapshot"
VIEWER_TRANSPORTS = {VIEWER_TRANSPORT_SCREENCAST, VIEWER_TRANSPORT_SNAPSHOT}


class WsBrowser(WsHandler):
    _streams: ClassVar[dict[tuple[str, str], asyncio.Task[None]]] = {}

    async def on_disconnect(self, sid: str) -> None:
        for key in [key for key in self._streams if key[0] == sid]:
            task = self._streams.pop(key)
            task.cancel()

    async def process(
        self,
        event: str,
        data: dict[str, Any],
        sid: str,
    ) -> dict[str, Any] | WsResult | None:
        if not event.startswith("browser_"):
            return None

        if event == "browser_viewer_subscribe":
            return await self._subscribe(data, sid)
        if event == "browser_viewer_unsubscribe":
            return self._unsubscribe(data, sid)
        if event == "browser_viewer_snapshot":
            return await self._snapshot(data)
        if event == "browser_viewer_sessions":
            return await self._sessions(data)
        if event == "browser_viewer_command":
            return await self._command(data, sid)
        if event == "browser_viewer_input":
            return await self._input(data, sid)
        if event == "browser_viewer_annotation":
            return await self._annotation(data, sid)

        return WsResult.error(
            code="UNKNOWN_BROWSER_EVENT",
            message=f"Unknown browser event: {event}",
            correlation_id=data.get("correlationId"),
        )

    async def _subscribe(self, data: dict[str, Any], sid: str) -> dict[str, Any] | WsResult:
        context_id = self._context_id(data)
        if not context_id:
            return self._error("MISSING_CONTEXT", "context_id is required", data)
        if not AgentContext.get(context_id):
            return self._error("CONTEXT_NOT_FOUND", f"Context '{context_id}' was not found", data)

        create_browser = self._bool(data.get("create_browser", data.get("createBrowser")))
        runtime = await get_runtime(context_id, create=create_browser)
        listing = {"browsers": [], "last_interacted_browser_id": None}
        browsers: list[dict[str, Any]] = []
        if runtime:
            listing = await runtime.call("list")
            browsers = listing.get("browsers") or []
        if runtime and not browsers and create_browser:
            opened = await runtime.call("open", "")
            listing = await runtime.call("list")
            browsers = listing.get("browsers") or []
            if opened.get("id"):
                listing["last_interacted_browser_id"] = opened.get("id")
        active_id = self._active_browser_id(listing, data.get("browser_id"))
        initial_viewport = self._viewport_from_data(data)
        if runtime and active_id and initial_viewport:
            await runtime.call(
                "set_viewport",
                active_id,
                initial_viewport["width"],
                initial_viewport["height"],
            )
            listing = await runtime.call("list")
            browsers = listing.get("browsers") or []

        stream_key = (sid, context_id)
        existing = self._streams.pop(stream_key, None)
        if existing:
            existing.cancel()
        viewer_id = str(data.get("viewer_id") or "")
        viewer_transport = self._viewer_transport(data)
        binary_frames = self._bool(data.get("binary_frames", data.get("binaryFrames")))
        slim_frames = self._bool(data.get("slim_frames", data.get("slimFrames", binary_frames)))
        capture_scale = self._capture_scale_from_data(data)
        snapshot = None
        if runtime:
            if viewer_transport == VIEWER_TRANSPORT_SCREENCAST:
                stream_task = self._stream_frames(
                    sid,
                    context_id,
                    active_id,
                    viewer_id,
                    binary_frames=binary_frames,
                    slim_frames=slim_frames,
                    capture_scale=capture_scale,
                )
            else:
                stream_task = self._stream_state(sid, context_id, active_id, viewer_id)
            self._streams[stream_key] = asyncio.create_task(stream_task)
            snapshot = await self._snapshot_for_browser(runtime, active_id)

        browsers, all_browsers, tab_scope = await self._tabs_for_scope(context_id, browsers)

        return {
            "context_id": context_id,
            "active_browser_context_id": context_id,
            "active_browser_id": active_id,
            "snapshot": snapshot,
            "browsers": browsers,
            "all_browsers": all_browsers,
            "tab_scope": tab_scope,
            "viewer_id": viewer_id,
            "viewer_transport": viewer_transport,
            "binary_frames": binary_frames,
            "slim_frames": slim_frames,
        }

    def _unsubscribe(self, data: dict[str, Any], sid: str) -> dict[str, Any] | WsResult:
        context_id = self._context_id(data)
        if not context_id:
            return self._error("MISSING_CONTEXT", "context_id is required", data)
        task = self._streams.pop((sid, context_id), None)
        if task:
            task.cancel()
        return {"context_id": context_id, "unsubscribed": True}

    async def _sessions(self, data: dict[str, Any]) -> dict[str, Any]:
        context_id = self._context_id(data)
        tab_scope = self._tab_scope()
        if tab_scope == "shared":
            return {
                "context_id": context_id,
                "browsers": await self._all_browser_tabs(),
                "all_browsers": True,
                "tab_scope": tab_scope,
            }

        runtime = await get_runtime(context_id, create=False) if context_id else None
        listing = await runtime.call("list") if runtime else {}
        return {
            "context_id": context_id,
            "browsers": listing.get("browsers") or [],
            "all_browsers": False,
            "tab_scope": tab_scope,
        }

    async def _snapshot(self, data: dict[str, Any]) -> dict[str, Any] | WsResult:
        context_id = self._context_id(data)
        if not context_id:
            return self._error("MISSING_CONTEXT", "context_id is required", data)
        if not AgentContext.get(context_id):
            return self._error("CONTEXT_NOT_FOUND", f"Context '{context_id}' was not found", data)

        runtime = await get_runtime(context_id, create=False)
        if not runtime:
            browsers, all_browsers, tab_scope = await self._tabs_for_scope(context_id, [])
            return {
                "context_id": context_id,
                "active_browser_context_id": context_id,
                "active_browser_id": None,
                "snapshot": None,
                "browsers": browsers,
                "all_browsers": all_browsers,
                "tab_scope": tab_scope,
            }

        listing = await runtime.call("list")
        browsers = listing.get("browsers") or []
        active_id = self._active_browser_id(listing, data.get("browser_id"))
        snapshot = None
        if active_id:
            try:
                quality = int(data.get("quality") or SCREENSHOT_QUALITY)
            except (TypeError, ValueError):
                quality = SCREENSHOT_QUALITY
            with contextlib.suppress(Exception):
                snapshot = await runtime.call(
                    "screenshot",
                    active_id,
                    quality=quality,
                )

        browsers, all_browsers, tab_scope = await self._tabs_for_scope(context_id, browsers)

        return {
            "context_id": context_id,
            "active_browser_context_id": context_id,
            "active_browser_id": active_id,
            "snapshot": snapshot,
            "browsers": browsers,
            "all_browsers": all_browsers,
            "tab_scope": tab_scope,
        }

    async def _command(self, data: dict[str, Any], sid: str) -> dict[str, Any] | WsResult:
        context_id = self._context_id(data)
        if not context_id:
            return self._error("MISSING_CONTEXT", "context_id is required", data)
        runtime = await get_runtime(context_id)
        command = str(data.get("command") or "").strip().lower().replace("-", "_")
        browser_id = data.get("browser_id")
        viewer_id = str(data.get("viewer_id") or "")

        try:
            if command == "open":
                result = await runtime.call("open", data.get("url") or "")
            elif command == "navigate":
                result = await runtime.call("navigate", browser_id, data.get("url") or "")
            elif command == "back":
                result = await runtime.call("back", browser_id)
            elif command == "forward":
                result = await runtime.call("forward", browser_id)
            elif command == "reload":
                result = await runtime.call("reload", browser_id)
            elif command == "close":
                result = await runtime.call("close_browser", browser_id)
            elif command == "list":
                result = await runtime.call("list")
            else:
                return self._error("UNKNOWN_COMMAND", f"Unknown browser command: {command}", data)
        except Exception as exc:
            return self._error("COMMAND_FAILED", str(exc), data)

        listing = await runtime.call("list")
        last_interacted_browser_id = listing.get("last_interacted_browser_id")
        snapshot = await self._snapshot_for_result(runtime, result)
        browsers, all_browsers, tab_scope = await self._tabs_for_scope(
            context_id,
            listing.get("browsers") or [],
        )
        await self.emit_to(
            sid,
            "browser_viewer_state",
            {
                "context_id": context_id,
                "active_browser_context_id": context_id,
                "viewer_id": viewer_id,
                "command": command,
                "browser_id": browser_id,
                "result": result,
                "snapshot": snapshot,
                "browsers": browsers,
                "all_browsers": all_browsers,
                "tab_scope": tab_scope,
                "last_interacted_browser_id": last_interacted_browser_id,
                "viewer_transport": self._viewer_transport(data),
            },
            correlation_id=data.get("correlationId"),
        )
        return {
            "result": result,
            "snapshot": snapshot,
            "browsers": browsers,
            "all_browsers": all_browsers,
            "tab_scope": tab_scope,
            "active_browser_context_id": context_id,
            "last_interacted_browser_id": last_interacted_browser_id,
            "command": command,
            "browser_id": browser_id,
            "viewer_id": viewer_id,
            "viewer_transport": self._viewer_transport(data),
        }

    async def _input(self, data: dict[str, Any], sid: str) -> dict[str, Any] | WsResult:
        context_id = self._context_id(data)
        if not context_id:
            return self._error("MISSING_CONTEXT", "context_id is required", data)
        runtime = await get_runtime(context_id, create=False)
        if not runtime:
            return self._error("NO_BROWSER_RUNTIME", "No browser runtime exists for this context", data)

        input_type = str(data.get("input_type") or "").strip().lower()
        browser_id = data.get("browser_id")
        try:
            if input_type == "mouse":
                result = await runtime.call(
                    "mouse",
                    browser_id,
                    data.get("event_type") or "click",
                    float(data.get("x") or 0),
                    float(data.get("y") or 0),
                    data.get("button") or "left",
                )
            elif input_type == "keyboard":
                result = await runtime.call(
                    "keyboard",
                    browser_id,
                    key=str(data.get("key") or ""),
                    text=str(data.get("text") or ""),
                )
            elif input_type == "clipboard":
                result = await runtime.call(
                    "clipboard",
                    browser_id,
                    action=str(data.get("action") or ""),
                    text=str(data.get("text") or ""),
                )
            elif input_type == "viewport":
                result = await runtime.call(
                    "set_viewport",
                    browser_id,
                    int(data.get("width") or 0),
                    int(data.get("height") or 0),
                    restart_screencast=bool(data.get("restart_stream")),
                )
            elif input_type == "wheel":
                result = await runtime.call(
                    "wheel",
                    browser_id,
                    float(data.get("x") or 0),
                    float(data.get("y") or 0),
                    float(data.get("delta_x") or 0),
                    float(data.get("delta_y") or 0),
                )
            else:
                return self._error("UNKNOWN_INPUT", f"Unknown browser input: {input_type}", data)
        except Exception as exc:
            return self._error("INPUT_FAILED", str(exc), data)

        if input_type == "clipboard":
            response = {
                "state": result.get("state") if isinstance(result, dict) else result,
                "snapshot": None,
            }
            if isinstance(result, dict):
                response["clipboard"] = result.get("clipboard")
            return response

        return {
            "state": result,
            "snapshot": await self._snapshot_for_result(runtime, result)
            if input_type == "mouse"
            else None,
        }

    async def _annotation(self, data: dict[str, Any], sid: str) -> dict[str, Any] | WsResult:
        context_id = self._context_id(data)
        if not context_id:
            return self._error("MISSING_CONTEXT", "context_id is required", data)
        runtime = await get_runtime(context_id, create=False)
        if not runtime:
            return self._error("NO_BROWSER_RUNTIME", "No browser runtime exists for this context", data)

        browser_id = data.get("browser_id")
        viewer_id = str(data.get("viewer_id") or "")
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        try:
            annotation = await runtime.call("annotation_target", browser_id, payload)
        except Exception as exc:
            return self._error("ANNOTATION_FAILED", str(exc), data)

        return {
            "annotation": annotation,
            "context_id": context_id,
            "browser_id": browser_id,
            "viewer_id": viewer_id,
        }

    async def _snapshot_for_result(
        self,
        runtime: Any,
        result: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(result, dict):
            return None
        state = result.get("state") if isinstance(result.get("state"), dict) else result
        browser_id = state.get("id") if isinstance(state, dict) else result.get("id")
        if not browser_id:
            return None
        with contextlib.suppress(Exception):
            return await runtime.call("screenshot", browser_id, quality=SCREENSHOT_QUALITY)
        return None

    async def _snapshot_for_browser(
        self,
        runtime: Any,
        browser_id: int | str | None,
    ) -> dict[str, Any] | None:
        if not browser_id:
            return None
        with contextlib.suppress(Exception):
            return await runtime.call("screenshot", browser_id, quality=SCREENSHOT_QUALITY)
        return None

    @staticmethod
    def _tab_scope() -> str:
        scope = str(
            (get_browser_config() or {}).get(TAB_SCOPE_KEY, DEFAULT_BROWSER_TAB_SCOPE)
            or DEFAULT_BROWSER_TAB_SCOPE
        ).strip().lower().replace("-", "_")
        return "shared" if scope == "shared" else DEFAULT_BROWSER_TAB_SCOPE

    async def _tabs_for_scope(
        self,
        context_id: str,
        browsers: list[dict[str, Any]] | None,
    ) -> tuple[list[dict[str, Any]], bool, str]:
        tab_scope = self._tab_scope()
        if tab_scope == "shared":
            return await self._all_browser_tabs(), True, tab_scope
        return browsers or [], False, tab_scope

    async def _all_browser_tabs(self) -> list[dict[str, Any]]:
        browsers: list[dict[str, Any]] = []
        for session in await list_runtime_sessions():
            context_id = str(session.get("context_id") or "")
            for browser in session.get("browsers") or []:
                entry = dict(browser or {})
                entry.setdefault("context_id", context_id)
                browsers.append(entry)
        return browsers

    async def _stream_frames(
        self,
        sid: str,
        context_id: str,
        browser_id: int | str | None,
        viewer_id: str = "",
        *,
        binary_frames: bool = False,
        slim_frames: bool = False,
        capture_scale: float = 1.0,
    ) -> None:
        runtime = None
        stream_id = None
        while True:
            try:
                runtime = await get_runtime(context_id, create=False)
                if not runtime:
                    await self._emit_empty_frame(
                        sid,
                        context_id,
                        viewer_id=viewer_id,
                        frame_source=VIEWER_TRANSPORT_SCREENCAST,
                    )
                    await asyncio.sleep(FRAME_RETRY_DELAY_SECONDS)
                    continue

                listing = await runtime.call("list")
                browsers = listing.get("browsers") or []
                active_id = self._active_browser_id(listing, browser_id)
                if not active_id:
                    await self._emit_viewer_state(
                        sid,
                        context_id,
                        active_id,
                        browsers=browsers,
                        viewer_id=viewer_id,
                        state=None,
                        viewer_transport=VIEWER_TRANSPORT_SCREENCAST,
                    )
                    await asyncio.sleep(FRAME_RETRY_DELAY_SECONDS)
                    continue

                screencast = await runtime.call(
                    "start_screencast",
                    active_id,
                    quality=SCREENCAST_STREAM_QUALITY,
                    every_nth_frame=1,
                    capture_scale=capture_scale,
                )
                stream_id = screencast["stream_id"]
                active_id = screencast["browser_id"]
                state = screencast.get("state")
                await self._emit_viewer_state(
                    sid,
                    context_id,
                    active_id,
                    browsers=browsers,
                    viewer_id=viewer_id,
                    state=state,
                    viewer_transport=VIEWER_TRANSPORT_SCREENCAST,
                )

                last_state_refresh = 0.0
                last_state_signature = self._state_signature(active_id, browsers)
                frame_sequence = 0
                server_loop = asyncio.get_running_loop()
                stop_event = asyncio.Event()

                async def emit_frame(frame: dict[str, Any]) -> None:
                    nonlocal frame_sequence
                    try:
                        frame_sequence += 1
                        payload = self._frame_payload(
                            frame,
                            context_id=context_id,
                            viewer_id=viewer_id,
                            browser_id=active_id,
                            sequence=frame_sequence,
                            binary_frames=binary_frames,
                        )
                        if not slim_frames:
                            payload["browsers"] = browsers
                            payload["state"] = state
                        await self._emit_to_connected_viewer(sid, "browser_viewer_frame", payload)
                    except BaseException:
                        stop_event.set()
                        raise

                def frame_consumer(frame: dict[str, Any]):
                    return asyncio.run_coroutine_threadsafe(emit_frame(frame), server_loop)

                def stop_consumer() -> None:
                    server_loop.call_soon_threadsafe(stop_event.set)

                await runtime.call("attach_screencast_consumer", stream_id, frame_consumer, stop_consumer)

                while True:
                    if stop_event.is_set():
                        break
                    now = time.monotonic()
                    if now - last_state_refresh >= FRAME_STATE_REFRESH_SECONDS:
                        listing = await runtime.call("list")
                        browsers = listing.get("browsers") or []
                        browser_ids = {str(browser.get("id")) for browser in browsers}
                        if str(active_id) not in browser_ids:
                            break
                        state = self._state_for_browser(browsers, active_id, state)
                        state_signature = self._state_signature(active_id, browsers)
                        if state_signature != last_state_signature:
                            await self._emit_viewer_state(
                                sid,
                                context_id,
                                active_id,
                                browsers=browsers,
                                viewer_id=viewer_id,
                                state=state,
                                viewer_transport=VIEWER_TRANSPORT_SCREENCAST,
                            )
                            last_state_signature = state_signature
                        last_state_refresh = now

                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=FRAME_READ_TIMEOUT_SECONDS)
                        break
                    except TimeoutError:
                        continue
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(FRAME_RETRY_DELAY_SECONDS)
            finally:
                if runtime and stream_id:
                    with contextlib.suppress(Exception):
                        await runtime.call("stop_screencast", stream_id)
                    stream_id = None

    async def _stream_state(
        self,
        sid: str,
        context_id: str,
        browser_id: int | str | None,
        viewer_id: str = "",
    ) -> None:
        last_signature = None
        while True:
            try:
                runtime = await get_runtime(context_id, create=False)
                if not runtime:
                    signature = (None, ())
                    if signature != last_signature:
                        await self._emit_empty_frame(
                            sid,
                            context_id,
                            viewer_id=viewer_id,
                            frame_source=VIEWER_TRANSPORT_SNAPSHOT,
                        )
                        last_signature = signature
                    await asyncio.sleep(FRAME_RETRY_DELAY_SECONDS)
                    continue

                listing = await runtime.call("list")
                browsers = listing.get("browsers") or []
                active_id = self._active_browser_id(listing, browser_id)
                state = self._state_for_browser(browsers, active_id, None) if active_id else None
                signature = (
                    str(active_id or ""),
                    tuple(
                        (
                            str(browser.get("context_id") or context_id),
                            str(browser.get("id") or ""),
                            str(browser.get("currentUrl") or ""),
                            str(browser.get("title") or ""),
                            bool(browser.get("loading")),
                        )
                        for browser in browsers
                    ),
                )
                if signature != last_signature:
                    await self._emit_viewer_state(
                        sid,
                        context_id,
                        active_id,
                        browsers=browsers,
                        viewer_id=viewer_id,
                        state=state,
                        viewer_transport=VIEWER_TRANSPORT_SNAPSHOT,
                    )
                    last_signature = signature
                await asyncio.sleep(SNAPSHOT_STATE_POLL_SECONDS)
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(FRAME_RETRY_DELAY_SECONDS)

    @staticmethod
    def _active_browser_id(
        listing: dict[str, Any],
        requested_browser_id: int | str | None,
    ) -> int | str | None:
        browsers = listing.get("browsers") or []
        browser_ids = {str(browser.get("id")) for browser in browsers}
        requested_id = str(requested_browser_id or "") if requested_browser_id else ""
        active_id = (
            requested_browser_id
            if requested_id and requested_id in browser_ids
            else listing.get("last_interacted_browser_id")
        )
        if active_id and str(active_id) not in browser_ids:
            active_id = None
        if not active_id and browsers:
            active_id = browsers[0].get("id")
        return active_id

    @staticmethod
    def _state_for_browser(
        browsers: list[dict[str, Any]],
        browser_id: int | str,
        current_state: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        for browser in browsers:
            if str(browser.get("id")) == str(browser_id):
                return browser
        return current_state

    @staticmethod
    def _state_signature(
        active_id: int | str | None,
        browsers: list[dict[str, Any]],
    ) -> tuple[str, tuple[tuple[str, str, str, str, bool], ...]]:
        return (
            str(active_id or ""),
            tuple(
                (
                    str(browser.get("context_id") or ""),
                    str(browser.get("id") or ""),
                    str(browser.get("currentUrl") or ""),
                    str(browser.get("title") or ""),
                    bool(browser.get("loading")),
                )
                for browser in browsers
            ),
        )

    @staticmethod
    def _frame_payload(
        frame: dict[str, Any],
        *,
        context_id: str,
        viewer_id: str,
        browser_id: int | str,
        sequence: int,
        binary_frames: bool,
    ) -> dict[str, Any]:
        image = str(frame.get("image") or "")
        payload: dict[str, Any] = {
            "context_id": context_id,
            "viewer_id": viewer_id,
            "browser_id": browser_id,
            "seq": sequence,
            "mime": frame.get("mime") or "image/jpeg",
            "frame_source": VIEWER_TRANSPORT_SCREENCAST,
            "viewer_transport": VIEWER_TRANSPORT_SCREENCAST,
        }
        dimensions = WsBrowser._frame_dimensions(frame.get("metadata"))
        if dimensions:
            payload.update(dimensions)
        if binary_frames:
            try:
                payload["image"] = base64.b64decode(image, validate=False)
                payload["encoding"] = "binary"
            except Exception:
                payload["image"] = image
                payload["encoding"] = "base64"
        else:
            payload["image"] = image
            payload["encoding"] = "base64"
        return payload

    @staticmethod
    def _frame_dimensions(metadata: Any) -> dict[str, int]:
        if not isinstance(metadata, dict):
            return {}
        for width_key, height_key in (
            ("expectedWidth", "expectedHeight"),
            ("deviceWidth", "deviceHeight"),
            ("jpegWidth", "jpegHeight"),
        ):
            try:
                width = int(metadata.get(width_key) or 0)
                height = int(metadata.get(height_key) or 0)
            except (TypeError, ValueError):
                continue
            if width > 0 and height > 0:
                return {"width": width, "height": height}
        return {}

    async def _emit_viewer_state(
        self,
        sid: str,
        context_id: str,
        browser_id: int | str | None,
        *,
        browsers: list[dict[str, Any]] | None = None,
        viewer_id: str = "",
        state: dict[str, Any] | None = None,
        viewer_transport: str = VIEWER_TRANSPORT_SNAPSHOT,
    ) -> None:
        browsers, all_browsers, tab_scope = await self._tabs_for_scope(context_id, browsers or [])
        await self._emit_to_connected_viewer(
            sid,
            "browser_viewer_state",
            {
                "context_id": context_id,
                "active_browser_context_id": context_id,
                "viewer_id": viewer_id,
                "browser_id": browser_id,
                "active_browser_id": browser_id,
                "browsers": browsers or [],
                "state": state,
                "all_browsers": all_browsers,
                "tab_scope": tab_scope,
                "viewer_transport": viewer_transport,
            },
        )

    async def _emit_empty_frame(
        self,
        sid: str,
        context_id: str,
        *,
        browsers: list[dict[str, Any]] | None = None,
        viewer_id: str = "",
        frame_source: str = "",
    ) -> None:
        browsers, all_browsers, tab_scope = await self._tabs_for_scope(context_id, browsers or [])
        await self._emit_to_connected_viewer(
            sid,
            "browser_viewer_frame",
            {
                "context_id": context_id,
                "viewer_id": viewer_id,
                "browser_id": None,
                "browsers": browsers or [],
                "all_browsers": all_browsers,
                "tab_scope": tab_scope,
                "image": "",
                "mime": "",
                "state": None,
                "frame_source": frame_source,
                "viewer_transport": frame_source or VIEWER_TRANSPORT_SNAPSHOT,
            },
        )

    async def _emit_to_connected_viewer(
        self,
        sid: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        manager = getattr(self, "_manager", None)
        if manager is not None:
            with manager.lock:
                connected = (getattr(self, "namespace", "/ws"), sid) in manager.connections
            if not connected:
                raise asyncio.CancelledError()
        await self.emit_to(sid, event, data)

    @staticmethod
    def _viewer_transport(data: dict[str, Any]) -> str:
        raw = (
            data.get("viewer_transport")
            or data.get("viewerTransport")
            or data.get("surface_transport")
            or data.get("surfaceTransport")
            or data.get("transport")
            or ""
        )
        normalized = str(raw or "").strip().lower().replace("-", "_")
        if normalized == "live":
            normalized = VIEWER_TRANSPORT_SCREENCAST
        if normalized in VIEWER_TRANSPORTS:
            return normalized
        return VIEWER_TRANSPORT_SNAPSHOT

    @staticmethod
    def _viewport_from_data(data: dict[str, Any]) -> dict[str, int] | None:
        try:
            width = int(data.get("viewport_width") or data.get("width") or 0)
            height = int(data.get("viewport_height") or data.get("height") or 0)
        except (TypeError, ValueError):
            return None
        if width < 80 or height < 80:
            return None
        return {
            "width": max(320, min(4096, width)),
            "height": max(200, min(4096, height)),
        }

    @staticmethod
    def _capture_scale_from_data(data: dict[str, Any]) -> float:
        try:
            scale = float(
                data.get("device_pixel_ratio")
                or data.get("devicePixelRatio")
                or data.get("pixel_ratio")
                or data.get("pixelRatio")
                or 1
            )
        except (TypeError, ValueError):
            return 1.0
        return max(1.0, min(2.0, scale))

    @staticmethod
    def _context_id(data: dict[str, Any]) -> str:
        return str(data.get("context_id") or data.get("context") or "").strip()

    @staticmethod
    def _bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        return str(value or "").strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _error(code: str, message: str, data: dict[str, Any]) -> WsResult:
        return WsResult.error(
            code=code,
            message=message,
            correlation_id=data.get("correlationId"),
        )
