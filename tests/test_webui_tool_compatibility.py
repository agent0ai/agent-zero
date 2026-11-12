"""Render real modules without a backend, sidebar mount, or user state."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import pytest

playwright = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def page():
    def serve(route):
        path = urlparse(route.request.url).path
        if path == "/":
            route.fulfill(content_type="text/html", body='''<!doctype html>
                <script>globalThis.runtimeInfo = {webuiExtensions: {js: {}, html: {}}};</script>
                <div id="chat-history"></div>''')
            return
        asset = ROOT / (path.lstrip("/") if path.startswith(("/plugins/", "/extensions/")) else "webui/" + path.lstrip("/"))
        if asset.is_file():
            route.fulfill(path=asset, content_type=mimetypes.guess_type(asset)[0])
        else:
            route.abort()
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except playwright.Error as error:
            if "Executable doesn't exist" in str(error):
                pytest.skip("An installed Playwright Chromium is required.")
            raise
        page = browser.new_page()
        page.route("**/*", serve)
        page.goto("http://compat.test/")
        yield page
        browser.close()


def test_first_snapshot_retains_tasks_and_selection_before_sidebar_mount(page):
    result = page.evaluate('''async () => {
        const ui = await import('/index.js');
        const {getStore} = await import('/js/AlpineStore.js');
        const registeredBeforeSnapshot = !!getStore('tasks');
        ui.setContext('saved-task');
        const snapshot = {context:'saved-task', contexts:[{id:'ordinary-chat', created_at:1}],
            tasks:[{id:'saved-task', created_at:2}], logs:[], log_version:0, log_guid:'fixture'};
        await ui.applySnapshot(snapshot);
        await ui.applySnapshot({...snapshot, contexts:null, tasks:null});
        const tasks = getStore('tasks');
        const chats = getStore('chats');
        return {registeredBeforeSnapshot, ids:tasks?.tasks.map(t => t.id),
            context:ui.getContext(), selected:tasks?.selected, selectedChat:chats.selectedContext?.id};
    }''')
    assert result == {"registeredBeforeSnapshot": True, "ids": ["saved-task"], "context": "saved-task", "selected": "saved-task", "selectedChat": "saved-task"}


@pytest.mark.parametrize("attachments", [False, True])
@pytest.mark.parametrize("during_render", [False, True])
def test_welcome_send_survives_first_snapshot_until_backend_log_arrives(page, attachments, during_render):
    page.route("**/hold-first-render.js", lambda route: route.fulfill(
        content_type="text/javascript", body='''export default async () => {
            const hold = globalThis.holdFirstRender;
            if (hold) {
                globalThis.holdFirstRender = null;
                globalThis.renderStarted();
                await hold;
            }
        };'''))
    result = page.evaluate('''async ({attachments, duringRender}) => {
        const ui = await import('/index.js');
        const {getStore} = await import('/js/AlpineStore.js');
        const input = getStore('chatInput');
        const originalFetch = globalThis.fetch;
        let completeSend, messageId, requestStarted;
        const sending = new Promise(resolve => { requestStarted = resolve; });
        let releaseRender;
        const rendering = new Promise(resolve => { globalThis.renderStarted = resolve; });
        if (duringRender) {
            globalThis.holdFirstRender = new Promise(resolve => { releaseRender = resolve; });
            runtimeInfo.webuiExtensions.js.get_process_step_types = ['/hold-first-render.js'];
        }
        globalThis.fetch = (url, options) => {
            if (url === '/api/csrf_token') return Promise.resolve(Response.json({ok:true, token:'fixture'}));
            if (url === '/api/chat_create') return Promise.resolve(Response.json({ok:true, ctxid:'new-chat'}));
            if (url === '/api/message_async') {
                messageId = options.body instanceof FormData
                    ? options.body.get('message_id') : JSON.parse(options.body).message_id;
                requestStarted();
                return new Promise(resolve => { completeSend = resolve; });
            }
            return originalFetch(url, options);
        };
        input.message = 'First Welcome prompt';
        if (attachments) getStore('chatAttachments').getAttachmentsForSending = () => [
            {file:new File(['fixture'], 'fixture.txt')}];
        const send = input.sendMessage();
        await (duringRender ? rendering : sending);
        const snapshot = {context:'new-chat', contexts:[{id:'new-chat'}], tasks:[],
            logs:[{no:0, id:'greeting', type:'response', content:'Hello!'}],
            log_version:1, log_guid:'fixture'};
        const userRows = () => document.querySelectorAll('#chat-history .message-user').length;
        const applying = ui.applySnapshot(snapshot);
        if (duringRender) releaseRender();
        await applying;
        await sending;
        const whileSending = userRows();
        const order = [...document.querySelectorAll('#chat-history .message-container')]
            .map(element => element.id);
        completeSend(Response.json({context:'new-chat'}));
        await send;
        const confirmed = {no:1, id:messageId, type:'user', content:'Server confirmed prompt', kvps:{}};
        await ui.applySnapshot({...snapshot, logs:[confirmed], log_version:2});
        const afterConfirmation = userRows();
        const confirmedText = document.querySelector('#chat-history .message-user .message-text')?.textContent;
        await ui.applySnapshot({...snapshot, log_version:3});
        return {whileSending, greetingFirst:order[0] === 'message-greeting',
            userLast:order.at(-1) === `message-${messageId}`, afterConfirmation,
            confirmedText, afterRemoval:userRows()};
    }''', {"attachments": attachments, "duringRender": during_render})
    assert result == {"whileSending": 1, "greetingFirst": True, "userLast": True,
        "afterConfirmation": 1, "confirmedText": "Server confirmed prompt",
        "afterRemoval": 0}


@pytest.mark.parametrize("tool_name,code", [("skills_tool", "SKL"), ("vision_load", "EYE"), ("search_engine", "SRC"), ("memory_load", "MEM"), ("memory_save", "MEM"), ("memory_delete", "MEM"), ("memory_forget", "MEM")])
def test_saved_tool_logs_keep_their_specialized_renderer(page, tool_name, code):
    result = page.evaluate('''async ({tool_name}) => {
        runtimeInfo.webuiExtensions.js.get_tool_message_handler = [
            '/extensions/webui/get_tool_message_handler/skills-handler.js',
            '/extensions/webui/get_tool_message_handler/vision-handler.js',
            '/plugins/_search_engine/extensions/webui/get_tool_message_handler/search-engine-handler.js',
            '/plugins/_memory/extensions/webui/get_tool_message_handler/memory-handler.js'];
        const {drawMessageTool} = await import('/js/messages.js');
        const log = {id:'legacy', no:0, type:'tool', heading:'Saved tool call', content:'Saved result',
            kvps:{_tool_name:tool_name, query:'original query'}};
        const {element} = await drawMessageTool(log);
        document.getElementById('chat-history').append(element);
        return {badge:element.getAttribute('data-step-code'),
            text:element.textContent, originalTool:log.kvps._tool_name};
    }''', {"tool_name": tool_name})
    assert result["badge"] == code
    assert "Saved tool call" in result["text"]
    assert result["originalTool"] == tool_name
