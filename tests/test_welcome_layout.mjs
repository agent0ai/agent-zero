import assert from 'node:assert/strict';
import test from 'node:test';
import { normalizeOrder, collectBlocks, pairedBlocks, moveBlock, dropTarget } from '../webui/components/welcome/welcome-layout.js';

const DEFAULT_ORDER = ['intro', 'quick-actions', 'accounts', 'channels', 'system'];

test('saved layout preserves absent plugin positions and appends newly discovered blocks', () => {
  assert.deepEqual(normalizeOrder(['plugin.weather', 'system', 'accounts', 'accounts', null, '', '  ', 2, {}], DEFAULT_ORDER),
    ['plugin.weather', 'system', 'accounts', 'intro', 'quick-actions', 'channels']);
  for (const invalid of [null, {}, 'intro', 42]) {
    assert.deepEqual(normalizeOrder(invalid, DEFAULT_ORDER), DEFAULT_ORDER);
  }
});

test('late plugin registration retains saved positions even after another block moves', () => {
  const saved = ['intro', 'plugin.weather', 'system'];
  const initial = normalizeOrder(saved, ['intro', 'system']);
  const moved = moveBlock(initial, 'system', 'intro');
  assert.deepEqual(normalizeOrder(moved, ['intro', 'system', 'plugin.weather', 'plugin.notes']),
    ['system', 'intro', 'plugin.weather', 'plugin.notes']);
  assert.deepEqual(normalizeOrder([], Array.from({length: 9}, (_, i) => `plugin.${i}`)),
    Array.from({length: 9}, (_, i) => `plugin.${i}`));
});

test('registration uses markup metadata and rejects ambiguous or incomplete blocks', () => {
  const block = (id, label = id) => ({dataset: {welcomeBlock: id, welcomeLabel: label}});
  const weather = block('plugin.weather', 'Weather');
  const notes = block('plugin.notes', 'Notes');
  const invalid = [block(''), block(' spaced '), block('missing-label', ''), {dataset: {}}];
  assert.deepEqual([...collectBlocks([weather, ...invalid, notes])],
    [['plugin.weather', weather], ['plugin.notes', notes]]);
  assert.deepEqual([...collectBlocks([weather, notes, block('plugin.weather')])],
    [['plugin.notes', notes]]);
});

test('any adjacent half-width blocks pair; lone halves expand and full-width blocks divide pairs', () => {
  const halves = new Set(['weather', 'notes', 'news', 'clock', 'extra']);
  assert.deepEqual([...pairedBlocks(['weather', 'notes', 'news', 'clock', 'extra'], halves)],
    ['weather', 'notes', 'news', 'clock']);
  assert.deepEqual([...pairedBlocks(['weather', 'intro', 'notes', 'news', 'clock'], halves)],
    ['notes', 'news']);
  assert.equal(pairedBlocks(['intro'], halves).size, 0);
});

test('moves preserve hidden blocks and work in both directions and at either end', () => {
  assert.deepEqual(moveBlock(DEFAULT_ORDER, 'system', 'intro'),
    ['system', 'intro', 'quick-actions', 'accounts', 'channels']);
  assert.deepEqual(moveBlock(DEFAULT_ORDER, 'intro', 'system', true),
    ['quick-actions', 'accounts', 'channels', 'system', 'intro']);
  assert.deepEqual(moveBlock(DEFAULT_ORDER, 'channels', 'quick-actions'),
    ['intro', 'channels', 'quick-actions', 'accounts', 'system']);
  assert.deepEqual(moveBlock(DEFAULT_ORDER, 'accounts', 'channels', true),
    ['intro', 'quick-actions', 'channels', 'accounts', 'system']);
  assert.equal(moveBlock(DEFAULT_ORDER, 'intro', 'intro'), DEFAULT_ORDER);
  assert.equal(moveBlock(DEFAULT_ORDER, 'missing', 'intro'), DEFAULT_ORDER);
  assert.equal(moveBlock(DEFAULT_ORDER, 'intro', 'missing'), DEFAULT_ORDER);
  assert.deepEqual(DEFAULT_ORDER, ['intro', 'quick-actions', 'accounts', 'channels', 'system']);
});


test('drop targeting handles full-width rows, paired cards, own block and empty space', () => {
  const rects = [
    { id: 'intro', top: 0, bottom: 200, left: 0, right: 600 },
    { id: 'accounts', top: 220, bottom: 400, left: 0, right: 290 },
    { id: 'channels', top: 220, bottom: 400, left: 310, right: 600 },
    { id: 'system', top: 420, bottom: 800, left: 0, right: 600 },
  ];
  assert.deepEqual(dropTarget(rects, 300, 10, 'system'), { id: 'intro', after: false, horizontal: false });
  assert.deepEqual(dropTarget(rects, 300, 190, 'system'), { id: 'intro', after: true, horizontal: false });
  assert.deepEqual(dropTarget(rects, 320, 280, 'accounts'), { id: 'channels', after: false, horizontal: true });
  assert.deepEqual(dropTarget(rects, 590, 280, 'accounts'), { id: 'channels', after: true, horizontal: true });
  assert.deepEqual(dropTarget(rects, 590, 900, 'intro'), { id: 'system', after: true, horizontal: false });
  assert.equal(dropTarget(rects, 300, 30, 'intro'), null);
  assert.equal(dropTarget([], 0, 0, 'intro'), null);
});
