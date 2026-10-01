"""Chat import/export targeting and native file chooser cancellation."""
from pathlib import Path
import re
import subprocess


def test_chat_export_target_and_import_cancellation():
    source = (Path(__file__).resolve().parents[1]
              / 'webui/components/sidebar/chats/chats-store.js').read_text()
    source = re.sub(r'^import\b[\s\S]*?;\n', '', source, flags=re.M)
    source = source.replace('export { store };', '')
    script = r'''
import assert from 'node:assert/strict';
const createStore = (_name, model) => model;
const requests = [], downloads = [], notifications = [];
const getContext = () => 'fallback';
const setContext = () => {};
const toast = message => notifications.push(message);
const toastFetchError = (_message, error) => { throw error; };
const sendJsonData = async (url, body) => {
  requests.push({url, body});
  return url === '/chat_export' ? {ctxid:body.ctxid, content:'{}'} : {ctxids:[]};
};
let picker;
const document = {createElement(tag) {
  assert.equal(tag, 'input');
  return picker = {click() {}, files:[]};
}};
''' + source + r'''
store.downloadFile = (...args) => downloads.push(args);
store.selected = 'active';
await store.saveChat('clicked');
assert.deepEqual(requests.at(-1), {url:'/chat_export', body:{ctxid:'clicked'}});
assert.deepEqual(downloads.at(-1), ['clicked.json', '{}']);
assert.equal(store.selected, 'active');
await store.saveChat();
assert.equal(requests.at(-1).body.ctxid, 'active');
store.selected = '';
await store.saveChat();
assert.equal(requests.at(-1).body.ctxid, 'fallback');
const count = requests.length, toastCount = notifications.length;
let loading = store.loadChats();
assert.equal(picker.accept, '.json');
assert.equal(picker.multiple, true);
picker.oncancel();
await loading;
loading = store.loadChats();
await picker.onchange();
await loading;
assert.equal(requests.length, count, 'cancel and empty selection must not call chat_load');
assert.equal(notifications.length, toastCount, 'cancellation is silent');
store.readJsonFiles = async () => ['{"history":[]}'];
await store.loadChats();
assert.deepEqual(requests.at(-1), {url:'/chat_load', body:{chats:['{"history":[]}']}});
assert.equal(notifications.at(-1), 'Chats loaded.');
'''
    subprocess.run(['node', '--input-type=module'], input=script, text=True,
                   check=True, timeout=15)
