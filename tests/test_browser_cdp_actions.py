"""Exercise form and pointer actions using references from a real document capture."""
import asyncio
import re
from pathlib import Path

import pytest

from browser_fixtures import native_page
from helpers import files
from plugins._browser.helpers.sandbox import BrowserConnection
from plugins._browser.sandbox.cdp import CDPError
from plugins._browser.sandbox.runtime import _BrowserRuntimeCore


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.mark.anyio
async def test_agent_cdp_commands_sessions_events_and_chat_cleanup(native_page):
    core = _BrowserRuntimeCore("first")
    core.context = native_page.context
    tab = (await core._register_page(native_page)).id
    version = await core.cdp(cdp_method="Browser.getVersion")
    assert version["result"]["protocolVersion"]
    inspector = await core.cdp(tab, "Runtime.enable")
    sid = inspector["session_id"]
    assert sid != version["session_id"]
    batch = await core.multi([
        {"action": "cdp", "browser_id": tab, "cdp_method": "Page.getLayoutMetrics"},
        {"action": "cdp", "session_id": sid, "cdp_method": "Runtime.evaluate",
         "params": {"expression": "console.info('agent-cdp'); 6 * 7", "returnByValue": True}},
    ])
    assert batch[0]["result"]["result"]["cssLayoutViewport"]["clientWidth"] > 0
    assert batch[1]["result"]["result"]["result"]["value"] == 42
    token = core.request_context_id.set("second")
    assert (await core.cdp())["events"] == []
    with pytest.raises(ValueError, match="Unknown CDP session"):
        await core.cdp(cdp_method="Runtime.enable", session_id=sid)
    second = await core.cdp(tab, "DOM.getDocument", {"depth": 0})
    core.request_context_id.reset(token)
    events = (await core.cdp())["events"]
    assert any(e["method"] == "Runtime.consoleAPICalled" and e["sessionId"] == sid
               and e["params"]["args"][0]["value"] == "agent-cdp" for e in events)
    assert not (await core.cdp())["events"]
    nested = await core.cdp(cdp_method="Target.attachToTarget", params={
        "targetId": native_page.target_id, "flatten": True,
    })
    child = nested["result"]["sessionId"]
    assert (await core.cdp(cdp_method="Page.getFrameTree", session_id=child))["result"]["frameTree"]
    with pytest.raises(CDPError, match="wasn't found"):
        await core.cdp(tab, "MissingDomain.unknownCommand")
    await core.release_cdp()
    assert sid not in core.context.raw_sessions and child not in core.context.raw_sessions
    assert second["session_id"] in core.context.raw_sessions
    assert (await core.state(tab))["title"] == "Browser fixture"


def test_agent_cdp_buffer_reports_lost_events(monkeypatch):
    from plugins._browser.sandbox.raw_cdp import RawCDPClient

    client = RawCDPClient(None)
    monkeypatch.setattr(client, "MAX_BYTES", 8)
    for sequence, size in enumerate([4, 4, 1, 9]):
        client.receive({"method": "Page.loadEventFired", "params": {"n": sequence}}, size)
    read = client.drain()
    assert [event["params"]["n"] for event in read["events"]] == [1, 2]
    assert read["dropped"] == 2 and read["remaining"] == client.size == 0
    assert client.drain()["dropped"] == 0


@pytest.mark.anyio
async def test_captured_controls_resolve_for_native_browser_actions(native_page):
    page = native_page
    await page.evaluate("""() => {
        document.body.innerHTML = `
            <select id="size"><option>Small</option><option>Large</option></select>
            <input id="enabled" type="checkbox"><input id="locked" type="checkbox" disabled>
            <button id="probe">Probe</button>`;
        probe.onmouseenter = event => probe.dataset.hover = String(event.isTrusted);
        probe.onclick = event => probe.dataset.shift = String(event.isTrusted && event.shiftKey);
    }""")
    core = _BrowserRuntimeCore('forms')
    core.context = page.context
    tab = (await core._register_page(page)).id
    capture = await core.content(tab, {'selectors': ['#size', '#enabled', '#locked', '#probe']})
    refs = {selector: re.search(r' (\d+)\]', text)[1] for selector, text in capture.items()}
    await core.select_option(tab, refs['#size'], value='Large')
    await core.set_checked(tab, refs['#enabled'])
    with pytest.raises(CDPError, match='disabled'):
        await core.set_checked(tab, refs['#locked'])
    await core.hover(tab, refs['#probe'])
    await core.click(tab, refs['#probe'], modifiers=['Shift'])
    assert await page.evaluate('[size.value, enabled.checked, locked.checked, probe.dataset.hover, probe.dataset.shift]') == [
        'Large', True, False, 'true', 'true',
    ]


@pytest.mark.anyio
async def test_guest_screenshot_bytes_match_pathless_format_and_explicit_suffix(native_page, tmp_path, monkeypatch):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    core = _BrowserRuntimeCore("formats")
    core.context = native_page.context
    tab = (await core._register_page(native_page)).id
    capture = BrowserConnection("formats")
    calls = [
        {"action": "screenshot", "browser_id": tab, "image_format": "png"},
        {"action": "screenshot", "browser_id": tab},
        {"action": "screenshot", "browser_id": tab, "path": str(tmp_path / "explicit.jpeg"), "image_format": "png"},
        {"action": "screenshot", "browser_id": tab, "path": str(tmp_path / "explicit.PNG"), "image_format": "jpeg"},
    ]
    results = await core.multi(calls)
    for call, item, extension in zip(calls, results, [".png", ".jpg", ".jpeg", ".png"], strict=True):
        assert item["ok"], item
        result = capture.save_screenshot(item["result"], call.get("path", ""))
        saved = Path(result["path"])
        assert saved.suffix.lower() == extension
        assert result["mime"] == ("image/png" if extension == ".png" else "image/jpeg")
        assert saved.read_bytes().startswith(b"\x89PNG\r\n\x1a\n" if extension == ".png" else b"\xff\xd8\xff")


@pytest.mark.anyio
@pytest.mark.parametrize("method", ["click", "submit", "type_submit"])
async def test_reference_navigation_reports_replaced_document_once(native_page, method):
    page = native_page
    core = _BrowserRuntimeCore("navigation")
    core.context = page.context
    tab = (await core._register_page(page)).id
    await page.evaluate("""() => {
        document.body.innerHTML = '<form><input name="q"><button id="go">Send</button></form>';
        document.querySelector('form').onsubmit = event => {
            event.preventDefault();
            sessionStorage.setItem('submits', String(Number(sessionStorage.getItem('submits')) + 1));
            location.reload();
        };
    }""")
    selector = "input" if method == "type_submit" else "#go"
    capture = await core.content(tab, {"selectors": [selector]})
    ref = re.search(r' (\d+)\]', capture[selector])[1]
    args = (tab, ref, "fixture") if method == "type_submit" else (tab, ref)
    previous = page.loader_id
    result = await getattr(core, method)(*args)
    assert page.loader_id != previous and result["state"]["currentUrl"] == page.url
    assert result["action"]["ref"] == ref and "navigated" in result["action"]["warning"]
    assert await page.evaluate("sessionStorage.getItem('submits')") == "1"


@pytest.mark.anyio
@pytest.mark.parametrize("interrupt", ["no navigation", "close tab", "close after commit"])
async def test_reference_navigation_error_requires_a_new_live_document(native_page, monkeypatch, interrupt):
    core = _BrowserRuntimeCore("navigation")
    core.context = native_page.context
    tab = (await core._register_page(native_page)).id
    await core.content(tab)
    with pytest.raises(CDPError, match="reference"):
        await core.click(tab, 9999)

    evaluate = native_page.evaluate
    calls = 0

    async def interrupted(script, *args, **kwargs):
        nonlocal calls
        if "args.method" in script:
            calls += 1
            if interrupt == "close tab":
                await native_page.close()
            elif interrupt == "close after commit":
                await native_page.reload(wait_until="commit")
            raise CDPError("Inspected target navigated or closed")
        if interrupt == "close after commit" and "canGoBack: history.length" in script:
            await native_page.close()
            await asyncio.wait_for(native_page._wait(native_page.is_closed), 2)
        return await evaluate(script, *args, **kwargs)

    monkeypatch.setattr(native_page, "evaluate", interrupted)
    message = "tab closed" if interrupt == "close after commit" else "Inspected target navigated or closed"
    with pytest.raises(CDPError, match=message):
        await core.click(tab, 1)
    assert calls == 1
