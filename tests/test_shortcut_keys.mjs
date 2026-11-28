import assert from 'node:assert/strict';
import test from 'node:test';
import { matchesChordKey } from '../webui/js/shortcut-keys.js';

test('chord matching works across keyboard layouts', () => {
  assert.equal(matchesChordKey({ key: 'ф', code: 'KeyA' }, 'a'), true);
  assert.equal(matchesChordKey({ key: 'a', code: 'KeyA' }, 'a'), true);
  assert.equal(matchesChordKey({ key: 'a', code: 'KeyQ' }, 'a'), true);
  assert.equal(matchesChordKey({ key: 'b', code: 'KeyB' }, 'a'), false);
  assert.equal(matchesChordKey({ key: 'ю', code: 'Period' }, '.'), true);
  assert.equal(matchesChordKey({ key: 'Insert', code: 'Insert' }, 'insert'), true);
  assert.equal(matchesChordKey(null, 'a'), false);
  assert.equal(matchesChordKey({ key: 'Escape', code: 'Escape' }, 'a'), false);
});
