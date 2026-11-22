"""Chromium's private DevTools pipe, page targets and document sessions."""
from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import os
import re
import uuid
from collections import OrderedDict, deque
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from plugins._browser.sandbox.cdp_input import Keyboard, Mouse


_SHUTDOWN_GRACE_SECONDS = 5


class CDPError(RuntimeError):
    pass


class CDPSession:
    def __init__(self, context: CDPContext, session_id: str):
        self.context = context
        self.id = session_id
        self.handlers = {}

    def on(self, method, callback):
        self.handlers[method] = callback

    async def send(self, method: str, params: dict | None = None, *, timeout: float = 30) -> dict:
        return await self.context.command(method, params, session_id=self.id, timeout=timeout)

    async def detach(self):
        if self.id in self.context.sessions:
            await self.context.command("Target.detachFromTarget", {"sessionId": self.id})
            self.context.sessions.pop(self.id, None)


class CDPContext:
    def __init__(self, process: asyncio.subprocess.Process, proxy: dict[str, str]):
        self.process = process
        self.proxy = proxy
        self._auth_attempts = deque(maxlen=256)
        self.sessions: dict[str, CDPSession] = {}
        self.targets: dict[str, CDPPage] = {}
        self.handlers = {}
        self.pending: dict[int, tuple[str | None, asyncio.Future]] = {}
        self.jobs = set()
        self.changed = asyncio.Event()
        self.closed = False
        self.closing = False
        self.next_id = 0
        self.reader = asyncio.create_task(self._read())

    @classmethod
    async def launch(cls, executable: str | os.PathLike, args: list[str], *,
                     env: dict[str, str] | None = None, proxy: dict[str, str] | None = None) -> CDPContext:
        flags = ["--remote-debugging-pipe"]
        if proxy:
            server = proxy["server"]
            address = urlsplit(server if "://" in server else "http://" + server)
            if (not address.hostname or address.username is not None or address.password is not None
                    or address.path not in ("", "/") or address.query or address.fragment):
                raise ValueError("Enter a proxy address and keep credentials in the separate proxy fields")
            if address.scheme.startswith("socks") and (proxy.get("username") or proxy.get("password")):
                raise ValueError("Chromium supports authenticated HTTP proxies and unauthenticated SOCKS proxies")
            flags.append(f"--proxy-server={server}")
            if proxy.get("bypass"):
                flags.append("--proxy-bypass-list=" + proxy["bypass"].replace(",", ";"))
        # Chromium uses descriptors 3/4 for CDP. Its normal output belongs on stderr.
        process = await asyncio.create_subprocess_exec(
            "/bin/sh", "-c", 'exec "$@" 3<&0 4>&1 </dev/null >&2',
            "a0-chromium", os.fspath(executable), *flags, *args,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            limit=128 * 1024 * 1024, env=env,
        )
        context = cls(process, proxy or {})
        try:
            if proxy and (proxy.get("username") or proxy.get("password")):
                # Restored tabs can request credentials before a page session exists.
                await context.command("Fetch.enable", {"handleAuthRequests": True})
            await context.command("Target.setDiscoverTargets", {"discover": True})
            # Discovery can precede native session restoration or creation of the first tab.
            await context.wait_for_page(lambda page: True)
            return context
        except BaseException:
            await context.close()
            raise

    @property
    def pages(self) -> list[CDPPage]:
        return list(self.targets.values())

    def on(self, event, callback):
        self.handlers[event] = callback

    def _notify(self):
        self.changed.set()
        self.changed = asyncio.Event()

    async def wait_for_page(self, predicate: Callable[[CDPPage], bool]) -> CDPPage:
        async with asyncio.timeout(30):
            while not self.closed:
                for page in self.targets.values():
                    if predicate(page):
                        return page
                await self.changed.wait()
        raise CDPError("Chromium closed while opening the tab")

    async def command(self, method: str, params: dict | None = None, *, session_id: str | None = None,
                      timeout: float = 30) -> dict:
        if self.closed:
            raise CDPError("Chromium's DevTools pipe is closed")
        self.next_id += 1
        ident = self.next_id
        message = {"id": ident, "method": method, "params": params or {}}
        if session_id:
            message["sessionId"] = session_id
        future = asyncio.get_running_loop().create_future()
        self.pending[ident] = (session_id, future)
        try:
            async with asyncio.timeout(timeout):
                self.process.stdin.write(json.dumps(message, separators=(",", ":")).encode() + b"\0")
                await self.process.stdin.drain()
                return await future
        finally:
            self.pending.pop(ident, None)

    async def _read(self):
        try:
            while True:
                data = await self.process.stdout.readuntil(b"\0")
                message = json.loads(data[:-1])
                if "id" in message:
                    pending = self.pending.get(message["id"])
                    if pending and not pending[1].done():
                        if "error" in message:
                            pending[1].set_exception(CDPError(message["error"]["message"]))
                        else:
                            pending[1].set_result(message.get("result", {}))
                    continue
                self._event(message)
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        except (ValueError, KeyError, asyncio.LimitOverrunError):
            logging.getLogger(__name__).exception("Invalid Chromium pipe message")
        finally:
            self.closed = True
            self._fail_requests()
            self.sessions.clear()
            for page in self.targets.values():
                page._closed()
            self.targets.clear()
            self._notify()
            self.process.stdin.close()
            # EOF also owns cleanup when the user closes the native browser.
            try:
                await asyncio.wait_for(self.process.wait(), _SHUTDOWN_GRACE_SECONDS)
            except TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    self.process.kill()
                await self.process.wait()
            # The runtime may reuse this profile as soon as it receives the close event.
            if "close" in self.handlers:
                self.handlers["close"]()

    def _fail_requests(self, session_id=None):
        for owner, future in self.pending.values():
            if (session_id is None or owner == session_id) and not future.done():
                future.set_exception(CDPError("Chromium closed the DevTools session"))

    def _event(self, message):
        event, params = message["method"], message.get("params", {})
        if event in ("Target.targetCreated", "Target.targetInfoChanged"):
            info = params["targetInfo"]
            if info["type"] != "page" or info.get("subtype"):
                return
            target_id = info["targetId"]
            page = self.targets.get(target_id)
            if page is None:
                page = self.targets[target_id] = CDPPage(self, target_id)
            created = page.info is None
            page.info = info
            self._notify()
            if created:
                if "page" in self.handlers:
                    self.handlers["page"](page)
        elif event == "Fetch.requestPaused" and not message.get("sessionId"):
            self._background(self.command("Fetch.continueRequest", {"requestId": params["requestId"]}))
        elif event == "Fetch.authRequired" and not message.get("sessionId"):
            self._background(self._auth(params))
        elif event == "Target.targetDestroyed":
            page = self.targets.pop(params["targetId"], None)
            if page:
                page._closed()
            self._notify()
        elif event == "Target.detachedFromTarget":
            session_id = params["sessionId"]
            self.sessions.pop(session_id, None)
            self._fail_requests(session_id)
        else:
            session = self.sessions.get(message.get("sessionId"))
            if session and event in session.handlers:
                session.handlers[event](params)

    async def _auth(self, params):
        request_id = params["requestId"]
        challenge = params["authChallenge"]
        proxy = self.proxy
        answer = {"response": "Default"}
        if challenge.get("source") == "Proxy":
            answer = {"response": "CancelAuth"}
            server = proxy["server"]
            expected = urlsplit(server if "://" in server else "http://" + server)
            origin = urlsplit(challenge["origin"])
            def endpoint(parsed):
                return parsed.scheme, parsed.hostname, parsed.port or {"http": 80, "https": 443}.get(parsed.scheme)
            if endpoint(origin) == endpoint(expected) and request_id not in self._auth_attempts:
                self._auth_attempts.append(request_id)
                answer = {"response": "ProvideCredentials", "username": proxy.get("username", ""),
                          "password": proxy.get("password", "")}
        await self.command("Fetch.continueWithAuth", {"requestId": request_id, "authChallengeResponse": answer})

    def _background(self, coro):
        task = asyncio.create_task(coro)
        self.jobs.add(task)
        def done(finished):
            self.jobs.discard(finished)
            if not finished.cancelled() and finished.exception() and not self.closed and not self.closing:
                logging.getLogger(__name__).warning("Chromium session event failed: %s", finished.exception())
        task.add_done_callback(done)

    async def new_cdp_session(self, page: CDPPage) -> CDPSession:
        result = await self.command("Target.attachToTarget", {"targetId": page.target_id, "flatten": True})
        return self._register_session(result["sessionId"])

    def _register_session(self, session_id: str) -> CDPSession:
        session = CDPSession(self, session_id)
        self.sessions[session.id] = session
        return session

    async def new_page(self, *, new_window: bool = False) -> CDPPage:
        result = await self.command("Target.createTarget", {"url": "about:blank", "newWindow": new_window})
        return await self.wait_for_page(lambda page: page.target_id == result["targetId"])

    async def close(self) -> None:
        self.closing = True
        try:
            if not self.closed:
                await self.command("Browser.close", timeout=4)
                await asyncio.wait_for(asyncio.shield(self.reader), _SHUTDOWN_GRACE_SECONDS)
        except (CDPError, TimeoutError, ConnectionError):
            pass
        finally:
            self.process.stdin.close()
            if not self.closed:
                with contextlib.suppress(ProcessLookupError):
                    self.process.terminate()
                try:
                    await asyncio.wait_for(asyncio.shield(self.reader), _SHUTDOWN_GRACE_SECONDS)
                except TimeoutError:
                    with contextlib.suppress(ProcessLookupError):
                        self.process.kill()
                    if not self.closed:
                        self.reader.cancel()
            await asyncio.gather(self.reader, return_exceptions=True)
            for task in tuple(self.jobs):
                task.cancel()
            await asyncio.gather(*self.jobs, return_exceptions=True)


_UNSET = object()
_READY_EVENTS = {"domcontentloaded": "DOMContentLoaded", "load": "load", "networkidle": "networkIdle"}


class CDPFrame:
    def __init__(self, page: CDPPage, frame_id: str):
        self.page = page
        self.frame_id = frame_id

    async def evaluate(self, script: str, arg: Any = _UNSET, *, isolated_context: bool = True):
        return await self.page._evaluate(script, arg, isolated_context, self.frame_id)


class CDPPage:
    def __init__(self, context: CDPContext, target_id: str):
        self.context = context
        self.target_id = target_id
        self.info = None
        self._session = None
        self._attach_lock = asyncio.Lock()
        self._on_close = None
        self._frame_id = None
        self.loader_id: str | None = None
        self._revision = 0
        self._lifecycle = OrderedDict()
        self._changed = asyncio.Event()
        self.keyboard = Keyboard(self)
        self.mouse = Mouse(self)

    @property
    def url(self) -> str:
        return self.info.get("url") or "about:blank"

    async def opener(self) -> CDPPage | None:
        return self.context.targets.get(self.info.get("openerId"))

    def is_closed(self) -> bool:
        return self.target_id not in self.context.targets or self.context.closed

    def on(self, event, callback):
        if event == "close":
            self._on_close = callback

    def _closed(self):
        self._changed.set()
        if self._on_close:
            self._on_close()

    async def session(self) -> CDPSession:
        async with self._attach_lock:
            if self._session and self._session.id in self.context.sessions:
                return self._session
            session = await self.context.new_cdp_session(self)
            try:
                session.on("Page.frameNavigated", self._navigated)
                session.on("Page.navigatedWithinDocument", self._within_document)
                session.on("Page.lifecycleEvent", self._lifecycle_event)
                session.on("Page.javascriptDialogOpening", lambda p: self.context._background(
                    session.send("Page.handleJavaScriptDialog", {"accept": p["type"] == "beforeunload"})))
                await session.send("Page.enable")
                await session.send("Runtime.enable")
                tree = await session.send("Page.getFrameTree")
                frame = tree["frameTree"]["frame"]
                self._frame_id, self.loader_id = frame["id"], frame.get("loaderId")
                await session.send("Page.setLifecycleEventsEnabled", {"enabled": True})
            except BaseException:
                with contextlib.suppress(CDPError, ConnectionError):
                    await session.detach()
                raise
            self._session = session
            return session

    async def send(self, method: str, params: dict | None = None, *, timeout: float = 30) -> dict:
        session = await self.session()
        return await session.send(method, params, timeout=timeout)

    def _notify(self):
        self._changed.set()
        self._changed = asyncio.Event()

    def _navigated(self, params):
        frame = params["frame"]
        if "parentId" not in frame:
            self._frame_id, self.loader_id = frame["id"], frame.get("loaderId")
            self.info["url"] = frame["url"] + frame.get("urlFragment", "")
            self._revision += 1
            if params.get("type") == "BackForwardCacheRestore":
                self._lifecycle.setdefault(self.loader_id, set()).update(_READY_EVENTS.values())
            self._notify()

    def _within_document(self, params):
        if params["frameId"] == self._frame_id:
            self.info["url"] = params["url"]
            self._revision += 1
            self._notify()

    def _lifecycle_event(self, params):
        if params["frameId"] == self._frame_id:
            self._lifecycle.setdefault(params["loaderId"], set()).add(params["name"])
            if len(self._lifecycle) > 8:
                self._lifecycle.popitem(last=False)
            self._notify()

    async def _wait(self, condition):
        while not condition():
            if self.is_closed():
                raise CDPError("The tab closed during navigation")
            await self._changed.wait()

    async def wait_for_document_change(self, previous_loader: str | None) -> bool:
        if not previous_loader:
            return False
        try:
            # A lost evaluation can arrive just before the main frame's commit event.
            async with asyncio.timeout(1):
                await self._wait(lambda: self.loader_id and self.loader_id != previous_loader)
        except (CDPError, TimeoutError):
            return False
        return not self.is_closed()

    async def _ready(self, wait_until):
        if wait_until == "commit":
            return
        if wait_until not in _READY_EVENTS:
            raise ValueError(f"Unknown Chromium navigation readiness: {wait_until}")
        await self._wait(lambda: _READY_EVENTS[wait_until] in self._lifecycle.get(self.loader_id, ()))

    async def wait_for_load_state(self, state="load", timeout=30000):
        async with asyncio.timeout(timeout / 1000):
            await self.session()
            await self._ready(state)

    async def goto(self, url, *, wait_until="domcontentloaded", timeout=30000):
        async with asyncio.timeout(timeout / 1000):
            result = await self.send("Page.navigate", {"url": url})
            if result.get("errorText"):
                raise CDPError(result["errorText"])
            if loader := result.get("loaderId"):
                await self._wait(lambda: self.loader_id == loader)
            await self._ready(wait_until)

    async def reload(self, *, wait_until="domcontentloaded", timeout=30000):
        async with asyncio.timeout(timeout / 1000):
            session = await self.session()
            previous = self._revision
            await session.send("Page.reload")
            await self._wait(lambda: self._revision != previous)
            await self._ready(wait_until)

    async def _history(self, offset, wait_until, timeout):
        async with asyncio.timeout(timeout / 1000):
            history = await self.send("Page.getNavigationHistory")
            index = history["currentIndex"] + offset
            if not 0 <= index < len(history["entries"]):
                return
            if wait_until != "commit" and wait_until not in _READY_EVENTS:
                raise ValueError(f"Unknown Chromium navigation readiness: {wait_until}")
            await self._wait_for_history_entry(history["entries"][index]["id"], wait_until)

    async def _wait_for_history_entry(self, entry_id, wait_until):
        events = asyncio.Queue()
        children = []

        def attached(params):
            child = self.context._register_session(params["sessionId"])
            children.append(child)
            events.put_nowait(("Target.attachedToTarget", child))

        async def watch(session):
            session.on("Target.attachedToTarget", attached)
            for method in ("Page.frameStartedNavigating", "Page.frameNavigated", "Page.frameDetached",
                           "Page.navigatedWithinDocument", "Page.lifecycleEvent"):
                session.on(method, lambda params, event=method: events.put_nowait((event, params)))
            await session.send("Page.enable")
            await session.send("Page.setLifecycleEventsEnabled", {"enabled": True})
            await session.send("Target.setAutoAttach", {
                "autoAttach": True, "waitForDebuggerOnStart": False, "flatten": True,
                "filter": [{"type": "iframe"}, {"exclude": True}],
            })

        attach = asyncio.create_task(self.context.new_cdp_session(self))
        try:
            observer = await asyncio.shield(attach)
        except asyncio.CancelledError:
            # Chromium can already own the session before we receive its ID.
            async def discard_observer():
                session = await attach
                await session.detach()
            self.context._background(discard_observer())
            raise
        try:
            await watch(observer)
            navigating = False
            frame_id = loader_id = None
            while True:
                # Chromium reports existing iframe targets before acknowledging auto-attach.
                if not navigating and events.empty():
                    await observer.send("Page.navigateToHistoryEntry", {"entryId": entry_id})
                    navigating = True
                event, params = await events.get()
                if event == "Target.attachedToTarget":
                    child = params
                    try:
                        await watch(child)
                    except CDPError:
                        if child.id in self.context.sessions:
                            raise
                elif not navigating:
                    continue
                elif event == "Page.frameStartedNavigating" and params["navigationType"].startswith("history"):
                    frame_id, loader_id = params["frameId"], params.get("loaderId")
                elif event == "Page.frameDetached" and params["frameId"] == frame_id and params["reason"] == "remove":
                    raise CDPError("The frame was removed during history navigation")
                elif event == "Page.navigatedWithinDocument" and params["frameId"] == frame_id:
                    return
                elif event == "Page.frameNavigated" and params["frame"]["id"] == frame_id:
                    if wait_until == "commit" or params.get("type") == "BackForwardCacheRestore":
                        return
                    loader_id = params["frame"]["loaderId"]
                elif (event == "Page.lifecycleEvent" and params["frameId"] == frame_id
                      and params["loaderId"] == loader_id and params["name"] == _READY_EVENTS.get(wait_until, "commit")):
                    return
        finally:
            # Chromium detaches the observer's entire subtree with the parent session.
            try:
                await observer.detach()
            finally:
                for child in children:
                    self.context.sessions.pop(child.id, None)

    async def go_back(self, *, wait_until, timeout):
        await self._history(-1, wait_until, timeout)

    async def go_forward(self, *, wait_until, timeout):
        await self._history(1, wait_until, timeout)

    async def bring_to_front(self):
        await self.context.command("Target.activateTarget", {"targetId": self.target_id})

    async def open_tab(self) -> CDPPage:
        marker = "about:blank#a0-" + uuid.uuid4().hex
        await self.evaluate("(url) => { window.open(url, '_blank'); }", marker, isolated_context=True)
        page = await self.context.wait_for_page(lambda p: p.url == marker)
        await page.evaluate("window.opener = null; history.replaceState(null, '', 'about:blank')", isolated_context=False)
        return page

    async def close(self, *, run_before_unload: bool = False) -> None:
        result = await self.context.command("Target.closeTarget", {"targetId": self.target_id})
        if not result.get("success"):
            raise CDPError("Chromium could not close the tab")

    async def document_frames(self) -> list[CDPFrame]:
        tree = await self.send("Page.getFrameTree")
        frames = []
        def collect(node):
            frames.append(CDPFrame(self, node["frame"]["id"]))
            for child in node.get("childFrames", []):
                collect(child)
        collect(tree["frameTree"])
        return frames

    async def _evaluate(self, script, arg, isolated, frame_id=None):
        session = await self.session()
        params = {"awaitPromise": True, "returnByValue": True, "userGesture": True}
        if isolated:
            world = await session.send("Page.createIsolatedWorld", {
                "frameId": frame_id or self._frame_id, "worldName": "agent-zero-browser"})
            params["contextId"] = world["executionContextId"]
        elif frame_id and frame_id != self._frame_id:
            raise ValueError("Only the main document supports page-world evaluation")
        source = script.strip()
        if arg is not _UNSET:
            params["expression"] = f"({source.rstrip(';')})({json.dumps(arg, ensure_ascii=True)})"
            return self._value(await session.send("Runtime.evaluate", params, timeout=65))

        # Anonymous function declarations need expression syntax. A script containing
        # subsequent statements must still execute as written.
        if re.match(r"^(?:async\s+)?function\b", source):
            expression = "(" + source.rstrip(";") + ")"
            compiled = await session.send("Runtime.compileScript", {
                "expression": expression, "sourceURL": "", "persistScript": False})
            if "exceptionDetails" not in compiled:
                source = expression
        group = uuid.uuid4().hex
        serialization = {"serializationOptions": {"serialization": "deep"}, "objectGroup": group}
        params.pop("returnByValue")
        result = self._remote(await session.send("Runtime.evaluate", {
            **params, **serialization, "expression": source}, timeout=65))
        if "objectId" not in result:
            return self._json_value(result["deepSerializedValue"], {})
        try:
            if result["type"] == "function":
                result = self._remote(await session.send("Runtime.callFunctionOn", {
                    **serialization, "objectId": result["objectId"], "functionDeclaration": "function(){return this()}",
                    "awaitPromise": True, "userGesture": True,
                }, timeout=65))
            try:
                return self._json_value(result["deepSerializedValue"], {})
            except ValueError:
                # Keep Chromium's existing by-value behavior for native objects such as typed arrays.
                return self._value(await session.send("Runtime.callFunctionOn", {
                    "objectId": result["objectId"], "functionDeclaration": "function(){return this}", "returnByValue": True,
                }))
        finally:
            with contextlib.suppress(CDPError, ConnectionError):
                await session.send("Runtime.releaseObjectGroup", {"objectGroup": group})

    @classmethod
    def _json_value(cls, node, references):
        kind, value = node["type"], node.get("value")
        if kind == "bigint":
            return int(value)
        if kind in ("null", "undefined", "string", "boolean", "number"):
            if kind == "number" and isinstance(value, str):
                return -0.0 if value == "-0" else None
            return value
        reference = node.get("weakLocalObjectReference")
        if reference is not None and reference in references:
            return references[reference]
        if kind == "array" and value is not None:
            result = [cls._json_value(item, references) for item in value]
        elif kind == "object" and value is not None:
            result = {key: cls._json_value(item, references) for key, item in value if item["type"] != "undefined"}
        else:
            raise ValueError("Not a JSON value")
        if reference is not None:
            references[reference] = result
        return result

    @staticmethod
    def _remote(response):
        if error := response.get("exceptionDetails"):
            raise CDPError(error.get("exception", {}).get("description") or error["text"])
        return response["result"]

    @classmethod
    def _value(cls, response):
        result = cls._remote(response)
        if result["type"] == "bigint":
            return int(result["unserializableValue"].removesuffix("n"))
        return result.get("value")

    async def evaluate(self, script: str, arg: Any = _UNSET, *, isolated_context: bool = False):
        return await self._evaluate(script, arg, isolated_context)

    async def screenshot(self, *, type: str = "jpeg", quality: int = 80, full_page: bool = False) -> bytes:
        params = {"format": type}
        if type == "jpeg":
            params["quality"] = quality
        if full_page:
            metrics = await self.send("Page.getLayoutMetrics")
            params.update(clip={**metrics["cssContentSize"], "scale": 1}, captureBeyondViewport=True)
        response = await self.send("Page.captureScreenshot", params, timeout=60)
        return base64.b64decode(response["data"])

    async def set_viewport_size(self, viewport):
        await self.send("Emulation.setDeviceMetricsOverride", {**viewport, "deviceScaleFactor": 1, "mobile": False})

    async def click_selector(self, selector, modifiers):
        point = await self.evaluate("""selector => {
            const el = document.querySelector(selector);
            if (!el) throw Error('Target element is missing');
            el.scrollIntoView({block:'center',inline:'center'});
            const r = el.getBoundingClientRect();
            if (!r.width || !r.height) throw Error('Target element has no bounds');
            return [r.x+r.width/2,r.y+r.height/2];
        }""", selector, isolated_context=True)
        pressed = []
        try:
            for key in modifiers:
                await self.keyboard.down(key)
                pressed.append(key)
            await self.mouse.click(*point)
        finally:
            for key in reversed(pressed):
                await self.keyboard.up(key)

    async def upload_files(self, ref: int | str, selector: str | None, files: list[dict]) -> None:
        payload = [{"name": f["name"], "type": f["mimeType"], "data": base64.b64encode(f["buffer"]).decode()}
                   for f in files]
        await self.evaluate("""({ref, selector, files}) => {
            const input = globalThis.__spaceBrowserPageContent__.fileInputElementFor(ref)
                || (selector && document.querySelector(selector));
            if (!input || input.tagName !== 'INPUT' || input.type !== 'file') throw Error('Expected a file input');
            if (input.webkitdirectory || (!input.multiple && files.length > 1)) throw Error('Files do not match input');
            const transfer = new DataTransfer();
            for (const f of files) {
                const bytes = Uint8Array.from(atob(f.data), c => c.charCodeAt(0));
                transfer.items.add(new File([bytes], f.name, {type: f.type}));
            }
            input.files = transfer.files;
            input.dispatchEvent(new Event('input', {bubbles:true, composed:true}));
            input.dispatchEvent(new Event('change', {bubbles:true}));
        }""", {"ref": ref, "selector": selector, "files": payload}, isolated_context=True)
