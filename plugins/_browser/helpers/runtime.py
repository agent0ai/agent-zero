from __future__ import annotations

import atexit
import asyncio
import base64
import contextlib
import os
import re
import shutil
import signal
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from helpers import files
from helpers.defer import DeferredTask
from helpers.errors import RepairableException
from helpers.print_style import PrintStyle

from plugins._browser.helpers.config import (
    DEFAULT_HOMEPAGE_KEY,
    DEFAULT_MAX_OPEN_TABS,
    MAX_OPEN_TABS_KEY,
    build_browser_launch_config,
    get_browser_config,
)
from plugins._browser.helpers.playwright import configure_playwright_env, ensure_playwright_binary
from plugins._browser.helpers.url import normalize_url


PLUGIN_DIR = Path(__file__).resolve().parents[1]
CONTENT_HELPER_PATH = PLUGIN_DIR / "assets" / "browser-page-content.js"
RUNTIME_DATA_KEY = "_browser_runtime"
DEFAULT_VIEWPORT = {"width": 1024, "height": 768}
CHROME_SINGLETON_FILES = ("SingletonLock", "SingletonCookie", "SingletonSocket")
SCREENCAST_MAX_WIDTH = 4096
SCREENCAST_MAX_HEIGHT = 4096
VIEWPORT_SIZE_TOLERANCE = 4
VIEWPORT_REMOUNT_PAUSE_SECONDS = 0.05
CLIPBOARD_BRIDGE_SCRIPT = r"""
(payload) => {
  const action = String(payload?.action || "").trim().toLowerCase();
  const text = String(payload?.text || "");
  const result = {
    action,
    text: "",
    changed: false,
    default_prevented: false,
    handled: false,
    method: "dom",
  };
  const textInputTypes = new Set([
    "",
    "email",
    "number",
    "password",
    "search",
    "tel",
    "text",
    "url",
  ]);

  function deepestActiveElement() {
    let active = document.activeElement || document.body || document.documentElement;
    while (active?.shadowRoot?.activeElement) {
      active = active.shadowRoot.activeElement;
    }
    return active || document.body || document.documentElement;
  }

  function editableTarget(element) {
    if (!element) return null;
    if (isTextControl(element) || element.isContentEditable) return element;
    const closest = element.closest?.("input, textarea, [contenteditable]");
    if (closest && (isTextControl(closest) || closest.isContentEditable)) return closest;
    return element;
  }

  function isTextControl(element) {
    if (!element) return false;
    const tagName = String(element.tagName || "").toLowerCase();
    if (tagName === "textarea") {
      return !element.disabled && !element.readOnly;
    }
    if (tagName !== "input") return false;
    const type = String(element.type || "text").toLowerCase();
    return textInputTypes.has(type) && !element.disabled && !element.readOnly;
  }

  function selectedText(element) {
    if (isTextControl(element)) {
      try {
        const start = Number(element.selectionStart);
        const end = Number(element.selectionEnd);
        if (Number.isFinite(start) && Number.isFinite(end) && end > start) {
          return String(element.value || "").slice(start, end);
        }
      } catch {}
      return "";
    }
    const selection = globalThis.getSelection?.();
    return selection ? String(selection.toString() || "") : "";
  }

  function makeClipboardData(seedText = "") {
    let transfer = null;
    try {
      transfer = new DataTransfer();
    } catch {}
    if (transfer && seedText) {
      transfer.setData("text/plain", seedText);
      transfer.setData("text", seedText);
    }
    return transfer;
  }

  function clipboardDataText(transfer) {
    if (!transfer) return "";
    return String(transfer.getData("text/plain") || transfer.getData("text") || "");
  }

  function makeClipboardEvent(type, transfer) {
    let event = null;
    try {
      event = new ClipboardEvent(type, {
        bubbles: true,
        cancelable: true,
        clipboardData: transfer,
      });
    } catch {}
    if (!event) {
      event = new Event(type, { bubbles: true, cancelable: true });
    }
    if (transfer && !event.clipboardData) {
      try {
        Object.defineProperty(event, "clipboardData", { value: transfer });
      } catch {}
    }
    return event;
  }

  function dispatchClipboardEvent(target, type, seedText = "") {
    const transfer = makeClipboardData(seedText);
    const event = makeClipboardEvent(type, transfer);
    (target || document.body || document.documentElement).dispatchEvent(event);
    return {
      defaultPrevented: Boolean(event.defaultPrevented),
      text: clipboardDataText(event.clipboardData || transfer),
    };
  }

  function dispatchInputEvent(element, type, inputType, data = null) {
    let event = null;
    try {
      event = new InputEvent(type, {
        bubbles: true,
        cancelable: type === "beforeinput",
        inputType,
        data,
      });
    } catch {}
    if (!event) {
      event = new Event(type, {
        bubbles: true,
        cancelable: type === "beforeinput",
      });
    }
    return element.dispatchEvent(event);
  }

  function insertIntoTextControl(element, value) {
    if (!isTextControl(element)) return false;
    let start = 0;
    let end = 0;
    try {
      start = Number(element.selectionStart);
      end = Number(element.selectionEnd);
    } catch {
      return false;
    }
    if (!Number.isFinite(start) || !Number.isFinite(end)) return false;
    if (!dispatchInputEvent(element, "beforeinput", "insertFromPaste", value)) {
      return false;
    }
    element.setRangeText(value, start, end, "end");
    dispatchInputEvent(element, "input", "insertFromPaste", value);
    return true;
  }

  function insertIntoContentEditable(element, value) {
    if (!element?.isContentEditable) return false;
    if (!dispatchInputEvent(element, "beforeinput", "insertFromPaste", value)) {
      return false;
    }
    const selection = globalThis.getSelection?.();
    if (!selection || selection.rangeCount === 0) return false;
    try {
      if (document.queryCommandSupported?.("insertText") && document.execCommand("insertText", false, value)) {
        return true;
      }
    } catch {}
    const range = selection.getRangeAt(0);
    range.deleteContents();
    const node = document.createTextNode(value);
    range.insertNode(node);
    range.setStartAfter(node);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    dispatchInputEvent(element, "input", "insertFromPaste", value);
    return true;
  }

  function insertText(element, value) {
    return insertIntoTextControl(element, value) || insertIntoContentEditable(element, value);
  }

  function removeSelectedText(element) {
    if (isTextControl(element)) {
      let start = 0;
      let end = 0;
      try {
        start = Number(element.selectionStart);
        end = Number(element.selectionEnd);
      } catch {
        return false;
      }
      if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return false;
      if (!dispatchInputEvent(element, "beforeinput", "deleteByCut", null)) {
        return false;
      }
      element.setRangeText("", start, end, "start");
      dispatchInputEvent(element, "input", "deleteByCut", null);
      return true;
    }
    if (!element?.isContentEditable) return false;
    const selection = globalThis.getSelection?.();
    if (!selection || selection.rangeCount === 0 || !String(selection.toString() || "")) {
      return false;
    }
    if (!dispatchInputEvent(element, "beforeinput", "deleteByCut", null)) {
      return false;
    }
    selection.deleteFromDocument();
    dispatchInputEvent(element, "input", "deleteByCut", null);
    return true;
  }

  const target = editableTarget(deepestActiveElement());
  if (action === "paste") {
    const event = dispatchClipboardEvent(target, "paste", text);
    result.default_prevented = event.defaultPrevented;
    result.handled = true;
    result.text = text;
    if (!event.defaultPrevented) {
      result.changed = insertText(target, text);
    }
    return result;
  }

  if (action === "copy" || action === "cut") {
    const selectionText = selectedText(target);
    const event = dispatchClipboardEvent(target, action, selectionText);
    result.default_prevented = event.defaultPrevented;
    result.text = event.text || selectionText;
    result.handled = Boolean(result.text || event.defaultPrevented);
    if (action === "cut" && result.text && !event.defaultPrevented) {
      result.changed = removeSelectedText(target);
    }
    return result;
  }

  result.error = `Unsupported clipboard action: ${action}`;
  return result;
}
"""

_SAFE_CONTEXT_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


def _nudged_viewport(viewport: dict[str, int]) -> dict[str, int]:
    width = int(viewport["width"])
    height = int(viewport["height"])
    if width < 4096:
        return {"width": width + 1, "height": height}
    if width > 320:
        return {"width": width - 1, "height": height}
    if height < 4096:
        return {"width": width, "height": height + 1}
    return {"width": width, "height": height - 1}


def _safe_context_id(context_id: str) -> str:
    return _SAFE_CONTEXT_RE.sub("_", str(context_id or "default")).strip("._") or "default"


@dataclass
class BrowserPage:
    id: int
    page: Any


class _BrowserScreencast:
    def __init__(
        self,
        *,
        stream_id: str,
        browser_id: int,
        session: Any,
        mime: str,
    ):
        self.id = stream_id
        self.browser_id = browser_id
        self.session = session
        self.mime = mime
        self.queue = asyncio.Queue(maxsize=1)
        self.stopped = False
        self._ack_tasks: set[asyncio.Task] = set()
        self._expected_width = 0
        self._expected_height = 0

    async def start(
        self,
        *,
        quality: int,
        every_nth_frame: int,
        viewport: dict[str, int],
    ) -> None:
        self.session.on("Page.screencastFrame", self._on_frame)
        width = max(320, min(4096, int(viewport.get("width") or DEFAULT_VIEWPORT["width"])))
        height = max(200, min(4096, int(viewport.get("height") or DEFAULT_VIEWPORT["height"])))
        self._expected_width = width
        self._expected_height = height
        with contextlib.suppress(Exception):
            await self.session.send("Page.enable")
        await self._apply_cdp_viewport_with_remount({"width": width, "height": height})
        await self.session.send(
            "Page.startScreencast",
            {
                "format": "jpeg",
                "quality": max(20, min(95, int(quality))),
                "maxWidth": SCREENCAST_MAX_WIDTH,
                "maxHeight": SCREENCAST_MAX_HEIGHT,
                "everyNthFrame": max(1, int(every_nth_frame)),
            },
        )

    async def _apply_cdp_viewport_with_remount(self, viewport: dict[str, int]) -> None:
        await self._apply_cdp_viewport(viewport)
        await asyncio.sleep(VIEWPORT_REMOUNT_PAUSE_SECONDS)
        await self._apply_cdp_viewport(_nudged_viewport(viewport))
        await asyncio.sleep(VIEWPORT_REMOUNT_PAUSE_SECONDS)
        await self._apply_cdp_viewport(viewport)
        await asyncio.sleep(VIEWPORT_REMOUNT_PAUSE_SECONDS)

    async def _apply_cdp_viewport(self, viewport: dict[str, int]) -> None:
        width = max(320, min(4096, int(viewport.get("width") or DEFAULT_VIEWPORT["width"])))
        height = max(200, min(4096, int(viewport.get("height") or DEFAULT_VIEWPORT["height"])))
        await self.session.send(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
                "mobile": False,
                "dontSetVisibleSize": True,
            },
        )
        with contextlib.suppress(Exception):
            await self.session.send(
                "Emulation.setVisibleSize",
                {
                    "width": width,
                    "height": height,
                },
            )

    async def next_frame(self, timeout: float = 1.0) -> dict[str, Any]:
        frame = await asyncio.wait_for(self.queue.get(), timeout=max(0.1, float(timeout)))
        if frame is None:
            raise RuntimeError("Browser screencast stopped.")
        return frame

    async def pop_frame(self) -> dict[str, Any] | None:
        try:
            frame = self.queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
        if frame is None:
            raise RuntimeError("Browser screencast stopped.")
        return frame

    async def stop(self) -> None:
        if self.stopped:
            return
        self.stopped = True
        self._drop_queued_frames()
        with contextlib.suppress(asyncio.QueueFull):
            self.queue.put_nowait(None)
        with contextlib.suppress(Exception):
            await self.session.send("Page.stopScreencast")
        for task in list(self._ack_tasks):
            task.cancel()
        if self._ack_tasks:
            await asyncio.gather(*self._ack_tasks, return_exceptions=True)
            self._ack_tasks.clear()
        with contextlib.suppress(Exception):
            await self.session.detach()

    def _on_frame(self, params: dict[str, Any]) -> None:
        if self.stopped:
            return
        task = asyncio.create_task(self._handle_frame(params or {}))
        self._ack_tasks.add(task)
        task.add_done_callback(self._ack_tasks.discard)

    async def _handle_frame(self, params: dict[str, Any]) -> None:
        try:
            data = params.get("data") or ""
            if data:
                metadata = dict(params.get("metadata") or {})
                size = self._jpeg_size(data)
                if size:
                    metadata["jpegWidth"], metadata["jpegHeight"] = size
                metadata["expectedWidth"] = self._expected_width
                metadata["expectedHeight"] = self._expected_height
                self._queue_latest(
                    {
                        "browser_id": self.browser_id,
                        "mime": self.mime,
                        "image": data,
                        "metadata": metadata,
                    }
                )
        finally:
            session_id = params.get("sessionId")
            if session_id is not None and not self.stopped:
                with contextlib.suppress(Exception):
                    await self.session.send(
                        "Page.screencastFrameAck",
                        {"sessionId": int(session_id)},
                    )

    def _queue_latest(self, frame: dict[str, Any]) -> None:
        self._drop_queued_frames()
        with contextlib.suppress(asyncio.QueueFull):
            self.queue.put_nowait(frame)

    @staticmethod
    def _jpeg_size(data: str) -> tuple[int, int] | None:
        try:
            raw = base64.b64decode(data, validate=False)
        except Exception:
            return None
        if len(raw) < 10 or raw[:2] != b"\xff\xd8":
            return None
        index = 2
        standalone_markers = {0x01, *range(0xD0, 0xD8)}
        size_markers = {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }
        while index < len(raw) - 9:
            if raw[index] != 0xFF:
                index += 1
                continue
            while index < len(raw) and raw[index] == 0xFF:
                index += 1
            if index >= len(raw):
                return None
            marker = raw[index]
            index += 1
            if marker in standalone_markers:
                continue
            if index + 2 > len(raw):
                return None
            segment_length = int.from_bytes(raw[index : index + 2], "big")
            if segment_length < 2 or index + segment_length > len(raw):
                return None
            if marker in size_markers and segment_length >= 7:
                height = int.from_bytes(raw[index + 3 : index + 5], "big")
                width = int.from_bytes(raw[index + 5 : index + 7], "big")
                return width, height
            index += segment_length
        return None

    def _drop_queued_frames(self) -> None:
        while True:
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                return


class BrowserRuntime:
    def __init__(self, context_id: str):
        self.context_id = str(context_id)
        self._core = _BrowserRuntimeCore(self.context_id)
        self._worker = DeferredTask(thread_name=f"BrowserRuntime-{self.context_id}")
        self._closed = False

    async def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        if self._closed and method != "close":
            raise RuntimeError("Browser runtime is closed.")

        async def runner():
            fn = getattr(self._core, method)
            return await fn(*args, **kwargs)

        return await self._worker.execute_inside(runner)

    async def close(self, delete_profile: bool = False) -> None:
        if self._closed:
            return
        try:
            await self.call("close", delete_profile=delete_profile)
        finally:
            self._closed = True
            self._worker.kill(terminate_thread=True)


class _BrowserRuntimeCore:
    _VALID_MODIFIERS = {"Control", "Shift", "Alt", "Meta"}
    _KEY_ALIASES = {
        "cmd": "Meta",
        "command": "Meta",
        "control": "Control",
        "ctrl": "Control",
        "escape": "Escape",
        "esc": "Escape",
        "meta": "Meta",
        "option": "Alt",
        "return": "Enter",
        "space": "Space",
    }
    _POPUP_WAIT_SECONDS = 2.0

    def __init__(self, context_id: str):
        self.context_id = context_id
        self.safe_context_id = _safe_context_id(context_id)
        self.playwright = None
        self.context = None
        self.pages: dict[int, BrowserPage] = {}
        self.screencasts: dict[str, _BrowserScreencast] = {}
        self.next_browser_id = 1
        self.last_interacted_browser_id: int | None = None
        self._content_helper_source: str | None = None
        self._start_lock: asyncio.Lock | None = None
        self._registry_lock: asyncio.Lock | None = None
        self._closing = False
        self._pending_popups: list[asyncio.Future[int]] = []
        self._background_popup_pages: set[int] = set()

    def _ensure_registry_lock(self) -> asyncio.Lock:
        if self._registry_lock is None:
            self._registry_lock = asyncio.Lock()
        return self._registry_lock

    def _maybe_promote(self, resolved_id: int) -> None:
        # Promote only if the target IS the current active tab or no tab is
        # active yet. Cross-tab work on a backgrounded tab does not steal
        # viewer focus.
        current = self.last_interacted_browser_id
        if current is None or current == resolved_id:
            self.last_interacted_browser_id = int(resolved_id)

    def _background_focus_target(
        self,
        previous_focus: int | None,
        fallback_id: int,
    ) -> int | None:
        if previous_focus in self.pages:
            return int(previous_focus)
        if fallback_id in self.pages:
            return int(fallback_id)
        return next(iter(sorted(self.pages)), None)

    def _normalize_modifiers(self, modifiers: list[str] | str | None) -> list[str] | None:
        if modifiers is None:
            return None
        if isinstance(modifiers, str):
            raw = [modifiers]
        elif isinstance(modifiers, list):
            raw = modifiers
        else:
            raise ValueError("modifiers must be a string or list")
        normalized = [str(modifier).strip() for modifier in raw if str(modifier).strip()]
        if not normalized:
            return None
        bad = set(normalized) - self._VALID_MODIFIERS
        if bad:
            raise ValueError(
                f"unsupported modifiers: {sorted(bad)}; allowed: {sorted(self._VALID_MODIFIERS)}"
            )
        return normalized

    @classmethod
    def _normalize_keys(cls, keys: list[str] | str | None) -> list[str]:
        if keys is None:
            return []
        if isinstance(keys, str):
            raw = re.split(r"\s*\+\s*|\s*,\s*", keys.strip())
        elif isinstance(keys, list):
            raw = keys
        else:
            raw = [str(keys)]
        normalized: list[str] = []
        for key in raw:
            value = str(key or "").strip()
            if not value:
                continue
            normalized.append(
                cls._KEY_ALIASES.get(
                    value.lower(),
                    value.upper() if len(value) == 1 and value.isalpha() else value,
                )
            )
        return normalized

    @staticmethod
    def _has_reference(reference_id: int | str | None) -> bool:
        return reference_id is not None and str(reference_id).strip() != ""

    def _screenshot_output_path(self, browser_id: int, path: str = "") -> tuple[Path, str, str]:
        raw_path = str(path or "").strip()
        if raw_path:
            output_path = Path(files.fix_dev_path(raw_path) if raw_path.startswith("/a0/") else raw_path)
            if not output_path.is_absolute():
                output_path = Path(files.get_abs_path(str(output_path)))
            suffix = output_path.suffix.lower()
            if suffix == ".png":
                return output_path, "png", "image/png"
            if suffix not in {".jpg", ".jpeg"}:
                output_path = output_path.with_suffix(".jpg") if not suffix else output_path.with_name(f"{output_path.name}.jpg")
            return output_path, "jpeg", "image/jpeg"

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        millis = int((time.time() % 1) * 1000)
        output_path = self.screenshots_dir / f"browser-{int(browser_id)}-{timestamp}-{millis:03d}.jpg"
        return output_path, "jpeg", "image/jpeg"

    @staticmethod
    def _normalize_upload_paths(path: str = "", paths: list[str] | None = None) -> list[str]:
        raw_paths: list[str] = []
        if paths:
            if not isinstance(paths, list):
                raise ValueError("paths must be a list of file paths")
            raw_paths.extend(str(item or "").strip() for item in paths)
        if str(path or "").strip():
            raw_paths.append(str(path or "").strip())

        normalized_paths: list[str] = []
        for raw_path in raw_paths:
            if not raw_path:
                continue
            candidate = Path(files.fix_dev_path(raw_path) if raw_path.startswith("/a0/") else raw_path)
            if not candidate.is_absolute():
                candidate = Path(files.get_abs_path(str(candidate)))
            candidate = candidate.expanduser().resolve()
            if not candidate.is_file():
                raise FileNotFoundError(f"Upload file does not exist: {candidate}")
            normalized_paths.append(str(candidate))

        if not normalized_paths:
            raise ValueError("upload_file requires path or non-empty paths")
        return normalized_paths

    @staticmethod
    def _multi_group_key(call: dict[str, Any]) -> Any:
        value = call.get("browser_id")
        if value is None or str(value).strip() == "":
            return None
        raw = str(value).strip()
        if raw.startswith("browser-"):
            raw = raw.split("-", 1)[1]
        try:
            return int(raw)
        except ValueError:
            return raw

    @property
    def profile_dir(self) -> Path:
        return Path(files.get_abs_path("tmp/browser/sessions", self.safe_context_id))

    @property
    def downloads_dir(self) -> Path:
        return Path(files.get_abs_path("usr/downloads/browser"))

    @property
    def screenshots_dir(self) -> Path:
        return Path(files.get_abs_path("tmp/browser/screenshots", self.safe_context_id))

    async def ensure_started(self) -> None:
        if self._context_is_alive():
            return
        if self.context:
            await self._discard_stale_context("Browser context is stale; restarting.")

        if self._start_lock is None:
            self._start_lock = asyncio.Lock()

        async with self._start_lock:
            if self._context_is_alive():
                return
            if self.context:
                await self._discard_stale_context("Browser context is stale; restarting.")
            elif self.playwright and not self._closing:
                await self._stop_playwright("Browser context closed; restarting Playwright.")
            await self._start()

    def _context_is_alive(self) -> bool:
        if not self.context:
            return False
        try:
            pages = getattr(self.context, "pages")
            len(pages() if callable(pages) else pages)
            return True
        except AttributeError:
            # Lightweight test doubles may not model Playwright's pages property.
            return True
        except Exception:
            return False

    async def _discard_stale_context(self, message: str) -> None:
        PrintStyle.warning(message)
        self._discard_context_state()
        await self._stop_playwright("Playwright stop after Browser context loss failed")

    def _discard_context_state(self) -> None:
        for waiter in self._pending_popups:
            if not waiter.done():
                waiter.set_exception(RuntimeError("Browser context closed."))
        self._pending_popups.clear()
        self._background_popup_pages.clear()
        self.pages.clear()
        self.last_interacted_browser_id = None
        for screencast in self.screencasts.values():
            screencast.stopped = True
            screencast._drop_queued_frames()
            with contextlib.suppress(asyncio.QueueFull):
                screencast.queue.put_nowait(None)
            for task in list(screencast._ack_tasks):
                task.cancel()
            screencast._ack_tasks.clear()
        self.screencasts.clear()
        self.context = None

    async def _stop_playwright(self, warning: str) -> None:
        if not self.playwright:
            return
        try:
            await self.playwright.stop()
        except Exception as exc:
            PrintStyle.warning(f"{warning}: {exc}")
        finally:
            self.playwright = None

    async def _start(self) -> None:
        from playwright.async_api import async_playwright

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self._release_orphaned_profile_singleton()
        browser_config = get_browser_config()
        launch_config = build_browser_launch_config(browser_config)
        configure_playwright_env()
        browser_binary = ensure_playwright_binary()

        self.playwright = await async_playwright().start()
        launch_kwargs: dict[str, Any] = {
            "user_data_dir": str(self.profile_dir),
            "headless": True,
            "accept_downloads": True,
            "downloads_path": str(self.downloads_dir),
            "viewport": DEFAULT_VIEWPORT,
            "screen": DEFAULT_VIEWPORT,
            "no_viewport": False,
            "args": launch_config["args"],
        }
        if launch_config["channel"]:
            launch_kwargs["channel"] = launch_config["channel"]
        else:
            launch_kwargs["executable_path"] = str(browser_binary)
        try:
            self.context = await self.playwright.chromium.launch_persistent_context(
                **launch_kwargs
            )
        except Exception:
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception:
                    pass
                self.playwright = None
            raise
        self.context.set_default_timeout(30000)
        self.context.set_default_navigation_timeout(30000)
        self.context.on("close", self._on_context_closed)
        self.context.on("page", self._on_new_page_sync)
        await self.context.add_init_script(path=str(CONTENT_HELPER_PATH))

        for page in list(self.context.pages):
            if page.url == "about:blank":
                try:
                    await page.close()
                except Exception:
                    pass
                continue
            await self._register_page(page)

    def _release_orphaned_profile_singleton(self) -> None:
        lock_path = self.profile_dir / "SingletonLock"
        owner_pid = self._profile_singleton_owner_pid(lock_path)
        if owner_pid and self._process_owns_profile(owner_pid):
            PrintStyle.warning(
                f"Stopping orphaned Chromium process {owner_pid} for Browser profile {self.safe_context_id}."
            )
            self._terminate_process(owner_pid)

        for name in CHROME_SINGLETON_FILES:
            singleton_path = self.profile_dir / name
            try:
                if singleton_path.exists() or singleton_path.is_symlink():
                    singleton_path.unlink()
            except OSError as exc:
                PrintStyle.warning(f"Could not remove stale Browser profile lock {singleton_path}: {exc}")

    @staticmethod
    def _profile_singleton_owner_pid(lock_path: Path) -> int | None:
        try:
            target = os.readlink(lock_path)
        except OSError:
            return None
        raw_pid = target.rsplit("-", 1)[-1]
        if not raw_pid.isdigit():
            return None
        return int(raw_pid)

    def _process_owns_profile(self, pid: int) -> bool:
        cmdline_path = Path("/proc") / str(pid) / "cmdline"
        try:
            raw = cmdline_path.read_bytes()
        except OSError:
            return False
        cmdline = raw.replace(b"\x00", b" ").decode("utf-8", errors="ignore")
        return "chrome" in cmdline.lower() and str(self.profile_dir) in cmdline

    @staticmethod
    def _terminate_process(pid: int) -> None:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        except OSError as exc:
            PrintStyle.warning(f"Could not stop orphaned Chromium process {pid}: {exc}")
            return

        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if not Path("/proc", str(pid)).exists():
                return
            time.sleep(0.1)

        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError as exc:
            PrintStyle.warning(f"Could not force-stop orphaned Chromium process {pid}: {exc}")

    async def open(self, url: str = "") -> dict[str, Any]:
        await self.ensure_started()
        self._ensure_can_open_page()
        page = await self.context.new_page()
        browser_page = await self._register_page(page)
        self.last_interacted_browser_id = browser_page.id
        target_url = self._initial_url(url)
        if target_url and target_url != "about:blank":
            await self._goto(page, normalize_url(target_url))
        else:
            await self._settle(page)
        return {"id": browser_page.id, "state": await self._state(browser_page.id)}

    def _initial_url(self, url: str = "") -> str:
        raw_url = str(url or "").strip()
        if raw_url:
            return raw_url
        return str(get_browser_config().get(DEFAULT_HOMEPAGE_KEY) or "about:blank").strip() or "about:blank"

    def _max_open_tabs(self) -> int:
        try:
            value = int(get_browser_config().get(MAX_OPEN_TABS_KEY, DEFAULT_MAX_OPEN_TABS))
        except (TypeError, ValueError):
            value = DEFAULT_MAX_OPEN_TABS
        return max(1, value)

    def _tab_limit_error(self) -> RepairableException:
        max_open_tabs = self._max_open_tabs()
        return RepairableException(
            f"Browser tab limit reached ({len(self.pages)}/{max_open_tabs}). "
            "Navigate an existing browser_id or close tabs with close/close_all before opening more."
        )

    def _ensure_can_open_page(self) -> None:
        if len(self.pages) >= self._max_open_tabs():
            raise self._tab_limit_error()

    async def list(self, include_content: bool = False) -> dict[str, Any]:
        await self.ensure_started()
        ids = sorted(self.pages)
        if not ids:
            return {
                "browsers": [],
                "last_interacted_browser_id": self.last_interacted_browser_id,
            }
        states_task = asyncio.gather(*(self._state(bid) for bid in ids))
        if include_content:
            contents_task = asyncio.gather(
                *(self.content(bid) for bid in ids),
                return_exceptions=True,
            )
            states, contents = await asyncio.gather(states_task, contents_task)
            out: list[dict[str, Any]] = []
            for idx, bid in enumerate(ids):
                entry = states[idx]
                c = contents[idx]
                if isinstance(c, Exception):
                    entry["content_error"] = str(c)
                else:
                    entry["content"] = c
                out.append(entry)
        else:
            out = await states_task
        return {
            "browsers": out,
            "last_interacted_browser_id": self.last_interacted_browser_id,
        }

    async def multi(self, calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(calls, list) or not calls:
            raise ValueError("multi requires a non-empty list of calls")
        groups: dict[Any, list[tuple[int, dict[str, Any]]]] = {}
        for idx, call in enumerate(calls):
            if not isinstance(call, dict):
                raise ValueError(f"calls[{idx}] is not an object")
            key = self._multi_group_key(call)
            groups.setdefault(key, []).append((idx, call))

        results: list[dict[str, Any] | None] = [None] * len(calls)

        async def run_group(group: list[tuple[int, dict[str, Any]]]) -> None:
            for idx, call in group:
                try:
                    out = await self._dispatch_call(call)
                    results[idx] = {"ok": True, "result": out}
                except Exception as exc:
                    results[idx] = {"ok": False, "error": str(exc)}

        await asyncio.gather(*(run_group(g) for g in groups.values()))
        return [r if r is not None else {"ok": False, "error": "missing"} for r in results]

    async def _dispatch_call(self, call: dict[str, Any]) -> Any:
        action = str(call.get("action") or "").strip().lower().replace("-", "_")
        bid = call.get("browser_id")
        if action == "open":
            return await self.open(call.get("url") or "")
        if action == "screenshot":
            return await self.screenshot_file(
                bid,
                quality=int(call.get("quality") or 80),
                full_page=bool(call.get("full_page")),
                path=call.get("path") or "",
            )
        if action == "list":
            return await self.list(include_content=bool(call.get("include_content")))
        if action == "state":
            return await self.state(bid)
        if action in {"set_active", "setactive", "activate", "focus"}:
            return await self.set_active(bid)
        if action == "navigate":
            return await self.navigate(bid, call.get("url") or "")
        if action == "back":
            return await self.back(bid)
        if action == "forward":
            return await self.forward(bid)
        if action == "reload":
            return await self.reload(bid)
        if action == "content":
            payload = None
            sels = call.get("selectors")
            sel = call.get("selector")
            if sels:
                payload = {"selectors": sels}
            elif sel:
                payload = {"selector": sel}
            return await self.content(bid, payload)
        if action == "detail":
            ref = call.get("ref")
            if ref is None:
                raise ValueError("detail requires ref")
            return await self.detail(bid, ref)
        if action == "click":
            ref = call.get("ref")
            if ref is None and (call.get("x") or call.get("y")):
                return await self.mouse(
                    bid,
                    "click",
                    float(call.get("x") or 0),
                    float(call.get("y") or 0),
                    button=call.get("button") or "left",
                    modifiers=self._normalize_modifiers(call.get("modifiers")),
                )
            if ref is None:
                raise ValueError("click requires ref")
            return await self.click(
                bid, ref,
                modifiers=self._normalize_modifiers(call.get("modifiers")),
                focus_popup=call.get("focus_popup"),
            )
        if action == "type":
            ref = call.get("ref")
            if ref is None:
                return await self.keyboard(
                    bid,
                    key="",
                    text=str(call.get("text") or ""),
                )
            return await self.type(bid, ref, call.get("text") or "")
        if action == "submit":
            ref = call.get("ref")
            if ref is None:
                raise ValueError("submit requires ref")
            return await self.submit(bid, ref)
        if action in {"type_submit", "typesubmit"}:
            ref = call.get("ref")
            if ref is None:
                raise ValueError("type_submit requires ref")
            return await self.type_submit(bid, ref, call.get("text") or "")
        if action == "scroll":
            ref = call.get("ref")
            if ref is None:
                raise ValueError("scroll requires ref")
            return await self.scroll(bid, ref)
        if action == "evaluate":
            return await self.evaluate(bid, call.get("script") or "")
        if action in {"key_chord", "keychord"}:
            keys = self._normalize_keys(call.get("keys"))
            if not keys:
                raise ValueError("key_chord requires non-empty keys")
            return await self.key_chord(bid, keys)
        if action == "mouse":
            return await self.mouse(
                bid, call.get("event_type") or "click",
                float(call.get("x") or 0), float(call.get("y") or 0),
                button=call.get("button") or "left",
                modifiers=self._normalize_modifiers(call.get("modifiers")),
            )
        if action == "hover":
            return await self.hover(
                bid,
                ref=call.get("ref"),
                x=float(call.get("x") or 0),
                y=float(call.get("y") or 0),
                offset_x=float(call.get("offset_x") or 0),
                offset_y=float(call.get("offset_y") or 0),
            )
        if action == "double_click":
            return await self.double_click(
                bid,
                ref=call.get("ref"),
                x=float(call.get("x") or 0),
                y=float(call.get("y") or 0),
                button=call.get("button") or "left",
                modifiers=self._normalize_modifiers(call.get("modifiers")),
                offset_x=float(call.get("offset_x") or 0),
                offset_y=float(call.get("offset_y") or 0),
            )
        if action == "right_click":
            return await self.right_click(
                bid,
                ref=call.get("ref"),
                x=float(call.get("x") or 0),
                y=float(call.get("y") or 0),
                modifiers=self._normalize_modifiers(call.get("modifiers")),
                offset_x=float(call.get("offset_x") or 0),
                offset_y=float(call.get("offset_y") or 0),
            )
        if action == "drag":
            return await self.drag(
                bid,
                ref=call.get("ref"),
                target_ref=call.get("target_ref"),
                x=float(call.get("x") or 0),
                y=float(call.get("y") or 0),
                to_x=float(call.get("to_x") or 0),
                to_y=float(call.get("to_y") or 0),
                offset_x=float(call.get("offset_x") or 0),
                offset_y=float(call.get("offset_y") or 0),
                target_offset_x=float(call.get("target_offset_x") or 0),
                target_offset_y=float(call.get("target_offset_y") or 0),
            )
        if action == "wheel":
            return await self.wheel(
                bid,
                float(call.get("x") or 0),
                float(call.get("y") or 0),
                float(call.get("delta_x") or 0),
                float(call.get("delta_y") or 0),
            )
        if action == "keyboard":
            return await self.keyboard(
                bid,
                key=str(call.get("key") or ""),
                text=str(call.get("text") or ""),
            )
        if action == "clipboard":
            clipboard_action = str(
                call.get("clipboard_action")
                or call.get("operation")
                or call.get("event_type")
                or ""
            ).strip().lower()
            return await self.clipboard(
                bid,
                action=clipboard_action,
                text=str(call.get("text") or ""),
            )
        if action in {"copy", "cut", "paste"}:
            return await self.clipboard(
                bid,
                action=action,
                text=str(call.get("text") or ""),
            )
        if action == "set_viewport":
            return await self.set_viewport(
                bid,
                int(call.get("width") or 0),
                int(call.get("height") or 0),
            )
        if action == "select_option":
            ref = call.get("ref")
            if ref is None:
                raise ValueError("select_option requires ref")
            return await self.select_option(
                bid,
                ref,
                value=str(call.get("value") or ""),
                values=call.get("values"),
            )
        if action == "set_checked":
            ref = call.get("ref")
            if ref is None:
                raise ValueError("set_checked requires ref")
            checked = call.get("checked")
            return await self.set_checked(
                bid,
                ref,
                checked=True if checked is None else bool(checked),
            )
        if action == "upload_file":
            ref = call.get("ref")
            if ref is None:
                raise ValueError("upload_file requires ref")
            return await self.upload_file(
                bid,
                ref,
                path=call.get("path") or "",
                paths=call.get("paths"),
            )
        if action == "close":
            return await self.close_browser(bid)
        if action == "close_all":
            return await self.close_all_browsers()
        raise ValueError(f"unknown action: {action}")

    async def set_active(self, browser_id: int | str | None) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        # Explicit focus change — bypass _maybe_promote.
        self.last_interacted_browser_id = int(resolved_id)
        return await self._state(resolved_id)

    async def state(self, browser_id: int | str | None = None) -> dict[str, Any]:
        await self.ensure_started()
        return await self._state(self._resolve_browser_id(browser_id))

    async def navigate(self, browser_id: int | str | None, url: str) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await self._goto(page, normalize_url(url))
        self._maybe_promote(resolved_id)
        return await self._state(resolved_id)

    async def back(self, browser_id: int | str | None = None) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await page.go_back(wait_until="domcontentloaded", timeout=10000)
        await self._settle(page)
        self._maybe_promote(resolved_id)
        return await self._state(resolved_id)

    async def forward(self, browser_id: int | str | None = None) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await page.go_forward(wait_until="domcontentloaded", timeout=10000)
        await self._settle(page)
        self._maybe_promote(resolved_id)
        return await self._state(resolved_id)

    async def reload(self, browser_id: int | str | None = None) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await page.reload(wait_until="domcontentloaded", timeout=15000)
        await self._settle(page)
        self._maybe_promote(resolved_id)
        return await self._state(resolved_id)

    async def content(
        self,
        browser_id: int | str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await self._ensure_content_helper(page)
        result = await page.evaluate(
            "(payload) => globalThis.__spaceBrowserPageContent__.capture(payload || null)",
            payload or None,
        )
        self._maybe_promote(resolved_id)
        return result or {}

    async def detail(self, browser_id: int | str | None, reference_id: int | str) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await self._ensure_content_helper(page)
        result = await page.evaluate(
            "(ref) => globalThis.__spaceBrowserPageContent__.detail(ref)",
            reference_id,
        )
        self._maybe_promote(resolved_id)
        return result or {}

    async def annotation_target(
        self,
        browser_id: int | str | None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await self._ensure_content_helper(page)
        result = await page.evaluate(
            "(payload) => globalThis.__spaceBrowserPageContent__.annotate(payload || null)",
            payload or None,
        )
        self._maybe_promote(resolved_id)
        return result or {}

    async def evaluate(self, browser_id: int | str | None, script: str) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        result = await page.evaluate(str(script or "undefined"))
        self._maybe_promote(resolved_id)
        return {"result": result, "state": await self._state(resolved_id)}

    async def click(
        self,
        browser_id: int | str | None,
        reference_id: int | str,
        modifiers: list[str] | str | None = None,
        focus_popup: bool | None = None,
    ) -> dict[str, Any]:
        modifiers = self._normalize_modifiers(modifiers)
        if modifiers:
            return await self._modifier_click(browser_id, reference_id, modifiers, focus_popup)
        return await self._reference_action("click", browser_id, reference_id)

    async def _modifier_click(
        self,
        browser_id: int | str | None,
        reference_id: int | str,
        modifiers: list[str],
        focus_popup: bool | None,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        previous_focus = self.last_interacted_browser_id
        page = self._page(resolved_id)
        await self._ensure_content_helper(page)

        box = await page.evaluate(
            "(ref) => globalThis.__spaceBrowserPageContent__.boundingBoxFor(ref)",
            reference_id,
        )

        background = focus_popup is False or (
            focus_popup is None and bool({"Control", "Meta"} & set(modifiers))
        )

        loop = asyncio.get_running_loop()
        waiter: asyncio.Future[int] = loop.create_future()
        self._pending_popups.append(waiter)

        warning: str | None = None
        opened_id: int | None = None
        try:
            box_has_geometry = bool(box and box.get("width") and box.get("height"))
            box_selector = box.get("selector") if box else None
            if box_has_geometry:
                cx = box["x"] + box["width"] / 2
                cy = box["y"] + box["height"] / 2
                # Mouse.click does not accept modifiers; hold them via keyboard.
                pressed: list[str] = []
                try:
                    for mod in modifiers:
                        await page.keyboard.down(mod)
                        pressed.append(mod)
                    await page.mouse.click(cx, cy)
                finally:
                    for mod in reversed(pressed):
                        with contextlib.suppress(Exception):
                            await page.keyboard.up(mod)
                await self._settle(page, short=False)
            elif box_selector:
                try:
                    await page.locator(box_selector).click(
                        modifiers=list(modifiers), force=True, timeout=5000
                    )
                    await self._settle(page, short=False)
                except Exception as exc:
                    await self._reference_action("click", browser_id, reference_id)
                    warning = f"modifiers ignored: locator click failed ({exc})"
            else:
                await self._reference_action("click", browser_id, reference_id)
                warning = "modifiers ignored: target geometry unavailable"

            try:
                opened_id = await asyncio.wait_for(
                    asyncio.shield(waiter), timeout=self._POPUP_WAIT_SECONDS
                )
            except asyncio.TimeoutError:
                opened_id = None
            finally:
                if waiter in self._pending_popups:
                    self._pending_popups.remove(waiter)
                if not waiter.done():
                    waiter.cancel()

            if opened_id is not None and background:
                if self.last_interacted_browser_id == opened_id:
                    # Force focus back to the tab that was active before the
                    # background click; the popup hook may have promoted.
                    self.last_interacted_browser_id = self._background_focus_target(
                        previous_focus,
                        resolved_id,
                    )
        finally:
            if waiter in self._pending_popups:
                self._pending_popups.remove(waiter)

        if background:
            # Background-mode click: preserve the pre-click focus even when
            # the clicked tab itself was not active.
            self.last_interacted_browser_id = self._background_focus_target(
                previous_focus,
                resolved_id,
            )
        return {
            "action": {
                "ref": reference_id,
                "modifiers": list(modifiers),
                "opened_browser_ids": [opened_id] if opened_id is not None else [],
                **({"warning": warning} if warning else {}),
            },
            "state": await self._state(resolved_id),
        }

    async def key_chord(
        self,
        browser_id: int | str | None,
        keys: list[str],
    ) -> dict[str, Any]:
        if not keys:
            raise ValueError("key_chord requires at least one key")
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        pressed: list[str] = []
        try:
            for k in keys:
                await page.keyboard.down(k)
                pressed.append(k)
        finally:
            for k in reversed(pressed):
                with contextlib.suppress(Exception):
                    await page.keyboard.up(k)
        await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return await self._state(resolved_id)

    async def submit(self, browser_id: int | str | None, reference_id: int | str) -> dict[str, Any]:
        return await self._reference_action("submit", browser_id, reference_id)

    async def scroll(self, browser_id: int | str | None, reference_id: int | str) -> dict[str, Any]:
        return await self._reference_action("scroll", browser_id, reference_id)

    async def type(
        self,
        browser_id: int | str | None,
        reference_id: int | str,
        text: str,
    ) -> dict[str, Any]:
        return await self._reference_action("type", browser_id, reference_id, text)

    async def type_submit(
        self,
        browser_id: int | str | None,
        reference_id: int | str,
        text: str,
    ) -> dict[str, Any]:
        return await self._reference_action("typeSubmit", browser_id, reference_id, text)

    async def clipboard(
        self,
        browser_id: int | str | None,
        *,
        action: str,
        text: str = "",
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        normalized_action = str(action or "").strip().lower()
        if normalized_action not in {"copy", "cut", "paste"}:
            raise ValueError(f"Unsupported clipboard action: {normalized_action}")

        clipboard_result: dict[str, Any]
        try:
            clipboard_result = await page.evaluate(
                CLIPBOARD_BRIDGE_SCRIPT,
                {
                    "action": normalized_action,
                    "text": str(text or ""),
                },
            ) or {}
        except Exception as exc:
            clipboard_result = {
                "action": normalized_action,
                "text": "",
                "changed": False,
                "default_prevented": False,
                "handled": False,
                "error": str(exc),
            }

        if (
            normalized_action == "paste"
            and text
            and not clipboard_result.get("changed")
            and not clipboard_result.get("default_prevented")
        ):
            if await self._insert_clipboard_text(page, str(text)):
                clipboard_result["changed"] = True
                clipboard_result["method"] = "keyboard.insert_text"
        elif normalized_action in {"copy", "cut"} and not clipboard_result.get("text"):
            with contextlib.suppress(Exception):
                shortcut = "Control+C" if normalized_action == "copy" else "Control+X"
                await page.keyboard.press(shortcut)
                clipboard_result["keyboard_shortcut"] = True

        await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return {
            "state": await self._state(resolved_id),
            "clipboard": clipboard_result,
        }

    async def close_browser(self, browser_id: int | str | None = None) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        await self._stop_screencasts_for_browser(resolved_id)
        page = self._page(resolved_id)
        await page.close()
        self.pages.pop(resolved_id, None)
        if self.last_interacted_browser_id == resolved_id:
            self.last_interacted_browser_id = next(iter(sorted(self.pages)), None)
        return await self.list()

    async def close_all_browsers(self) -> dict[str, Any]:
        await self.ensure_started()
        await self._stop_all_screencasts()
        for browser_id in list(self.pages):
            try:
                await self.pages[browser_id].page.close()
            except Exception:
                pass
        self.pages.clear()
        self.last_interacted_browser_id = None
        return {"browsers": [], "last_interacted_browser_id": None}

    async def screenshot(
        self,
        browser_id: int | str | None = None,
        *,
        quality: int = 70,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        image = await page.screenshot(type="jpeg", quality=max(20, min(95, int(quality))))
        return {
            "browser_id": resolved_id,
            "mime": "image/jpeg",
            "image": base64.b64encode(image).decode("ascii"),
            "state": await self._state(resolved_id),
        }

    async def screenshot_file(
        self,
        browser_id: int | str | None = None,
        *,
        quality: int = 80,
        full_page: bool = False,
        path: str = "",
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        output_path, image_type, mime = self._screenshot_output_path(resolved_id, path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        clamped_quality = max(20, min(95, int(quality)))
        screenshot_kwargs: dict[str, Any] = {
            "path": str(output_path),
            "type": image_type,
            "full_page": bool(full_page),
        }
        if image_type == "jpeg":
            screenshot_kwargs["quality"] = clamped_quality
        await page.screenshot(**screenshot_kwargs)
        local_path = str(output_path)
        return {
            "browser_id": resolved_id,
            "path": local_path,
            "a0_path": files.normalize_a0_path(local_path),
            "mime": mime,
            "state": await self._state(resolved_id),
            "vision_load": {
                "tool_name": "vision_load",
                "tool_args": {
                    "paths": [local_path],
                },
            },
        }

    async def start_screencast(
        self,
        browser_id: int | str | None = None,
        *,
        quality: int = 78,
        every_nth_frame: int = 1,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        stream_id = uuid.uuid4().hex
        session = await self.context.new_cdp_session(page)
        screencast = _BrowserScreencast(
            stream_id=stream_id,
            browser_id=resolved_id,
            session=session,
            mime="image/jpeg",
        )
        self.screencasts[stream_id] = screencast
        try:
            await screencast.start(
                quality=quality,
                every_nth_frame=every_nth_frame,
                viewport=page.viewport_size or DEFAULT_VIEWPORT,
            )
        except Exception:
            self.screencasts.pop(stream_id, None)
            await screencast.stop()
            raise
        self._maybe_promote(resolved_id)
        return {
            "stream_id": stream_id,
            "browser_id": resolved_id,
            "state": await self._state(resolved_id),
        }

    async def read_screencast_frame(
        self,
        stream_id: str,
        *,
        timeout: float = 1.0,
    ) -> dict[str, Any]:
        screencast = self.screencasts.get(str(stream_id or ""))
        if not screencast:
            raise KeyError("Browser screencast is not active.")
        return await screencast.next_frame(timeout=timeout)

    async def pop_screencast_frame(self, stream_id: str) -> dict[str, Any] | None:
        screencast = self.screencasts.get(str(stream_id or ""))
        if not screencast:
            raise KeyError("Browser screencast is not active.")
        return await screencast.pop_frame()

    async def stop_screencast(self, stream_id: str) -> None:
        screencast = self.screencasts.pop(str(stream_id or ""), None)
        if screencast:
            await screencast.stop()

    async def set_viewport(
        self,
        browser_id: int | str | None,
        width: int,
        height: int,
        restart_screencast: bool = False,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        viewport = {
            "width": max(320, min(4096, int(width or DEFAULT_VIEWPORT["width"]))),
            "height": max(200, min(4096, int(height or DEFAULT_VIEWPORT["height"]))),
        }
        current_viewport = page.viewport_size or {}
        changed = (
            abs(int(current_viewport.get("width") or 0) - viewport["width"])
            > VIEWPORT_SIZE_TOLERANCE
            or abs(int(current_viewport.get("height") or 0) - viewport["height"])
            > VIEWPORT_SIZE_TOLERANCE
        )
        should_remount_viewport = changed or restart_screencast
        if should_remount_viewport:
            await self._stop_screencasts_for_browser(resolved_id)
        if changed:
            await self._apply_viewport_with_remount(page, viewport)
        elif restart_screencast:
            await self._remount_viewport(page, viewport)
        if should_remount_viewport:
            await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return {"state": await self._state(resolved_id), "viewport": viewport}

    async def _apply_viewport_with_remount(self, page: Any, viewport: dict[str, int]) -> None:
        await page.set_viewport_size(viewport)
        await asyncio.sleep(VIEWPORT_REMOUNT_PAUSE_SECONDS)
        await self._remount_viewport(page, viewport)

    async def _remount_viewport(self, page: Any, viewport: dict[str, int]) -> None:
        nudged_viewport = self._nudged_viewport(viewport)
        await page.set_viewport_size(nudged_viewport)
        await asyncio.sleep(VIEWPORT_REMOUNT_PAUSE_SECONDS)
        await page.set_viewport_size(viewport)

    @staticmethod
    def _nudged_viewport(viewport: dict[str, int]) -> dict[str, int]:
        return _nudged_viewport(viewport)

    async def _point_for(
        self,
        page: Any,
        reference_id: int | str,
        *,
        offset_x: float = 0,
        offset_y: float = 0,
    ) -> dict[str, Any]:
        await self._ensure_content_helper(page)
        point = await page.evaluate(
            "(args) => globalThis.__spaceBrowserPageContent__.pointFor(args.ref, args.offsets)",
            {
                "ref": reference_id,
                "offsets": {
                    "offset_x": float(offset_x),
                    "offset_y": float(offset_y),
                    "useOffsets": bool(offset_x or offset_y),
                },
            },
        )
        if not point or not isinstance(point, dict):
            raise ValueError(f"Could not resolve Browser ref {reference_id!r} to a viewport point")
        return point

    async def _input_point(
        self,
        page: Any,
        reference_id: int | str | None,
        *,
        x: float = 0,
        y: float = 0,
        offset_x: float = 0,
        offset_y: float = 0,
    ) -> dict[str, Any]:
        if self._has_reference(reference_id):
            return await self._point_for(
                page,
                reference_id,
                offset_x=offset_x,
                offset_y=offset_y,
            )
        return {
            "x": float(x),
            "y": float(y),
            "rect": None,
            "selector": None,
        }

    async def hover(
        self,
        browser_id: int | str | None,
        ref: int | str | None = None,
        x: float = 0,
        y: float = 0,
        offset_x: float = 0,
        offset_y: float = 0,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        point = await self._input_point(
            page,
            ref,
            x=x,
            y=y,
            offset_x=offset_x,
            offset_y=offset_y,
        )
        await page.mouse.move(float(point["x"]), float(point["y"]))
        self._maybe_promote(resolved_id)
        return {
            "action": {
                "point": point,
                "ref": ref if self._has_reference(ref) else None,
            },
            "state": await self._state(resolved_id),
        }

    async def double_click(
        self,
        browser_id: int | str | None,
        ref: int | str | None = None,
        x: float = 0,
        y: float = 0,
        button: str = "left",
        modifiers: list[str] | str | None = None,
        offset_x: float = 0,
        offset_y: float = 0,
    ) -> dict[str, Any]:
        modifiers = self._normalize_modifiers(modifiers)
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        point = await self._input_point(
            page,
            ref,
            x=x,
            y=y,
            offset_x=offset_x,
            offset_y=offset_y,
        )
        pressed: list[str] = []
        try:
            if modifiers:
                for mod in modifiers:
                    await page.keyboard.down(mod)
                    pressed.append(mod)
            await page.mouse.dblclick(float(point["x"]), float(point["y"]), button=button or "left")
        finally:
            for mod in reversed(pressed):
                with contextlib.suppress(Exception):
                    await page.keyboard.up(mod)
        await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return {
            "action": {
                "button": button or "left",
                "modifiers": modifiers or [],
                "point": point,
                "ref": ref if self._has_reference(ref) else None,
            },
            "state": await self._state(resolved_id),
        }

    async def right_click(
        self,
        browser_id: int | str | None,
        ref: int | str | None = None,
        x: float = 0,
        y: float = 0,
        modifiers: list[str] | str | None = None,
        offset_x: float = 0,
        offset_y: float = 0,
    ) -> dict[str, Any]:
        modifiers = self._normalize_modifiers(modifiers)
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        point = await self._input_point(
            page,
            ref,
            x=x,
            y=y,
            offset_x=offset_x,
            offset_y=offset_y,
        )
        pressed: list[str] = []
        try:
            if modifiers:
                for mod in modifiers:
                    await page.keyboard.down(mod)
                    pressed.append(mod)
            await page.mouse.click(float(point["x"]), float(point["y"]), button="right")
        finally:
            for mod in reversed(pressed):
                with contextlib.suppress(Exception):
                    await page.keyboard.up(mod)
        await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return {
            "action": {
                "button": "right",
                "modifiers": modifiers or [],
                "point": point,
                "ref": ref if self._has_reference(ref) else None,
            },
            "state": await self._state(resolved_id),
        }

    async def drag(
        self,
        browser_id: int | str | None,
        ref: int | str | None = None,
        target_ref: int | str | None = None,
        x: float = 0,
        y: float = 0,
        to_x: float = 0,
        to_y: float = 0,
        offset_x: float = 0,
        offset_y: float = 0,
        target_offset_x: float = 0,
        target_offset_y: float = 0,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        start_point = await self._input_point(
            page,
            ref,
            x=x,
            y=y,
            offset_x=offset_x,
            offset_y=offset_y,
        )
        end_point = await self._input_point(
            page,
            target_ref,
            x=to_x,
            y=to_y,
            offset_x=target_offset_x,
            offset_y=target_offset_y,
        )
        await page.mouse.move(float(start_point["x"]), float(start_point["y"]))
        await page.mouse.down()
        await page.mouse.move(float(end_point["x"]), float(end_point["y"]), steps=12)
        await page.mouse.up()
        await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return {
            "action": {
                "from": start_point,
                "ref": ref if self._has_reference(ref) else None,
                "target_ref": target_ref if self._has_reference(target_ref) else None,
                "to": end_point,
            },
            "state": await self._state(resolved_id),
        }

    async def select_option(
        self,
        browser_id: int | str | None,
        ref: int | str,
        value: str = "",
        values: list[str] | None = None,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await self._ensure_content_helper(page)
        action = await page.evaluate(
            "(args) => globalThis.__spaceBrowserPageContent__.select(args.ref, args.values)",
            {
                "ref": ref,
                "values": values if values is not None else value,
            },
        )
        await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return {"action": action or {}, "state": await self._state(resolved_id)}

    async def set_checked(
        self,
        browser_id: int | str | None,
        ref: int | str,
        checked: bool = True,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await self._ensure_content_helper(page)
        action = await page.evaluate(
            "(args) => globalThis.__spaceBrowserPageContent__.setChecked(args.ref, args.checked)",
            {
                "ref": ref,
                "checked": bool(checked),
            },
        )
        await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return {"action": action or {}, "state": await self._state(resolved_id)}

    async def upload_file(
        self,
        browser_id: int | str | None,
        ref: int | str,
        path: str = "",
        paths: list[str] | None = None,
    ) -> dict[str, Any]:
        upload_paths = self._normalize_upload_paths(path=path, paths=paths)
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await self._ensure_content_helper(page)
        metadata = await page.evaluate(
            "(ref) => globalThis.__spaceBrowserPageContent__.fileInputFor(ref)",
            ref,
        )
        handle = None
        try:
            handle = await page.evaluate_handle(
                "(ref) => globalThis.__spaceBrowserPageContent__.fileInputElementFor(ref)",
                ref,
            )
            element = handle.as_element() if handle else None
            if element:
                await element.set_input_files(upload_paths)
            elif metadata and metadata.get("selector"):
                await page.set_input_files(metadata["selector"], upload_paths)
            else:
                raise ValueError(f"Browser ref {ref!r} does not resolve to a file input")
        finally:
            if handle:
                with contextlib.suppress(Exception):
                    await handle.dispose()
        await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return {
            "action": {
                "files": upload_paths,
                "input": metadata or {},
                "ref": ref,
            },
            "state": await self._state(resolved_id),
        }

    async def mouse(
        self,
        browser_id: int | str | None,
        event_type: str,
        x: float,
        y: float,
        button: str = "left",
        modifiers: list[str] | str | None = None,
    ) -> dict[str, Any]:
        event_type_lower = str(event_type or "click").lower()
        modifiers = self._normalize_modifiers(modifiers)
        if modifiers:
            if event_type_lower != "click":
                raise ValueError("modifiers are only valid for event_type='click'")
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        if event_type_lower == "move":
            await page.mouse.move(float(x), float(y))
        elif event_type_lower == "down":
            await page.mouse.down(button=button)
        elif event_type_lower == "up":
            await page.mouse.up(button=button)
        else:
            pressed: list[str] = []
            try:
                if modifiers:
                    for mod in modifiers:
                        await page.keyboard.down(mod)
                        pressed.append(mod)
                await page.mouse.click(float(x), float(y), button=button)
            finally:
                for mod in reversed(pressed):
                    with contextlib.suppress(Exception):
                        await page.keyboard.up(mod)
            await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return await self._state(resolved_id)

    async def wheel(
        self,
        browser_id: int | str | None,
        x: float,
        y: float,
        delta_x: float = 0,
        delta_y: float = 0,
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await page.mouse.move(float(x), float(y))
        await page.mouse.wheel(float(delta_x), float(delta_y))
        self._maybe_promote(resolved_id)
        return await self._state(resolved_id)

    async def keyboard(
        self,
        browser_id: int | str | None,
        *,
        key: str = "",
        text: str = "",
    ) -> dict[str, Any]:
        await self.ensure_started()
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        if text:
            await page.keyboard.type(str(text))
        elif key:
            await page.keyboard.press(str(key))
        await self._settle(page, short=True)
        self._maybe_promote(resolved_id)
        return await self._state(resolved_id)

    async def _insert_clipboard_text(self, page: Any, text: str) -> bool:
        if not text:
            return False
        insert_text = getattr(page.keyboard, "insert_text", None)
        if callable(insert_text):
            await insert_text(str(text))
        else:
            await page.keyboard.type(str(text))
        return True

    async def close(self, delete_profile: bool = False) -> None:
        self._closing = True
        for waiter in self._pending_popups:
            if not waiter.done():
                waiter.set_exception(RuntimeError("Browser runtime is closing."))
        self._pending_popups.clear()
        self._background_popup_pages.clear()
        await self._stop_all_screencasts()
        for browser_id in list(self.pages):
            try:
                await self.pages[browser_id].page.close()
            except Exception:
                pass
        self.pages.clear()
        if self.context:
            try:
                await self.context.close()
            except Exception as exc:
                PrintStyle.warning(f"Browser context close failed: {exc}")
            self.context = None
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as exc:
                PrintStyle.warning(f"Playwright stop failed: {exc}")
            self.playwright = None
        self.last_interacted_browser_id = None
        if delete_profile:
            shutil.rmtree(self.profile_dir, ignore_errors=True)

    def _on_context_closed(self) -> None:
        if self._closing or self.context is None:
            return
        PrintStyle.warning("Browser context closed unexpectedly; will restart on next use.")
        self._discard_context_state()

    async def _reference_action(
        self,
        helper_method: str,
        browser_id: int | str | None,
        reference_id: int | str,
        text: str | None = None,
    ) -> dict[str, Any]:
        resolved_id = self._resolve_browser_id(browser_id)
        page = self._page(resolved_id)
        await self._ensure_content_helper(page)
        if text is None:
            action = await page.evaluate(
                "(args) => globalThis.__spaceBrowserPageContent__[args.method](args.ref)",
                {"method": helper_method, "ref": reference_id},
            )
        else:
            action = await page.evaluate(
                "(args) => globalThis.__spaceBrowserPageContent__[args.method](args.ref, args.text)",
                {"method": helper_method, "ref": reference_id, "text": text},
            )
        await self._settle(page, short=False)
        self._maybe_promote(resolved_id)
        return {"action": action or {}, "state": await self._state(resolved_id)}

    async def _goto(self, page: Any, url: str) -> None:
        from playwright.async_api import Error as PlaywrightError
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except PlaywrightTimeoutError:
            PrintStyle.warning(f"Browser navigation timed out after DOM handoff: {url}")
        except PlaywrightError as exc:
            PrintStyle.warning(f"Browser navigation showed a native error page for {url}: {exc}")
        await self._settle(page)

    async def _settle(self, page: Any, short: bool = False) -> None:
        from playwright.async_api import Error as PlaywrightError
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        try:
            await page.wait_for_load_state(
                "domcontentloaded",
                timeout=1000 if short else 5000,
            )
        except (PlaywrightError, PlaywrightTimeoutError):
            pass
        await asyncio.sleep(0.1 if short else 0.35)

    async def _state(self, browser_id: int) -> dict[str, Any]:
        browser_page = self.pages.get(int(browser_id))
        if not browser_page:
            raise KeyError(f"Browser {browser_id} is not open.")
        page = browser_page.page
        try:
            title = await page.title()
        except Exception:
            title = ""
        try:
            history_length = await page.evaluate("() => globalThis.history?.length || 0")
        except Exception:
            history_length = 0
        return {
            "id": browser_page.id,
            "context_id": self.context_id,
            "currentUrl": page.url,
            "title": title,
            "canGoBack": bool(history_length and int(history_length) > 1),
            "canGoForward": False,
            "loading": False,
        }

    def _register_page_locked(self, page: Any) -> BrowserPage:
        existing = self._browser_id_for_page(page)
        if existing is not None:
            return self.pages[existing]
        browser_id = self.next_browser_id
        self.next_browser_id += 1
        browser_page = BrowserPage(id=browser_id, page=page)
        self.pages[browser_id] = browser_page

        def on_close() -> None:
            try:
                asyncio.create_task(self._unregister_page_async(browser_id))
            except RuntimeError:
                # No running loop (e.g., during shutdown). Best-effort sync pop.
                self.pages.pop(browser_id, None)

        page.on("close", on_close)
        return browser_page

    async def _register_page(self, page: Any) -> BrowserPage:
        lock = self._ensure_registry_lock()
        async with lock:
            return self._register_page_locked(page)

    async def _unregister_page_async(self, browser_id: int) -> None:
        try:
            lock = self._ensure_registry_lock()
            async with lock:
                self.pages.pop(browser_id, None)
                if self.last_interacted_browser_id == browser_id:
                    self.last_interacted_browser_id = next(iter(sorted(self.pages)), None)
                self._background_popup_pages.discard(browser_id)
        except Exception as exc:
            PrintStyle.warning(f"Page unregister failed: {exc}")

    def _on_new_page_sync(self, page: Any) -> None:
        if self._closing or self.context is None:
            return
        try:
            asyncio.create_task(self._on_new_page_async(page))
        except RuntimeError:
            return

    async def _on_new_page_async(self, page: Any) -> None:
        try:
            with contextlib.suppress(Exception):
                await page.wait_for_load_state("domcontentloaded", timeout=2000)
            if self._closing or page.is_closed():
                return
            lock = self._ensure_registry_lock()
            close_over_limit = False
            async with lock:
                if self._closing:
                    return
                if self._browser_id_for_page(page) is not None:
                    return
                if len(self.pages) >= self._max_open_tabs():
                    limit_error = self._tab_limit_error()
                    while self._pending_popups:
                        waiter = self._pending_popups.pop(0)
                        if not waiter.done():
                            waiter.set_exception(limit_error)
                            break
                    close_over_limit = True
                else:
                    browser_page = self._register_page_locked(page)
                    new_id = browser_page.id
                    while self._pending_popups:
                        waiter = self._pending_popups.pop(0)
                        if not waiter.done():
                            waiter.set_result(new_id)
                            break
                    if new_id not in self._background_popup_pages:
                        self.last_interacted_browser_id = new_id
                    else:
                        self._background_popup_pages.discard(new_id)
            if close_over_limit:
                with contextlib.suppress(Exception):
                    await page.close()
        except Exception as exc:
            PrintStyle.warning(f"Popup registration failed: {exc}")

    def _browser_id_for_page(self, page: Any) -> int | None:
        for browser_id, browser_page in self.pages.items():
            if browser_page.page == page:
                return browser_id
        return None

    def _resolve_browser_id(self, browser_id: int | str | None = None) -> int:
        if browser_id is None or str(browser_id).strip() == "":
            if self.last_interacted_browser_id in self.pages:
                return int(self.last_interacted_browser_id)
            if self.pages:
                return sorted(self.pages)[0]
            raise KeyError("No browser is open. Use action=open first.")
        value = str(browser_id).strip()
        if value.startswith("browser-"):
            value = value.split("-", 1)[1]
        resolved = int(value)
        if resolved not in self.pages:
            raise KeyError(f"Browser {resolved} is not open.")
        return resolved

    def _page(self, browser_id: int) -> Any:
        return self.pages[int(browser_id)].page

    async def _stop_screencasts_for_browser(self, browser_id: int) -> None:
        stream_ids = [
            stream_id
            for stream_id, screencast in self.screencasts.items()
            if screencast.browser_id == int(browser_id)
        ]
        for stream_id in stream_ids:
            await self.stop_screencast(stream_id)

    async def _stop_all_screencasts(self) -> None:
        for stream_id in list(self.screencasts):
            await self.stop_screencast(stream_id)

    async def _ensure_content_helper(self, page: Any) -> None:
        has_helper = await page.evaluate(
            "() => Boolean(globalThis.__spaceBrowserPageContent__?.ready?.())"
        )
        if has_helper:
            return
        if self._content_helper_source is None:
            self._content_helper_source = CONTENT_HELPER_PATH.read_text(encoding="utf-8")
        await page.evaluate(self._content_helper_source)

_runtimes: dict[str, BrowserRuntime] = {}
_runtime_lock = threading.RLock()


async def get_runtime(context_id: str, *, create: bool = True) -> BrowserRuntime | None:
    context_id = str(context_id or "").strip()
    if not context_id:
        raise ValueError("context_id is required")
    with _runtime_lock:
        runtime = _runtimes.get(context_id)
        if runtime is None and create:
            runtime = BrowserRuntime(context_id)
            _runtimes[context_id] = runtime
        return runtime


async def close_runtime(context_id: str, *, delete_profile: bool = True) -> None:
    context_id = str(context_id or "").strip()
    if not context_id:
        return
    with _runtime_lock:
        runtime = _runtimes.pop(context_id, None)
    if runtime:
        await runtime.close(delete_profile=delete_profile)


def close_runtime_sync(context_id: str, *, delete_profile: bool = True) -> None:
    task = DeferredTask(thread_name="BrowserCleanup")
    task.start_task(close_runtime, context_id, delete_profile=delete_profile)
    try:
        task.result_sync(timeout=30)
    finally:
        task.kill(terminate_thread=True)


async def close_all_runtimes(*, delete_profiles: bool = False) -> None:
    with _runtime_lock:
        runtimes = list(_runtimes.values())
        _runtimes.clear()
    for runtime in runtimes:
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
