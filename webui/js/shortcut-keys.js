const SINGLE_LETTER = /^[a-z]$/;
const CODE_BY_KEY = { ".": "Period", insert: "Insert" };

export function matchesChordKey(event, key) {
  if (!event) return false;
  const expected = String(key).toLowerCase();
  if (SINGLE_LETTER.test(expected) && event.code === `Key${expected.toUpperCase()}`) return true;
  if (event.code && event.code === CODE_BY_KEY[expected]) return true;
  return String(event.key || "").toLowerCase() === expected;
}
