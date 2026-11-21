import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from browser_fixtures import chromium, native_page
from plugins._browser.sandbox.cdp import CDPError, CDPPage, CDPSession


pytestmark = pytest.mark.anyio
HELPER = (Path(__file__).resolve().parents[1] / 'plugins/_browser/assets/browser-dom-helper.js').read_text()
INSTALL_HELPER = '() => {' + HELPER + '}'
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
async def browser_context(tmp_path):
    # Serve both .test origins on loopback. Each document retains its own browser origin.
    async def serve(reader, writer):
        try:
            headers = await reader.readuntil(b"\r\n\r\n")
            fixture = headers.startswith((b"GET http://victim.test/", b"GET http://attacker.test/"))
            body = HTML.encode() if fixture else b""
            status = b"200 OK" if fixture else b"404 Not Found"
            writer.write(b"HTTP/1.1 " + status + b"\r\nContent-Type: text/html\r\nConnection: close\r\n"
                         + f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
            await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            writer.close()

    async with await asyncio.start_server(serve, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        async with chromium(tmp_path, proxy={"server": f"http://127.0.0.1:{port}"}) as context:
            yield context


@dataclass
class FixtureFrame:
    session: CDPSession
    main_world: int
    isolated_world: int

    async def evaluate(self, function, *args, isolated_context):
        result = await self.session.send("Runtime.callFunctionOn", {
            "functionDeclaration": function,
            "executionContextId": self.isolated_world if isolated_context else self.main_world,
            "arguments": [{"value": arg} for arg in args],
            "awaitPromise": True, "returnByValue": True,
        })
        return CDPPage._value(result)


async def fixture_frame(page, selector):
    document = await page.send("DOM.getDocument")
    element = await page.send("DOM.querySelector", {"nodeId": document["root"]["nodeId"], "selector": selector})
    node = await page.send("DOM.describeNode", element)
    frame_id = node["node"]["frameId"]

    # Site isolation can move this fixture into its own renderer target.
    local_ids = {frame.frame_id for frame in await page.document_frames()}
    target = page if frame_id in local_ids else CDPPage(page.context, frame_id)
    session = await page.context.new_cdp_session(target)
    main_world = asyncio.get_running_loop().create_future()

    def remember(event):
        context = event["context"]
        info = context.get("auxData", {})
        if info.get("isDefault") and info.get("frameId") == frame_id and not main_world.done():
            main_world.set_result(context["id"])

    session.on("Runtime.executionContextCreated", remember)
    await session.send("Runtime.enable")
    isolated = await session.send("Page.createIsolatedWorld", {"frameId": frame_id, "worldName": "agent-zero-browser"})
    main_id = await asyncio.wait_for(main_world, timeout=5)
    assert main_id != isolated["executionContextId"]
    return FixtureFrame(session, main_id, isolated["executionContextId"])


async def add_frame(page, kind):
    await page.evaluate("""({kind, html}) => new Promise(resolve => {
        const frame = document.createElement('iframe');
        frame.id = 'frame';
        if (kind === 'opaque') frame.sandbox = 'allow-scripts';
        if (kind === 'srcdoc' || kind === 'opaque') frame.srcdoc = html;
        else frame.src = kind === 'blank' ? 'about:blank' : `http://${kind}.test/`;
        frame.onload = () => {
            if (kind === 'blank') frame.contentDocument.body.innerHTML = html;
            resolve();
        };
        document.body.append(frame);
    })""", {'kind': kind, 'html': HTML}, isolated_context=False)
    return await fixture_frame(page, '#frame')


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
        url = 'http://attacker.test/' if parent_is_victim else 'http://victim.test/'
        await page.evaluate("url => { globalThis.rpcPopup = window.open(url); }", url)
        child = await browser_context.wait_for_page(lambda tab: tab.url == url and tab is not page)
        await child.wait_for_load_state()
        target = 'opener' if parent_is_victim else 'popup'
    else:
        child = await add_frame(page, 'opaque' if relationship == 'opaque' else ('attacker' if parent_is_victim else 'victim'))
        target = 'parent' if parent_is_victim else 'child'
    victim, attacker = (page, child) if parent_is_victim else (child, page)
    await victim.evaluate(INSTALL_HELPER, isolated_context=isolated)
    replies = await attack(victim, attacker, target, isolated)
    state = await victim.evaluate(STATE, isolated_context=False)
    assert (replies, state) == ([], {'value': 'private@example.test', 'clicks': 0, 'submits': 0})


@pytest.mark.parametrize('isolated', [False, True])
async def test_dom_rpc_rejects_distinct_opaque_origins(browser_context, isolated):
    page = await browser_context.new_page()
    await page.goto('http://victim.test/')
    victim = await add_frame(page, 'opaque')
    await page.evaluate("document.querySelector('#frame').id = 'victim-frame'")
    attacker = await add_frame(page, 'opaque')
    for frame in (victim, attacker):
        assert await frame.evaluate('() => origin', isolated_context=False) == 'null'
    await victim.evaluate(INSTALL_HELPER, isolated_context=isolated)
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
        await frame.evaluate(INSTALL_HELPER, isolated_context=True)
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
        await frame.evaluate(INSTALL_HELPER, isolated_context=True)
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
    await page.evaluate("""() => new Promise(resolve => {
        const sibling = document.createElement('iframe');
        sibling.id = 'sibling';
        sibling.onload = () => resolve();
        sibling.src = 'http://victim.test/sibling';
        document.body.append(sibling);
    })""", isolated_context=False)
    sibling = await fixture_frame(page, '#sibling')
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
    await page.evaluate(INSTALL_HELPER, isolated_context=True)
    snapshot = await page.evaluate("() => globalThis.__spaceBrowserDomHelper__.captureDocument({selectors: ['#frame']})",
                                   isolated_context=True)
    assert 'VALID_SNAPSHOT' in snapshot['targets']['#frame']
    assert 'FORGED_SNAPSHOT' not in snapshot['targets']['#frame']


async def test_dom_rpc_upgrade_requires_reload(browser_context):
    from plugins._browser.sandbox.runtime import _BrowserRuntimeCore

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
        await core._ensure_dom_helper(await page.document_frames())
    with pytest.raises(CDPError, match='Reload the browser page'):
        await page.evaluate(INSTALL_HELPER, isolated_context=True)
    assert await page.evaluate('() => globalThis.__spaceBrowserDomHelper__.version', isolated_context=True) == '1'
    await page.reload()
    child = await add_frame(page, 'attacker')
    await core._ensure_dom_helper(await page.document_frames())
    assert await page.evaluate('() => globalThis.__spaceBrowserDomHelper__.version', isolated_context=True) == '2'
    assert await attack(page, child, 'parent', True) == []
    assert await page.evaluate('() => typeof globalThis.legacyRequests', isolated_context=True) == 'undefined'
    assert await page.evaluate(STATE, isolated_context=False) == {'value': 'private@example.test', 'clicks': 0, 'submits': 0}


@pytest.mark.parametrize('nested', [False, True])
async def test_file_upload_resolves_captured_helper_reference(native_page, nested):
    from plugins._browser.sandbox.runtime import _BrowserRuntimeCore, BrowserPage
    page = native_page
    if nested:
        await page.evaluate("""() => {
            const frame = document.createElement("iframe");
            frame.srcdoc = "<body></body>";
            document.body.append(frame);
            return new Promise(resolve => frame.onload = resolve);
        }""")
    target = (await page.document_frames())[-1]
    await target.evaluate("() => { const input=document.createElement('input'); input.type='file'; input.id='fixture-file'; document.body.append(input); }", isolated_context=True)
    core = _BrowserRuntimeCore('fixture')
    core.pages[1] = BrowserPage(1, page)
    async def ready(): pass
    core.ensure_started = ready
    core._state = lambda _: asyncio.sleep(0, result={'id':1})
    capture = await core.content(1)
    ref = re.search(r'\[input file (\d+)\]', capture['document']).group(1)
    core.request_uploads.set({json.dumps(['fixture.txt', None]): {'paths':['fixture.txt'], 'files':[
        {'name':'fixture.txt','mimeType':'text/plain','buffer':'c2VsZWN0ZWQ='}]}})
    await core.upload_file(1, ref, path='fixture.txt')
    assert await target.evaluate("() => document.querySelector('#fixture-file').files[0].text()") == 'selected'
