"""Exercise the production DevTools pipe using a disposable Chromium profile."""
import asyncio
from collections import deque
import base64
import struct
import signal
import sys
from urllib.parse import quote

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from browser_fixtures import chromium
from plugins._browser.sandbox import cdp
from plugins._browser.sandbox.cdp import CDPError


@pytest.mark.asyncio
async def test_chromium_pipe_tabs_input_frames_upload_screenshot_and_history(tmp_path):
    html = """<script>window.initialWebdriver = navigator.webdriver;</script>
              <input autofocus><input type=file id=file><button ondblclick="this.textContent='twice'">click</button>
              <div style="height:2400px"></div><iframe srcdoc="<title>inner</title>"></iframe>"""
    url = "data:text/html," + quote(html)
    async with chromium(tmp_path) as context:
        page, = context.pages
        assert not (tmp_path / "DevToolsActivePort").exists()
        await page.goto(url, wait_until="load")
        assert await page.evaluate("[window.initialWebdriver, navigator.webdriver]") == [False, False]
        assert await page.evaluate("(() => { window.invocations = (window.invocations || 0) + 1; })();") is None
        assert await page.evaluate("(async () => window.invocations)") == 1
        assert await page.evaluate("async function () { return {count: window.invocations} }") == {"count": 1}
        assert await page.evaluate("function count() {return window.invocations}; count()") == 1
        assert await page.evaluate("() => confirm('discard?')") is False
        await page.keyboard.type("Original")
        await page.keyboard.press("Control+a")
        await page.keyboard.type("New+")
        assert await page.evaluate("document.querySelector('input').value") == "New+"
        await page.evaluate("document.addEventListener('keydown', e => window.received = [e.key, e.code, e.location])")
        await page.keyboard.press("ShiftRight")
        assert await page.evaluate("window.received") == ["Shift", "ShiftRight", 2]
        await page.keyboard.press("NumpadAdd")
        assert await page.evaluate("window.received") == ["+", "NumpadAdd", 3]
        point = await page.evaluate("() => {const r=document.querySelector('button').getBoundingClientRect();"
                                    "return [r.x+r.width/2,r.y+r.height/2]}")
        await page.mouse.dblclick(*point)
        assert await page.evaluate("document.querySelector('button').textContent") == "twice"
        frames = await page.document_frames()
        assert [await frame.evaluate("document.title") for frame in frames] == ["", "inner"]
        await page.evaluate("globalThis.__spaceBrowserPageContent__ = {fileInputElementFor(){return null;}}",
                            isolated_context=True)
        assert await page.evaluate("typeof globalThis.__spaceBrowserPageContent__") == "undefined"
        await page.upload_files(1, "#file", [{"name": "sample.bin", "mimeType": "application/octet-stream",
                                             "buffer": bytes(range(256))}])
        assert await page.evaluate("""async () => {
            const file=document.querySelector('#file').files[0];
            return [file.name, file.size, new Uint8Array(await file.arrayBuffer())[255]];
        }""") == ["sample.bin", 256, 255]
        image = await page.screenshot(type="png", full_page=True)
        assert image[:8] == b"\x89PNG\r\n\x1a\n"
        assert struct.unpack(">I", image[20:24])[0] >= 2400
        popup = await page.open_tab()
        assert await popup.evaluate("window.opener === null")
        assert len(context.pages) == 2
        await popup.goto("data:text/html,<title>first</title>")
        await popup.goto("data:text/html,<title>second</title>")
        await popup.go_back(wait_until="domcontentloaded", timeout=5000)
        assert await popup.evaluate("document.title") == "first"
        await popup.go_forward(wait_until="load", timeout=5000)
        assert await popup.evaluate("document.title") == "second"
        await popup.reload(wait_until="commit", timeout=5000)
        await popup.close()
        other = await context.new_page(new_window=True)
        a, b = await asyncio.gather(page.send("Browser.getWindowForTarget"), other.send("Browser.getWindowForTarget"))
        assert a["windowId"] != b["windowId"]


@pytest.mark.asyncio
async def test_evaluate_preserves_bigints_and_runs_function_once(tmp_path):
    async with chromium(tmp_path) as context:
        page, = context.pages
        assert await page.evaluate("-9007199254740993n") == -9007199254740993
        result = await page.evaluate("""() => {
            window.calls = (window.calls || 0) + 1;
            const item = {id: 9007199254740993n};
            return [item, item, {count: 42n}];
        }""")
        assert result == [{"id": 9007199254740993}, {"id": 9007199254740993}, {"count": 42}]
        assert await page.evaluate("window.calls") == 1
        assert await page.evaluate("() => null") is None
        assert await page.evaluate("new Uint8Array([12, 34])") == {"0": 12, "1": 34}


@pytest.mark.asyncio
async def test_history_traverses_subframe_entries_without_moving_the_main_document(tmp_path):
    main = tmp_path / "main.html"
    main.write_text('<iframe src="one.html" onload="window.childLoads = (window.childLoads || 0) + 1"></iframe>')
    (tmp_path / "one.html").write_text('<title>one</title><a href="two.html">Next</a>')
    (tmp_path / "two.html").write_text('<title>two</title>')
    async with chromium(tmp_path / "profile") as context:
        page, = context.pages
        await page.goto(main.as_uri(), wait_until="load")
        _, child = await page.document_frames()
        await child.evaluate("document.querySelector('a').click()")
        async with asyncio.timeout(3):
            while await page.evaluate("window.childLoads") < 2:
                await asyncio.sleep(.025)
        await page.go_back(wait_until="domcontentloaded", timeout=3000)
        assert await child.evaluate("document.title") == "one"
        await page.go_forward(wait_until="domcontentloaded", timeout=3000)
        assert await child.evaluate("document.title") == "two"
        assert page.url == main.as_uri()
        await page.evaluate("location.hash = 'part'")
        await page.go_back(wait_until="commit", timeout=3000)
        assert page.url == main.as_uri()
        await page.go_forward(wait_until="domcontentloaded", timeout=3000)
        assert page.url == main.as_uri() + "#part"


@pytest.mark.asyncio
async def test_history_reports_removal_of_the_traversing_frame(tmp_path):
    main = tmp_path / "main.html"
    main.write_text("""<iframe srcdoc="<script>if (parent.removeOnBack) frameElement.remove()</script>"></iframe>""")
    async with chromium(tmp_path / "profile") as context:
        page, = context.pages
        await page.goto(main.as_uri(), wait_until="load")
        await page.evaluate("""() => new Promise(resolve => {
            const frame = document.querySelector('iframe');
            frame.onload = () => resolve();
            frame.contentWindow.location.href = 'about:blank#two';
        })""")
        await page.evaluate("window.removeOnBack = true")
        with pytest.raises(CDPError, match="frame was removed"):
            await page.go_back(wait_until="domcontentloaded", timeout=3000)
        assert await page.evaluate("document.querySelector('iframe') === null")


@pytest.mark.asyncio
@pytest.mark.parametrize("forward_ready", ["commit", "domcontentloaded"])
async def test_history_follows_frame_process_swaps_and_releases_observers(tmp_path, forward_ready):
    parsing, release = asyncio.Event(), asyncio.Event()
    release.set()

    async def parser(request):
        parsing.set()
        await release.wait()
        return web.Response(text="", content_type="text/javascript", headers={"Cache-Control": "no-store"})

    async def document(request):
        body = '<iframe src="/one"></iframe>' if request.path == "/" else '<script src="/parser.js"></script>'
        return web.Response(text=body, content_type="text/html")

    app = web.Application()
    app.router.add_get("/parser.js", parser)
    app.router.add_get("/{path:.*}", document)
    async with TestServer(app) as server, chromium(tmp_path / "profile") as context:
        page, = context.pages
        await page.goto(str(server.make_url("/")), wait_until="load")
        await page.evaluate("""url => new Promise(resolve => {
            const frame = document.querySelector('iframe');
            frame.onload = () => resolve();
            frame.contentWindow.location.href = url;
        })""", str(server.make_url("/two").with_host("localhost")))
        sessions = set(context.sessions)
        for traverse, ready, cancel in ((page.go_back, "domcontentloaded", False),
                                        (page.go_forward, forward_ready, False),
                                        (page.go_back, "domcontentloaded", True)):
            parsing.clear()
            release.clear()
            await page.evaluate("""() => {
                window.loaded = new Promise(resolve => document.querySelector('iframe').onload = () => resolve());
            }""")
            traversal = asyncio.create_task(traverse(wait_until=ready, timeout=3000))
            try:
                await asyncio.wait_for(parsing.wait(), 2)
                if ready == "commit":
                    await traversal
                elif cancel:
                    traversal.cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await traversal
                else:
                    finished, _ = await asyncio.wait([traversal], timeout=.1)
                    assert not finished
                    release.set()
                    await traversal
            finally:
                release.set()
                await asyncio.gather(traversal, return_exceptions=True)
            await asyncio.wait_for(page.evaluate("window.loaded"), 2)
            assert set(context.sessions) == sessions


@pytest.mark.asyncio
async def test_chromium_exit_fails_waiters_and_reaps_owned_process(tmp_path):
    async with chromium(tmp_path) as context:
        page, = context.pages
        await page.session()
        pending = asyncio.create_task(page.evaluate("new Promise(() => {})"))
        await page.evaluate("1")  # The preceding command has reached the same session.
        exit_codes = []
        context.on("close", lambda: exit_codes.append(context.process.returncode))
        await context.command("Browser.close")
        with pytest.raises(CDPError):
            await asyncio.wait_for(pending, 3)
        await asyncio.wait_for(asyncio.shield(context.reader), 5)
        assert context.closed and context.process.returncode is not None and not context.pending
        assert exit_codes == [context.process.returncode]


@pytest.mark.asyncio
async def test_close_reaps_browser_that_keeps_its_pipe_open(monkeypatch):
    monkeypatch.setattr(cdp, "_SHUTDOWN_GRACE_SECONDS", .1)
    child = await asyncio.create_subprocess_exec(
        sys.executable, "-c", """
import signal, sys
signal.signal(signal.SIGTERM, signal.SIG_IGN)
while sys.stdin.buffer.read(1) != bytes(1):
    pass
sys.stdout.buffer.write(b'{"id":1,"result":{}}' + bytes(1))
sys.stdout.buffer.flush()
signal.pause()
""", stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
    )
    context = cdp.CDPContext(child, {})
    closed = []
    context.on("close", lambda: closed.append(child.returncode))
    try:
        await asyncio.wait_for(context.close(), 3)
        assert closed == [-signal.SIGKILL]
        assert context.closed and context.reader.done()
    finally:
        if child.returncode is None:
            child.kill()
        await child.wait()


@pytest.mark.asyncio
async def test_authenticated_proxy_uses_only_configured_endpoint(tmp_path):
    requests = []
    async def serve(reader, writer):
        try:
            headers = await reader.readuntil(b"\r\n\r\n")
            requested = headers.partition(b"\r\n")[0]
            if requested != b"GET http://fixture.invalid/ HTTP/1.1":
                status, body = b"403 Forbidden\r\n", b""
            elif b"\r\nProxy-Authorization: Basic " + base64.b64encode(b"fixture:pass") + b"\r\n" in headers:
                status, body = b"200 OK\r\n", b"<title>accepted</title>"
                requests.append("authorized")
            else:
                status, body = b'407 Proxy Authentication Required\r\nProxy-Authenticate: Basic realm="fixture"\r\n', b""
                requests.append("challenge")
            writer.write(b"HTTP/1.1 " + status + b"Content-Type: text/html\r\nCache-Control: no-store\r\nConnection: close\r\nContent-Length: "
                         + str(len(body)).encode() + b"\r\n\r\n" + body)
            await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            writer.close()

    async with await asyncio.start_server(serve, "127.0.0.1", 0) as server:
        address = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        proxy = {"server": address, "username": "fixture", "password": "pass"}
        for restore in (False, True):
            requests.clear()
            async with chromium(tmp_path, proxy, restore_session=restore) as context:
                page, = context.pages
                if restore:
                    await page.wait_for_load_state("load", timeout=8000)
                else:
                    await page.goto("http://fixture.invalid/", timeout=8000)
                assert await page.evaluate("document.title") == "accepted"
                assert requests == ["challenge", "authorized"]


@pytest.mark.asyncio
async def test_proxy_auth_challenges_deny_mismatch_and_repeat():
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    address = "http://proxy.test:1080"
    context = SimpleNamespace(proxy={"server": address, "username": "name", "password": "secret"},
                              _auth_attempts=deque(), command=AsyncMock())
    async def challenge(source, origin):
        await cdp.CDPContext._auth(context, {"requestId": "abc", "authChallenge": {"source": source, "origin": origin}})
        return context.command.await_args.args[1]["authChallengeResponse"]
    assert await challenge("Server", address) == {"response": "Default"}
    assert await challenge("Proxy", "http://different.test:1080") == {"response": "CancelAuth"}
    assert await challenge("Proxy", address) == {"response":"ProvideCredentials", "username":"name", "password":"secret"}
    assert await challenge("Proxy", address) == {"response": "CancelAuth"}
