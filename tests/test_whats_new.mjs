import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const source = readFileSync(new URL(
  '../plugins/_whats_new/extensions/webui/initFw_end/whats-new.js', import.meta.url,
), 'utf8').replace(/^import .*;\n/gm, '').replace('export default ', '');

function load({ configured = true, saved = new Map(), version = 'v2.15', fail = false } = {}) {
  const timers = [], opened = [], requests = [], errors = [];
  const document = new EventTarget();
  const context = vm.createContext({
    document: Object.assign(document, { querySelector: () => null }),
    window: { setTimeout: callback => timers.push(callback) },
    localStorage: { getItem: key => saved.get(key) || null, setItem: (key, value) => saved.set(key, value) },
    gitinfo: { version }, slides: [{ id: 'a0-cleaner' }],
    getModalStack: () => [], isModalOpen: () => false,
    openModal: path => opened.push(path),
    callJsonApi: async (path, data) => {
      requests.push({ path, data });
      if (fail) throw new Error('Unavailable');
      return { model_configured: configured };
    },
    console: { error: (...args) => errors.push(args) },
  });
  vm.runInContext(`${source}\ninitWhatsNew();`, context);
  return { timers, opened, requests, errors, document, saved };
}

test('new users skip this release after onboarding and reload, but see future updates', async () => {
  const first = load({ configured: false });
  await first.timers.shift()();
  assert.equal(first.opened.length, 0);
  assert.equal(JSON.parse(first.saved.get('a0_whats_new_seen_version')).version, 'v2.15');
  assert.equal(first.saved.has('a0_whats_new_never_show'), false);

  first.document.dispatchEvent(new Event('onboarding-configured'));
  first.document.dispatchEvent(new Event('modal-closed'));
  assert.equal(first.timers.length, 0);

  const reload = load({ saved: first.saved });
  await reload.timers.shift()();
  assert.equal(reload.opened.length, 0);
  assert.equal(reload.requests.length, 0);

  const update = load({ saved: first.saved, version: 'v2.16' });
  await update.timers.shift()();
  assert.deepEqual(update.opened, ['/plugins/_whats_new/webui/main.html']);
});

test('configured users still see the showcase', async () => {
  const app = load();
  await app.timers.shift()();
  assert.equal(app.requests[0].path, '/plugins/_model_config/model_config_get');
  assert.deepEqual(app.opened, ['/plugins/_whats_new/webui/main.html']);
  assert.equal(app.saved.has('a0_whats_new_seen_version'), false);
});

test('modal closes during the readiness check cannot bypass first-run suppression', async () => {
  const app = load({ configured: false });
  const pending = app.timers.shift()();
  app.document.dispatchEvent(new Event('modal-closed'));
  await pending;
  assert.equal(app.timers.length, 0);
  assert.equal(app.opened.length, 0);
});

test('readiness failures skip the showcase without recording it as seen', async () => {
  const app = load({ fail: true });
  await app.timers.shift()();
  app.document.dispatchEvent(new Event('modal-closed'));
  assert.equal(app.timers.length, 0);
  assert.equal(app.opened.length, 0);
  assert.equal(app.saved.size, 0);
  assert.equal(app.errors.length, 1);
});
