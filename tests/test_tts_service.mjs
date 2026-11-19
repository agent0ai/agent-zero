import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../webui/js/tts-service.js', import.meta.url), 'utf8')
  .replace(/^import .*;$/gm, '').replace('export const ttsService', 'const ttsService');

function setup() {
  const notices = [], spoken = [], played = [], document = new EventTarget();
  const state = { provider: null, discoveries: 0 };
  const context = {
    document, EventTarget, CustomEvent, console: { warn() {}, error() {} },
    window: { speechSynthesis: { speak(utterance) {
      spoken.push(utterance.text);
      utterance.onstart();
      queueMicrotask(() => utterance.onend?.());
    }, cancel() {} } },
    SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
    Audio: class {
      async play() {
        played.push(this.src);
        this.onplaying();
        queueMicrotask(() => this.onended?.());
      }
      pause() {}
    },
    notifications: {
      addFrontendToastOnly(type, message, title, duration) {
        notices.push({ type, title, duration });
        return String(notices.length);
      },
      removeFromToastStack(id) { notices[Number(id.slice(6)) - 1].removed = true; },
    },
    sleep: ms => new Promise(resolve => setTimeout(resolve, ms)),
    async loadJsExtensions(point, options) {
      assert.equal(point, 'tts_provider');
      assert.equal(options.fresh, true);
      state.discoveries++;
      return state.provider ? [{ module: { default: () => state.provider } }] : [];
    },
  };
  const service = vm.runInNewContext(source + '\nttsService', context);
  document.dispatchEvent(new Event('click'));
  return { service, state, notices, spoken, played };
}

test('only a provider initialization signal displays a notice while waiting for audio', async () => {
  const { service, state, notices, spoken, played } = setup();
  const ready = Promise.withResolvers();
  let initializing;
  state.provider = { id: 'local', synthesize(text, { onInitializing }) {
    assert.equal(text, 'Hello.');
    initializing = onInitializing;
    return ready.promise;
  } };
  const playing = service.speak('Hello.');
  assert.equal(service.getState().isPreparing, true);
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(notices, []);
  initializing();
  initializing();
  assert.deepEqual(notices, [{ type: 'progress', title: 'Initializing speech', duration: 0 }]);
  assert.deepEqual(spoken, []);
  ready.resolve({ audioBase64: 'voice' });
  await playing;
  assert.deepEqual(played, ['data:audio/wav;base64,voice']);
  assert.deepEqual(spoken, []);
  assert.ok(notices[0].removed);
  assert.equal(service.getState().activeProviderId, 'local');
  assert.equal(service.getState().isPreparing, false);
  await service.speak('Hello.');
  assert.equal(notices.length, 1);
});

test('a stopped cold request cannot play or clear a newer stream’s notice', async () => {
  const { service, state, notices, played } = setup();
  const first = Promise.withResolvers(), second = Promise.withResolvers();
  let firstSignal;
  state.provider = { synthesize(text, { onInitializing }) {
    if (text === 'One') firstSignal = onInitializing;
    onInitializing();
    return text === 'One' ? first.promise : second.promise;
  } };
  const old = service.speak('One');
  await new Promise(resolve => setImmediate(resolve));
  service.stop();
  assert.ok(notices[0].removed);
  const current = service.speak('Two');
  firstSignal();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(notices.length, 2);
  first.resolve({ audioBase64: 'old' });
  await old;
  assert.equal(service.getState().isPreparing, true);
  assert.deepEqual(played, []);
  assert.ok(!notices[1].removed);
  second.resolve({ audioBase64: 'new' });
  await current;
  assert.deepEqual(played, ['data:audio/wav;base64,new']);
});

test('streaming speech warns once on provider failure and retries local on the next response', async () => {
  const { service, state, notices, spoken, played } = setup();
  let attempts = 0;
  state.provider = { synthesize() { attempts++; throw new Error('offline'); } };
  const first = 'This sentence can be spoken.';
  const last = 'This is a second full sentence.';
  const streaming = service.speakStream(12, first, false);
  await service.speakStream(12, first + ' ' + last, true);
  await streaming;
  assert.equal(attempts, 1);
  assert.deepEqual(spoken, [first, last]);
  assert.equal(notices.filter(n => n.type === 'warning').length, 1);
  state.provider = null;
  await service.speak('Browser by choice.');
  assert.equal(spoken.at(-1), 'Browser by choice.');
  assert.equal(notices.filter(n => n.type === 'warning').length, 1);
  state.provider = { synthesize: () => ({ audioBase64: 'updated' }) };
  await service.speakStream(13, 'Local after enabling.', true);
  assert.deepEqual(played, ['data:audio/wav;base64,updated']);
  assert.equal(state.discoveries, 3);
});

test('an explicitly registered provider keeps priority and can cancel pending speech', async () => {
  const { service, state, played, spoken } = setup();
  const ready = Promise.withResolvers();
  let stopped = false;
  const unregister = service.registerProvider('custom', {
    synthesize(text, { providerId }) {
      assert.equal(providerId, 'custom');
      return ready.promise;
    },
    stop() { stopped = true; },
  });
  const pending = service.speak('Custom voice');
  await new Promise(resolve => setImmediate(resolve));
  unregister();
  ready.resolve({ audioBase64: 'cancelled' });
  await pending;
  assert.ok(stopped);
  assert.equal(state.discoveries, 0);
  assert.deepEqual(played, []);
  assert.deepEqual(spoken, []);
});
