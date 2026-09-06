import base64
from pathlib import Path
import re
import shutil
import subprocess

import pytest


@pytest.mark.skipif(not shutil.which("node"), reason="node is required")
def test_parameter_parsing_and_save_validation():
    source = (Path(__file__).parents[1] / "plugins/_model_config/webui/model-config-store.js").read_text()
    source = re.sub(r"^import .*?;\n", "", source, flags=re.MULTILINE)
    source = """
const createStore = (_name, value) => value;
const apiKeysState = {}, apiKeysMethods = {}, switcherState = {}, switcherMethods = {};
""" + source
    module_url = "data:text/javascript;base64," + base64.b64encode(source.encode()).decode()
    script = r'''
import assert from 'node:assert/strict';
const { textToKwargs, kwargsToText, store, MODEL_SECTIONS } = await import(MODULE_URL);
const values = { plain: 'hello', literal: 'true', flag: true, off: false, nothing: null,
                 number: 0.2, object: { list: [1, false] }, empty: '' };
assert.deepEqual(textToKwargs(kwargsToText(values)), values);
assert.deepEqual(textToKwargs('# comment\n\nplain=hello\nurl=https://example.test/?a=b'),
                 {plain: 'hello', url: 'https://example.test/?a=b'});
for (const value of ['{"enabled":True}', '[1,]', '"unfinished', 'True', 'False', 'None']) {
  assert.throws(() => textToKwargs('param=' + value), /line 1: invalid JSON for param/);
}
assert.throws(() => textToKwargs('# comment\nbroken'), /line 2: use KEY=VALUE/);
let saves = 0, keySaves = 0, saved;
const notifications = [];
globalThis.justToast = (message, type) => notifications.push({message, type});
const draft = {kwargs: {old: true}, _kwargs_text: 'param={"enabled":True}'};
store.updateModelKwargs(draft);
assert.deepEqual(draft.kwargs, {old: true});
assert.match(notifications.at(-1).message, /invalid JSON/);
draft._kwargs_text = 'param={"enabled":true}';
store.updateModelKwargs(draft);
assert.deepEqual(draft.kwargs, {param: {enabled: true}});
store.persistAllDirtyApiKeys = async () => { keySaves++; };
store.saveGlobalPresets = async presets => { saves++; saved = structuredClone(presets); return true; };
for (const slot of ['chat', 'vision', 'utility', 'embedding']) {
  store.globalPresets = [{name: 'Test', [slot]: {provider: 'test', name: 'test',
    kwargs: {old: true}, _kwargs_text: 'param={"enabled":True}'}}];
  store.globalPresets.push({name: 'Other'});
  const editor = store.createPresetEditor('Other');
  const before = [saves, keySaves];
  assert.equal(await editor.savePresets(), false);
  assert.deepEqual([saves, keySaves], before);
  assert.match(notifications.at(-1).message, /invalid JSON/);
  assert.ok(notifications.at(-1).message.startsWith(`Test (${MODEL_SECTIONS.find(s => s.key === slot + '_model').title}):`));
  assert.equal(notifications.at(-1).type, 'error');
  assert.equal(editor.presets[0][slot]._kwargs_text, 'param={"enabled":True}');
  editor.presets[0][slot]._kwargs_text = 'param={"enabled":true}';
  assert.equal(await editor.savePresets(), true);
  assert.deepEqual(saved[0][slot].kwargs, {param: {enabled: true}});
}
'''.replace("MODULE_URL", repr(module_url))
    subprocess.run(["node", "--input-type=module", "-e", script], check=True)
