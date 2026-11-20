import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const plugin = { key: 'sample', title: 'Sample', github: 'https://github.com/example/sample' };

function load(compatibility, answers = []) {
  const calls = [], dialogs = [], errors = [];
  const api = {
    async callJsonApi(endpoint, input) {
      calls.push(input);
      if (input.action === 'check_compatibility') return { success: true, ...compatibility };
      return { success: true, plugin_name: plugin.key };
    },
  };
  const source = readFileSync(new URL('../plugins/_plugin_installer/webui/pluginInstallStore.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '').replace('export { store };', '');
  const store = vm.runInNewContext(`${source}\nstore`, {
    createStore: (_, value) => value, URL, api,
    showConfirmDialog: async options => { dialogs.push(options); return answers.shift() ?? false; },
    toastFrontendSuccess() {}, toastFrontendError: message => errors.push(message),
    document: {
      createElement: () => ({
        textContent: '',
        get innerHTML() {
          return this.textContent.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
        },
      }),
    },
  });
  store.selectedPlugin = { ...plugin };
  store.fetchInstalledPluginInfo = () => {};
  return { store, api, calls, dialogs, errors };
}

test('a v3 plugin warns users on v2 and cancelling installs nothing', async () => {
  const { store, calls, dialogs } = load({ a0_version: '3.*', current_version: 'v2.15', compatible: false });
  await store.installFromIndex(plugin);
  assert.deepEqual(calls.map(call => call.action), ['check_compatibility']);
  assert.equal(dialogs.length, 1);
  assert.equal(dialogs[0].confirmText, 'Install Anyway');
  assert.match(dialogs[0].message, /not compatible/);
  assert.match(dialogs[0].message, /v2\.15/);
  assert.match(dialogs[0].message, /3\.\*/);
  assert.equal(store.loading, false);
  assert.equal(store.installedPlugins.length, 0);
});

test('confirming a mismatch preserves the security warning and then installs', async () => {
  const { store, calls, dialogs } = load({ a0_version: ['3.0', '4.*'], current_version: 'v2.15', compatible: false }, [true, true]);
  await store.installFromIndex(plugin);
  assert.deepEqual(calls.map(call => call.action), ['check_compatibility', 'install_git']);
  assert.equal(dialogs[1].title, 'Security Warning');
  assert.equal(dialogs[1].extensionContext.kind, 'plugin_hub_plugin_install_warning');
  assert.equal(calls[1].git_url, plugin.github);
  assert.equal(calls[1].plugin_name, plugin.key);
  assert.equal(store.installedPlugins[0], plugin.key);
  assert.equal(store.loading, false);
});

test('accepting compatibility does not bypass a cancelled security warning', async () => {
  const { store, calls } = load({ a0_version: '4.*', current_version: 'v3.2', compatible: false }, [true, false]);
  await store.installFromIndex(plugin);
  assert.deepEqual(calls.map(call => call.action), ['check_compatibility']);
});

test('compatible and legacy plugins only show the existing security warning', async () => {
  for (const requirement of ['3.*', null]) {
    const { store, calls, dialogs } = load({ a0_version: requirement, current_version: 'v3.2', compatible: true }, [true]);
    await store.installFromIndex(plugin);
    assert.equal(dialogs.length, 1);
    assert.equal(dialogs[0].title, 'Security Warning');
    assert.equal(calls.at(-1).action, 'install_git');
  }
});

test('unknown fork versions and failed manifest checks warn but allow confirmation', async () => {
  for (const requirement of ['3.*', null]) {
    const { store, calls, dialogs } = load({ a0_version: requirement, current_version: 'custom-fork', compatible: null, error: 'Cannot verify' }, [true, true]);
    await store.installFromIndex(plugin);
    assert.match(dialogs[0].message, /could not be verified/);
    assert.match(dialogs[0].message, /custom-fork/);
    assert.equal(calls.at(-1).action, 'install_git');
  }
});

test('untrusted requirement and version text are escaped in the popup', async () => {
  const { store, dialogs } = load({ a0_version: '<img src=x onerror=alert(1)>', current_version: '<fork>', compatible: null, error: '<bad>' });
  await store.installFromIndex(plugin);
  assert.ok(!dialogs[0].message.includes('<'));
  assert.match(dialogs[0].message, /&lt;img/);
  assert.match(dialogs[0].message, /&lt;fork&gt;/);
});

test('installation checks the manifest again instead of trusting the page result', async () => {
  const compatibility = { a0_version: '3.*', current_version: 'v3.2', compatible: true };
  const { store, calls, dialogs } = load(compatibility);
  await store.fetchPluginCompatibility(plugin);
  compatibility.a0_version = '4.*';
  compatibility.compatible = false;
  await store.installFromIndex(plugin);
  assert.deepEqual(calls.map(call => call.action), ['check_compatibility', 'check_compatibility']);
  assert.match(dialogs[0].message, /4\.\*/);
});

test('late page checks cannot overwrite a newer compatibility result', async () => {
  const { store, api } = load({});
  const pending = [];
  api.callJsonApi = () => new Promise(resolve => pending.push(resolve));
  const first = store.fetchPluginCompatibility(plugin);
  const second = store.fetchPluginCompatibility(plugin);
  pending[1]({ success: true, a0_version: '4.*', current_version: 'v3.2', compatible: false });
  await second;
  pending[0]({ success: true, a0_version: '3.*', current_version: 'v3.2', compatible: true });
  await first;
  assert.equal(store.pluginCompatibility.a0_version, '4.*');
  assert.equal(store.compatibilityLoading, false);
});

test('a failed API request warns instead of silently skipping the check', async () => {
  const { store, api, dialogs } = load({});
  store.pluginCompatibility = { current_version: 'v3.2' };
  api.callJsonApi = async () => { throw new Error('offline'); };
  await store.installFromIndex(plugin);
  assert.match(dialogs[0].message, /could not be verified/);
  assert.match(dialogs[0].message, /v3\.2/);
  assert.equal(store.loading, false);
});

test('the detail label distinguishes missing requirements, alternatives and unavailable metadata', () => {
  const { store } = load({});
  assert.equal(store.formatA0Requirement({ a0_version: null }), 'Not specified');
  assert.equal(store.formatA0Requirement({ a0_version: ['3.0', '4.*'] }), '3.0 OR 4.*');
  assert.equal(store.formatA0Requirement({ a0_version: null, error: 'offline' }), 'Unknown');
});
