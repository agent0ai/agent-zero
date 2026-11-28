import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function setup(captureFails = false, panelsWidth = 720) {
  const events = new EventTarget(), handle = new EventTarget();
  const overlays = new Set(), classes = new Set(), widths = [], notifications = [];
  const rootStyles = new Map(), panelStyles = new Map();
  let captured = false, saves = 0;
  const panels = {
    getBoundingClientRect: () => ({ width: panelsWidth }),
    style: {
      setProperty: (key, value) => panelStyles.set(key, value),
      removeProperty: key => panelStyles.delete(key),
    },
  };
  const dispatch = (type, values = {}, target = events) => target.dispatchEvent(Object.assign(new Event(type), {
    pointerId: 1, buttons: 1, clientX: 720, ...values,
  }));
  handle.setPointerCapture = () => { if (captureFails) throw new Error('Capture unavailable'); captured = true; };
  handle.hasPointerCapture = () => captured;
  handle.releasePointerCapture = () => { captured = false; dispatch('lostpointercapture', {}, handle); };
  const source = readFileSync(new URL('../webui/components/canvas/right-canvas-store.js', import.meta.url), 'utf8')
    .replace(/^import\b[\s\S]*?;\n/gm, '').replace('export const store', 'const store');
  const store = vm.runInNewContext(`${source}\nstore`, {
    AbortController, createStore: (_, model) => model,
    addEventListener: events.addEventListener.bind(events),
    document: {
      getElementById: () => ({ getBoundingClientRect: () => ({ left: 240 }) }),
      body: { appendChild: el => overlays.add(el), classList: { add: name => classes.add(name), remove: name => classes.delete(name) } },
      createElement: () => {
        const element = { properties: {}, setAttribute() {}, remove: () => overlays.delete(element) };
        element.style = { setProperty: (key, value) => { element.properties[key] = value; } };
        return element;
      },
    },
  });
  store._rootElement = {
    getBoundingClientRect: () => ({ top: 20, right: 1440, height: 800 }),
    closest: () => ({ getBoundingClientRect: () => ({ right: 1440 }) }),
    querySelector: () => panels,
    style: { setProperty: (key, value) => rootStyles.set(key, value) },
  };
  store.isOpen = true;
  store.applyLayoutState = () => widths.push(store.width);
  store.persist = () => { saves++; };
  store.dispatchResizeEvent = name => notifications.push(name);
  const start = (values = {}) => store.startResize({ button: 0, pointerId: 1, clientX: 720,
    currentTarget: handle, preventDefault() {}, ...values });
  return { store, start, dispatch, handle, overlays, classes, widths, notifications, rootStyles, panelStyles,
    saves: () => saves, captured: () => captured };
}

test('canvas shell follows the pointer while surface width waits for release', () => {
  const t = setup(); t.start();
  const preview = [...t.overlays][0];
  assert.equal(t.captured(), true);
  assert.equal(t.panelStyles.get('--right-canvas-resize-content-width'), '720px');
  for (const x of [600, 900, 700]) {
    t.dispatch('pointermove', { clientX: x });
    assert.equal(preview.properties['--resize-left'], `${x}px`);
    assert.equal(t.rootStyles.get('width'), `${1440 - x}px`);
    assert.equal(t.panelStyles.get('--right-canvas-resize-content-width'), '720px');
    assert.equal(t.store.width, 720);
    assert.deepEqual(t.widths, []);
    assert.equal(t.saves(), 0);
  }
  t.dispatch('pointerup', { clientX: 800 });
  assert.equal(t.store.width, 640);
  assert.deepEqual(t.widths, [640]);
  assert.equal(t.saves(), 1);
  assert.equal(t.panelStyles.has('--right-canvas-resize-content-width'), false);
  assert.equal(t.overlays.size, 0);
  assert.equal(t.classes.size, 0);
  assert.equal(t.captured(), false);
  assert.equal(t.store._resizeCleanup, null);
  assert.deepEqual(t.notifications, ['right-canvas-resize-start', 'right-canvas-resize-end']);
  t.dispatch('pointermove', { clientX: 200 });
  assert.equal(t.store.width, 640);
});

test('a zero-width panel does not pin surface content to zero', () => {
  const t = setup(false, 0); t.start();
  assert.equal(t.panelStyles.has('--right-canvas-resize-content-width'), false);
  t.dispatch('pointermove', { clientX: 900 });
  t.dispatch('pointerup', { clientX: 900 });
  assert.equal(t.store.width, 540);
  assert.equal(t.saves(), 1);
});

test('window tracking works without capture, ignores other pointers and clamps live width', () => {
  const t = setup(true); t.start();
  const preview = [...t.overlays][0];
  t.dispatch('pointermove', { pointerId: 2, clientX: 900 });
  t.dispatch('pointerup', { pointerId: 2 });
  assert.equal(preview.properties['--resize-left'], '720px');
  assert.equal(t.rootStyles.get('width'), '720px');
  t.dispatch('pointermove', { clientX: -100 });
  assert.equal(preview.properties['--resize-left'], '240px');
  assert.equal(t.rootStyles.get('width'), '1200px');
  t.dispatch('pointermove', { clientX: 2000 });
  assert.equal(preview.properties['--resize-left'], '1440px');
  assert.equal(t.rootStyles.get('width'), '0px');
  t.dispatch('pointerup', { clientX: 1500 });
  assert.deepEqual(t.widths, [0]);
  assert.equal(t.saves(), 1);
});

test('cancel, lost capture, blur, viewport changes, Escape and unmount restore shell and surface widths', () => {
  for (const type of ['pointercancel', 'lostpointercapture', 'blur', 'resize', 'keydown', 'unmount']) {
    const t = setup(); t.start(); t.dispatch('pointermove', { clientX: 900 });
    if (type === 'unmount') t.store._resizeCleanup();
    else t.dispatch(type, { key: 'Escape' }, type === 'lostpointercapture' ? t.handle : undefined);
    assert.equal(t.store.width, 720, type);
    assert.equal(t.rootStyles.get('width'), '720px', type);
    assert.equal(t.panelStyles.has('--right-canvas-resize-content-width'), false, type);
    assert.equal(t.saves(), 0, type);
    assert.equal(t.overlays.size, 0, type);
    assert.equal(t.classes.size, 0, type);
    assert.equal(t.captured(), false, type);
    t.dispatch('pointerup', { clientX: 900 });
    assert.equal(t.notifications.length, 2, type);
  }
});

test('a missed release commits only the last drag position; a click does not refresh', () => {
  const t = setup(); t.start();
  t.dispatch('pointermove', { clientX: 900 });
  t.dispatch('pointermove', { buttons: 0, clientX: 1100 });
  assert.deepEqual(t.widths, [540]);
  assert.equal(t.saves(), 1);
  assert.equal(t.panelStyles.has('--right-canvas-resize-content-width'), false);
  const click = setup(); click.start(); click.dispatch('pointerup');
  assert.deepEqual(click.widths, []);
  assert.equal(click.saves(), 0);
});

test('hidden/mobile canvases, secondary buttons and non-primary pointers cannot start a resize', () => {
  for (const [state, event] of [
    [{ isOpen: false }, {}], [{ isMobileMode: true }, {}], [{ isOverlayMode: true }, {}],
    [{}, { button: 2 }], [{}, { isPrimary: false }],
  ]) {
    const t = setup(); Object.assign(t.store, state); t.start(event);
    assert.equal(t.overlays.size, 0);
    assert.equal(t.store._resizeCleanup, null);
  }
});
