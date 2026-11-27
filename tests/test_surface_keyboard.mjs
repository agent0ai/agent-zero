import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function setup(userAgent = 'Mozilla/5.0 (Linux; Android 14) Mobile') {
  class Element {
    constructor() {
      this.attributes = new Map();
      this.listeners = new Map();
      this.classes = new Set();
      this.classList = { toggle: (name, enabled) => enabled ? this.classes.add(name) : this.classes.delete(name) };
      this.style = {};
      this.value = '';
      this.removed = false;
    }

    addEventListener(type, handler) {
      const listeners = this.listeners.get(type) || new Set();
      listeners.add(handler);
      this.listeners.set(type, listeners);
    }

    removeEventListener(type, handler) {
      this.listeners.get(type)?.delete(handler);
    }

    dispatchEvent(event) {
      event.target = this;
      event.preventDefault ||= () => { event.defaultPrevented = true; };
      for (const handler of this.listeners.get(event.type) || []) handler(event);
      return !event.defaultPrevented;
    }

    setAttribute(name, value) {
      this.attributes.set(name, value);
    }

    getAttribute(name) {
      return this.attributes.get(name);
    }

    focus() {
      documentRef.activeElement = this;
      this.dispatchEvent({ type: 'focus' });
    }

    blur() {
      if (documentRef.activeElement === this) documentRef.activeElement = null;
      this.dispatchEvent({ type: 'blur' });
    }

    remove() {
      this.removed = true;
    }
  }

  const documentRef = {
    activeElement: null,
    body: { children: [], append(node) { this.children.push(node); } },
    createElement: () => new Element(),
  };
  const source = readFileSync(new URL('../webui/js/surface-keyboard.js', import.meta.url), 'utf8')
    .replaceAll('export function ', 'function ');
  const api = vm.runInNewContext(`${source}\n({ createSurfaceKeyboard, isMobileUserAgent })`, {
    document: documentRef,
    navigator: { userAgent },
    setTimeout,
    clearTimeout,
    console,
  });
  return { ...api, document: documentRef, Element };
}

test('mobile user-agent detection recognizes phone and tablet families but not desktop', () => {
  const { isMobileUserAgent } = setup();
  for (const userAgent of [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)',
    'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)',
    'Mozilla/5.0 (Linux; Android 14; Pixel Tablet)',
    'Mozilla/5.0 (Windows Phone 10.0; Android 6.0.1; Microsoft; Lumia 950)',
  ]) assert.equal(isMobileUserAgent(userAgent), true, userAgent);
  assert.equal(isMobileUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130 Safari/537.36'), false);
});

test('keyboard toggle focuses the soft input and routes text and special keys', () => {
  const { createSurfaceKeyboard, document, Element } = setup();
  const button = new Element();
  const texts = [], keys = [], targetEvents = [];
  let targetBlurs = 0;
  const keyboard = createSurfaceKeyboard(button, {
    onFocusTarget: () => false,
    onBlurTarget: () => { targetBlurs++; },
    onText: text => texts.push(text),
    onKey: key => keys.push(key),
  });
  const input = document.body.children[0];

  button.dispatchEvent({ type: 'click' });
  assert.equal(button.getAttribute('aria-pressed'), 'true');
  assert.equal(document.activeElement, input);
  input.value = 'hello';
  input.dispatchEvent({ type: 'input' });
  assert.deepEqual(texts, ['hello']);
  assert.equal(input.value, '');
  input.dispatchEvent({ type: 'keydown', key: 'Enter' });
  input.dispatchEvent({ type: 'keydown', key: 'Shift' });
  assert.deepEqual(keys, ['Enter']);
  input.dispatchEvent({ type: 'compositionstart' });
  input.value = 'こんにちは';
  input.dispatchEvent({ type: 'input', isComposing: true });
  assert.deepEqual(texts, ['hello']);
  input.dispatchEvent({ type: 'compositionend' });
  assert.deepEqual(texts, ['hello', 'こんにちは']);
  button.dispatchEvent({ type: 'click' });
  assert.equal(button.getAttribute('aria-pressed'), 'false');
  assert.equal(targetBlurs, 1);
  keyboard.destroy();
  assert.equal(input.removed, true);
  assert.equal(targetEvents.length, 0);
});
