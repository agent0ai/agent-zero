"""Exercise form and pointer actions using references from a real document capture."""
import re

import pytest

from browser_fixtures import native_page
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
