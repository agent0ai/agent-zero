import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function setup(captureFails = false) {
  const events = new EventTarget(), handle = new EventTarget();
  let captured = false, saves = 0;
  handle.closest = () => ({ getBoundingClientRect: () => ({ top: 250, height: 100 }) });
  handle.setPointerCapture = () => { if (captureFails) throw new Error('Capture unavailable'); captured = true; };
  handle.hasPointerCapture = () => captured;
  handle.releasePointerCapture = () => { captured = false; };
  const source = readFileSync(new URL('../webui/components/canvas/right-canvas-store.js', import.meta.url), 'utf8')
    .replace(/^import\b[\s\S]*?;\n/gm, '').replace('export const store', 'const store');
  const store = vm.runInNewContext(`${source}\nstore`, {
    AbortController, createStore: (_, model) => model,
    addEventListener: events.addEventListener.bind(events),
  });
  store._rootElement = { getBoundingClientRect: () => ({ top: 0, height: 800 }) };
  store.railHeight = 100;
  store.persist = () => { saves++; };
  const start = () => store.startRailDrag({ button: 0, pointerId: 1, clientY: 300, currentTarget: handle, preventDefault() {} });
  const dispatch = (type, values = {}, target = events) => target.dispatchEvent(Object.assign(new Event(type), { pointerId: 1, buttons: 1, clientY: 400, ...values }));
  return { store, start, dispatch, handle, saves: () => saves, captured: () => captured };
}

test('rail tracks and releases its pointer outside the handle when capture fails', () => {
  const t = setup(true); t.start();
  t.dispatch('pointermove', { pointerId: 2 }); assert.equal(t.store.railPosition, null);
  t.dispatch('pointermove'); assert.equal(t.store.railPosition, 0.5);
  t.dispatch('pointerup', { pointerId: 2 }); assert.ok(t.store._railDragCleanup);
  t.dispatch('pointerup'); assert.equal(t.store._railDragCleanup, null);
  t.dispatch('pointermove', { clientY: 600 }); assert.equal(t.store.railPosition, 0.5);
  assert.equal(t.saves(), 1);
});

test('released buttons, blur and unmount clean up rail dragging', () => {
  const t = setup(); t.start();
  t.dispatch('pointermove');
  t.dispatch('pointermove', { buttons: 0, clientY: 700 });
  assert.equal(t.store.railPosition, 0.5); assert.equal(t.store._railDragCleanup, null);
  assert.equal(t.captured(), false);
  t.start(); t.dispatch('blur', { pointerId: undefined });
  assert.equal(t.store._railDragCleanup, null);
  t.start(); t.store.unmountRail();
  t.dispatch('pointermove', { clientY: 700 }); assert.equal(t.store.railPosition, 0.5);
  assert.equal(t.saves(), 3);
});

test('cancel and lost capture end a rail gesture exactly once', () => {
  for (const type of ['pointercancel', 'lostpointercapture']) {
    const t = setup(); t.start();
    t.dispatch(type, {}, type === 'lostpointercapture' ? t.handle : undefined);
    t.dispatch('pointerup');
    assert.equal(t.store._railDragCleanup, null); assert.equal(t.captured(), false);
    assert.equal(t.saves(), 1);
  }
});
