"""Extension handles must never enter the incumbent container viewer lane."""
import shutil
import subprocess
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_extension_log_projection_hides_input_without_mutating_tool_arguments(monkeypatch):
    from helpers import tool
    from plugins._browser.tools import browser

    config = {"runtime_backend": "host_required", "host_browser_selection": "extension:bridge-1"}
    monkeypatch.setattr(browser, "get_browser_config", lambda **kwargs: config)
    args = {"action": "type", "text": "synthetic private text", "_browser_backend": "forged"}
    agent = SimpleNamespace(agent_name="Agent Zero", context=SimpleNamespace(log=SimpleNamespace(log=lambda **kwargs: kwargs)))
    owner = browser.Browser(agent=agent, name="browser", method=None, args=args, message="", loop_data=None)
    projected = owner.get_log_object()["kvps"]
    assert projected["text"] == "[Input text withheld]" and projected["_browser_backend"] == "chrome_extension"
    assert args["text"] == "synthetic private text" and args["_browser_backend"] == "forged"
    # Exercise the actual base pre-execution console/extension-output path.
    output = []
    async def observe(_hook, _agent, ctx):
        output.append(ctx["content"])
    monkeypatch.setattr(tool, "PrintStyle", lambda **kwargs: SimpleNamespace(print=lambda *args: None, stream=lambda *args: None))
    monkeypatch.setattr(tool, "call_extensions_async", observe)
    asyncio.run(owner.before_execution())
    assert "synthetic private text" not in output and "[Input text withheld]" in output
    config["runtime_backend"] = "container"
    projected = owner.get_log_object()["kvps"]
    assert "_browser_backend" not in projected and projected["text"] == args["text"]


@pytest.mark.skipif(not shutil.which("node"), reason="Node required")
def test_extension_results_cannot_select_or_preview_container_tabs():
    root = Path(__file__).resolve().parents[1]
    script = r'''
import fs from 'node:fs';
import assert from 'node:assert/strict';
const root=process.argv[2]+'/plugins/_browser/extensions/webui/';
const source=fs.readFileSync(root+'get_tool_message_handler/browser-tool-handler.js','utf8');
const extract=(text,name)=>text.match(new RegExp('function '+name+'\\([^]*?\\n}'))[0];
const names=['browserIdFromResult','isExtensionBrowserTarget','buildBrowserCanvasPayload','shouldRenderBrowserScreenshotKvp','shouldSyncOpenBrowserCanvas'];
const code=names.map(name=>extract(source,name)).join('\n');
const probe=new Function('result','kvps', `
const browserSnapshotMeta=()=>({}),currentBrowserContextId=()=> 'context-1';
const normalizeBrowserAction=kvps=>kvps.action,NO_SCREENSHOT_ACTIONS=new Set();
const isBrowserCanvasAlreadyOpen=()=>true,isFreshToolMessage=()=>true,FOCUS_ACTIONS=new Set(['navigate']);
${code}
return [buildBrowserCanvasPayload(result,kvps),shouldRenderBrowserScreenshotKvp(result,kvps),shouldSyncOpenBrowserCanvas({kvps},result)];`);
for(const id of ['a0t1.generation.lease','extension:bridge-1']) {
  assert.deepEqual(probe({browser_id:id},{action:'navigate'}),[null,false,false]);
  assert.deepEqual(probe({},{browser_id:id,action:'navigate'}),[null,false,false]);
}
assert.deepEqual(probe({browser_id:7},{action:'navigate'}),[{browserId:7,contextId:'context-1',source:'tool-kvp'},true,true]);
assert.deepEqual(probe({},{action:'ensure',_browser_backend:'chrome_extension'}),[null,false,false]);
const auto=fs.readFileSync(root+'set_messages_after_loop/auto-open-browser-results.js','utf8');
const sync=new Function('id', `const isBrowserCanvasAlreadyOpen=()=>true,isFresh=()=>true,FOCUS_ACTIONS=new Set(['navigate']);
${extract(auto,'getBrowserId')}\n${extract(auto,'shouldSyncOpenBrowserCanvas')}
return shouldSyncOpenBrowserCanvas({}, {action:'navigate'}, {browser_id:id});`);
assert.equal(sync('a0t1.generation.lease'),false);assert.equal(sync(7),true);
// Verified static screenshots remain visible despite suppressing live previews.
assert.match(source,/if \(screenshotUri\) \{\s*displayKvps\[BROWSER_SCREENSHOT_KVP_KEY\] = screenshotUri;/);
'''
    result = subprocess.run(["node", "--input-type=module", "-", str(root)],
                            input=script, text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
