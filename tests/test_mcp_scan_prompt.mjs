import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const source = readFileSync(
  new URL('../webui/components/settings/mcp/client/mcp-servers-store.js', import.meta.url),
  'utf8',
);
const fillScanTemplate = vm.runInNewContext(
  `${source.match(/^function fillScanTemplate[\s\S]*?^}$/m)[0]}; fillScanTemplate`,
);

test('scan prompt placeholders are filled in one pass over the template', () => {
  const filled = fillScanTemplate('Summary: {{INSPECTION_SUMMARY}}\nPass: {{RATING_PASS}}\nOther: {{UNKNOWN}}', {
    INSPECTION_SUMMARY: "server text {{RATING_PASS}} $& $' stays literal",
    RATING_PASS: 'PASS',
  });

  assert.equal(filled, "Summary: server text {{RATING_PASS}} $& $' stays literal\nPass: PASS\nOther: {{UNKNOWN}}");
  assert.match(source, /this\.scanPrompt = fillScanTemplate\(template, \{/);
  assert.doesNotMatch(source, /prompt\.replace\(/);
});

test('the scan report is rendered through the safe markdown renderer', () => {
  assert.match(source, /return renderSafeMarkdown\(this\.scanOutput\);/);
  assert.doesNotMatch(source, /marked\.parse\(/);
});
