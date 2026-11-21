import re
from pathlib import Path

import pytest


pytestmark = pytest.mark.anyio
HELPER = Path(__file__).resolve().parents[1] / 'plugins/_browser/assets/browser-dom-helper.js'
HTML = """<!doctype html><title>DOM RPC fixture</title>
<p id="secret">PRIVATE_ACCOUNT_DATA</p>
<form onsubmit="event.preventDefault(); document.body.dataset.submits = String(Number(document.body.dataset.submits || 0) + 1)">
  <input id="input" value="private@example.test">
  <button id="submit" type="submit">Submit</button>
</form>
<button id="click" onclick="document.body.dataset.clicks = String(Number(document.body.dataset.clicks || 0) + 1)">Click</button>
"""
STATE = """() => ({
    value: document.querySelector('#input').value,
    clicks: Number(document.body.dataset.clicks || 0),
    submits: Number(document.body.dataset.submits || 0)
})"""


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def browser_context():
    pytest.importorskip('patchright.async_api')
    from patchright.async_api import async_playwright

    async with async_playwright() as playwright:
        executable = playwright.chromium.executable_path
        if not Path(executable).is_file():
            pytest.skip('Patchright Chromium is not installed')
        browser = await playwright.chromium.launch(executable_path=executable, headless=True, args=['--no-sandbox'])
        try:
            context = await browser.new_context()
            await context.route('**/*', lambda route: route.fulfill(content_type='text/html', body=HTML))
            yield context
        finally:
            await browser.close()


async def add_frame(page, kind):
    await page.evaluate("""({kind, html}) => {
        const frame = document.createElement('iframe');
        frame.id = 'frame';
        if (kind === 'opaque') frame.sandbox = 'allow-scripts';
        if (kind === 'srcdoc' || kind === 'opaque') frame.srcdoc = html;
        else frame.src = kind === 'blank' ? 'about:blank' : `http://${kind}.test/`;
        document.body.append(frame);
    }""", {'kind': kind, 'html': HTML}, isolated_context=False)
    element = await page.locator('#frame').element_handle()
    frame = await element.content_frame()
    await frame.wait_for_load_state()
    if kind == 'blank':
        await frame.set_content(HTML)
    await frame.locator('#input').wait_for()
    return frame


async def node_ids(frame, isolated):
    snapshot = await frame.evaluate("""() => globalThis.__spaceBrowserDomHelper__.captureDocument({
        selectors: ['#input', '#click', '#submit']
    })""", isolated_context=isolated)
    return {selector: re.search(r'data-space-browser-node-id="([^"]+)"', html).group(1)
            for selector, html in snapshot['targets'].items()}


async def attack(victim, attacker, target, isolated):
    ids = await node_ids(victim, isolated)
    await victim.evaluate("""() => addEventListener('message', event => {
        if (event.data?.channel === 'rpc-test-barrier') {
            setTimeout(() => event.source.postMessage({channel: 'rpc-test-barrier'},
                event.origin === 'null' ? '*' : event.origin), 250);
        }
    })""", isolated_context=False)
    return await attacker.evaluate("""({targetName, ids}) => new Promise((resolve, reject) => {
        const target = {parent, child: frames[0], sibling: parent.frames[0], popup: globalThis.rpcPopup, opener}[targetName];
        const replies = [];
        const timer = setTimeout(() => reject(new Error('Message barrier was not delivered')), 3000);
        function receive(event) {
            if (event.data?.channel === 'a0.browser.dom_helper') replies.push(event.data);
            if (event.data?.channel === 'rpc-test-barrier') {
                clearTimeout(timer);
                removeEventListener('message', receive);
                resolve(replies);
            }
        }
        addEventListener('message', receive);
        for (const [type, payload] of [
            ['capture_document', {selectors: ['#secret', '#input']}],
            ['type_node', {nodeId: ids['#input'], value: 'attacker@example.test'}],
            ['click_node', {nodeId: ids['#click']}],
            ['submit_node', {nodeId: ids['#submit']}]
        ]) target.postMessage({channel: 'a0.browser.dom_helper', requestId: type, type, payload}, '*');
        target.postMessage({channel: 'rpc-test-barrier'}, '*');
    })""", {'targetName': target, 'ids': ids}, isolated_context=False)


@pytest.mark.parametrize('isolated', [False, True])
@pytest.mark.parametrize('relationship', ['child', 'parent', 'opener', 'popup', 'opaque'])
async def test_dom_rpc_rejects_cross_origin_reads_and_mutations(browser_context, relationship, isolated):
    page = await browser_context.new_page()
    parent_is_victim = relationship in {'child', 'popup', 'opaque'}
    await page.goto('http://victim.test/' if parent_is_victim else 'http://attacker.test/')
    if relationship in {'opener', 'popup'}:
        async with browser_context.expect_page() as popup:
            await page.evaluate("url => { globalThis.rpcPopup = window.open(url); }",
                                'http://attacker.test/' if parent_is_victim else 'http://victim.test/',
                                isolated_context=False)
        child = await popup.value
        await child.wait_for_load_state()
        await child.locator('#input').wait_for()
        target = 'opener' if parent_is_victim else 'popup'
    else:
        child = await add_frame(page, 'opaque' if relationship == 'opaque' else ('attacker' if parent_is_victim else 'victim'))
        target = 'parent' if parent_is_victim else 'child'
    victim, attacker = (page, child) if parent_is_victim else (child, page)
    await victim.evaluate(HELPER.read_text(), isolated_context=isolated)
    replies = await attack(victim, attacker, target, isolated)
    state = await victim.evaluate(STATE, isolated_context=False)
    assert (replies, state) == ([], {'value': 'private@example.test', 'clicks': 0, 'submits': 0})


@pytest.mark.parametrize('isolated', [False, True])
async def test_dom_rpc_rejects_distinct_opaque_origins(browser_context, isolated):
    page = await browser_context.new_page()
    await page.goto('http://victim.test/')
    victim = await add_frame(page, 'opaque')
    await page.locator('#frame').evaluate("frame => { frame.id = 'victim-frame'; }")
    attacker = await add_frame(page, 'opaque')
    for frame in (victim, attacker):
        assert await frame.evaluate('() => origin', isolated_context=False) == 'null'
    await victim.evaluate(HELPER.read_text(), isolated_context=isolated)
    assert await attack(victim, attacker, 'sibling', isolated) == []
    assert await victim.evaluate(STATE, isolated_context=False) == {'value': 'private@example.test', 'clicks': 0, 'submits': 0}


@pytest.mark.parametrize('kind', ['attacker', 'opaque'])
async def test_dom_rpc_does_not_send_requests_to_untrusted_frames(browser_context, kind):
    page = await browser_context.new_page()
    await page.goto('http://victim.test/')
    child = await add_frame(page, kind)
    await child.evaluate("""() => {
        document.querySelector('#secret').textContent = 'PRIVATE_CHILD_DATA';
        globalThis.requests = 0;
        addEventListener('message', event => {
            if (event.data?.channel === 'a0.browser.dom_helper') globalThis.requests++;
        });
    }""", isolated_context=False)
    for frame in (page, child):
        await frame.evaluate(HELPER.read_text(), isolated_context=True)
    snapshot = await page.evaluate("() => globalThis.__spaceBrowserDomHelper__.captureDocument({selectors: ['#frame']})",
                                   isolated_context=True)
    assert 'browser_dom_helper_frame_origin_unavailable' in snapshot['targets']['#frame']
    assert 'PRIVATE_CHILD_DATA' not in snapshot['targets']['#frame']
    assert await child.evaluate('() => globalThis.requests', isolated_context=False) == 0
    direct = await child.evaluate("() => globalThis.__spaceBrowserDomHelper__.captureDocument({selectors: ['#secret']})",
                                  isolated_context=True)
    assert 'PRIVATE_CHILD_DATA' in direct['targets']['#secret']
    ids = await node_ids(child, True)
    await child.evaluate("id => globalThis.__spaceBrowserDomHelper__.typeNode([], id, 'allowed@example.test')",
                         ids['#input'], isolated_context=True)
    assert await child.evaluate(STATE, isolated_context=False) == {'value': 'allowed@example.test', 'clicks': 0, 'submits': 0}


@pytest.mark.parametrize('kind', ['victim', 'srcdoc', 'blank'])
async def test_dom_rpc_preserves_same_origin_frame_actions(browser_context, kind):
    page = await browser_context.new_page()
    await page.goto('http://victim.test/')
    child = await add_frame(page, kind)
    for frame in (page, child):
        await frame.evaluate(HELPER.read_text(), isolated_context=True)
    snapshot = await page.evaluate("() => globalThis.__spaceBrowserDomHelper__.captureDocument()", isolated_context=True)
    assert 'PRIVATE_ACCOUNT_DATA' in snapshot['html']
    child_id = await child.evaluate('() => globalThis.__spaceBrowserDomHelper__.frameId', isolated_context=True)
    ids = await node_ids(child, True)
    await page.evaluate("""async ({chain, ids}) => {
        const helper = globalThis.__spaceBrowserDomHelper__;
        await helper.typeNode(chain, ids['#input'], 'allowed@example.test');
        await helper.clickNode(chain, ids['#click']);
        await helper.submitNode(chain, ids['#submit']);
    }""", {'chain': [snapshot['frameId'], child_id], 'ids': ids}, isolated_context=True)
    assert await child.evaluate(STATE, isolated_context=False) == {'value': 'allowed@example.test', 'clicks': 1, 'submits': 1}


@pytest.mark.parametrize('forgery', ['source', 'type'])
async def test_dom_rpc_binds_responses_to_requested_frame_and_operation(browser_context, forgery):
    page = await browser_context.new_page()
    await page.goto('http://victim.test/')
    child = await add_frame(page, 'victim')
    await page.evaluate("""() => {
        const sibling = document.createElement('iframe');
        sibling.src = 'http://victim.test/sibling';
        document.body.append(sibling);
    }""", isolated_context=False)
    sibling = page.frames[-1]
    await sibling.wait_for_load_state()
    await sibling.evaluate("""() => addEventListener('message', event => {
        if (event.data?.channel === 'rpc-test-forge') parent.postMessage(event.data.reply, origin);
    })""", isolated_context=False)
    await child.evaluate("""forgery => addEventListener('message', event => {
        if (event.data?.channel !== 'a0.browser.dom_helper') return;
        const reply = {channel: event.data.channel, requestId: event.data.requestId,
            type: 'capture_document_result', ok: true,
            payload: {ok: true, frameId: 'fixture', html: 'FORGED_SNAPSHOT'}};
        if (forgery === 'source') parent.frames[1].postMessage({channel: 'rpc-test-forge', reply}, origin);
        else event.source.postMessage({...reply, type: 'click_node_result'}, origin);
        setTimeout(() => event.source.postMessage({...reply,
            payload: {...reply.payload, html: 'VALID_SNAPSHOT'}}, origin), 50);
    })""", forgery, isolated_context=False)
    await page.evaluate(HELPER.read_text(), isolated_context=True)
    snapshot = await page.evaluate("() => globalThis.__spaceBrowserDomHelper__.captureDocument({selectors: ['#frame']})",
                                   isolated_context=True)
    assert 'VALID_SNAPSHOT' in snapshot['targets']['#frame']
    assert 'FORGED_SNAPSHOT' not in snapshot['targets']['#frame']


async def test_dom_rpc_upgrade_requires_reload(browser_context):
    from patchright.async_api import Error
    from plugins._browser.helpers.runtime import _BrowserRuntimeCore

    page = await browser_context.new_page()
    await page.goto('http://victim.test/')
    await page.evaluate("""() => {
        globalThis.__spaceBrowserDomHelper__ = {version: '1', captureDocument() {}};
        globalThis.legacyRequests = 0;
        addEventListener('message', event => {
            if (event.data?.channel === 'a0.browser.dom_helper') globalThis.legacyRequests++;
        });
    }""", isolated_context=True)
    core = _BrowserRuntimeCore('dom-rpc-upgrade-test')
    with pytest.raises(RuntimeError, match='Reload the browser page'):
        await core._ensure_dom_helper(page)
    with pytest.raises(Error, match='Reload the browser page'):
        await page.evaluate(HELPER.read_text(), isolated_context=True)
    assert await page.evaluate('() => globalThis.__spaceBrowserDomHelper__.version', isolated_context=True) == '1'
    await page.reload()
    child = await add_frame(page, 'attacker')
    await core._ensure_dom_helper(page)
    assert await page.evaluate('() => globalThis.__spaceBrowserDomHelper__.version', isolated_context=True) == '2'
    assert await attack(page, child, 'parent', True) == []
    assert await page.evaluate('() => typeof globalThis.legacyRequests', isolated_context=True) == 'undefined'
    assert await page.evaluate(STATE, isolated_context=False) == {'value': 'private@example.test', 'clicks': 0, 'submits': 0}
