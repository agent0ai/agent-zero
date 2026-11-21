"""Exercise form and pointer actions using references from a real document capture."""
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
