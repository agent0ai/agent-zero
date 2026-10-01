from pathlib import Path
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORE_PATH = PROJECT_ROOT / "webui/components/modals/file-browser/file-browser-store.js"


def test_file_links_choose_visible_browser_or_modal_and_preserve_file_actions():
    source = STORE_PATH.read_text(encoding="utf-8")
    handler = source[source.index("window.openFileLink ="):].replace(
        'await import("/components/canvas/right-canvas-store.js")', '{store: canvas}'
    )
    script = '''
import assert from 'node:assert/strict';
const window = globalThis;
const FILE_BROWSER_MODAL_PATH = 'modals/file-browser/file-browser.html';
let modal = false, rendered = false, visible = false;
let response = {exists:true, is_dir:true, abs_path:'/clicked'};
const calls = [];
const canvas = {shouldRender:()=>rendered, isSurfaceVisible:()=>visible};
const store = {
  navigateToFolder:path=>calls.push(['navigate',path]),
  open:path=>calls.push(['open',path]),
  downloadFile:file=>calls.push(['download',file.path]),
};
window.isModalOpen = () => modal;
window.sendJsonData = async () => response;
window.toastFrontendError = () => calls.push(['error']);
''' + handler + '''
for (const [m,r,v,expected] of [[true,false,false,'navigate'],[false,true,true,'navigate'],[false,true,false,'open'],[false,false,true,'open']]) {
  modal=m; rendered=r; visible=v;
  await window.openFileLink('relative-link');
  assert.deepEqual(calls.pop(), [expected,'/clicked']);
}
response = {exists:true,is_dir:false,abs_path:'/clicked.txt',file_name:'clicked.txt'};
await window.openFileLink('file');
assert.deepEqual(calls.pop(), ['download','/clicked.txt']);
response = {exists:false};
await window.openFileLink('missing');
assert.deepEqual(calls.pop(), ['error']);
assert.deepEqual(calls, []);
'''
    subprocess.run(['node', '--input-type=module'], input=script, text=True, check=True, timeout=15)
