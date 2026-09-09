import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import { randomBytes } from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const bridgePath = fileURLToPath(new URL('../plugins/_whatsapp_integration/whatsapp-bridge/bridge.js', import.meta.url));
const source = fs.readFileSync(bridgePath, 'utf8')
  .replace(/^#!.*\n/, '')
  .replace(/^import .*;\n/gm, '')
  .replaceAll('import.meta.url', JSON.stringify(new URL(`file://${bridgePath}`).href))
  .split('// Start\n')[0];

// Exercise the real callback and filesystem; stub only transport and HTTP setup.
async function receive(t, { fileName = 'report.pdf', sender = '123', group = false, mention = false, reply = false, allowed = '123', allowGroup = false, fromMe = false, mode = 'self-chat', lid = false, wrapped = false } = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'a0-wa-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const cache = path.join(root, 'tmp/whatsapp/media');
  const target = path.join(root, 'extensions/python/job_loop/sentinel.py');
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, 'ORIGINAL');
  const session = path.join(root, 'session');
  fs.mkdirSync(session);
  if (lid) fs.writeFileSync(path.join(session, 'lid-mapping-123.json'), JSON.stringify(sender));
  const handlers = {};
  let downloads = 0;
  const express = Object.assign(() => ({ use() {}, get() {}, post() {} }), { json() {} });
  const sandbox = vm.createContext({
    ...fs, path, randomBytes, URL, console,
    process: { argv: ['node', bridgePath, '--session', session, '--cache-dir', cache, '--allowed-numbers', allowed, '--allow-group', String(allowGroup), '--mode', mode], env: {} },
    express, pino: () => ({}),
    useMultiFileAuthState: async () => ({ state: {}, saveCreds() {} }),
    fetchLatestBaileysVersion: async () => ({ version: [] }),
    makeWASocket: () => ({ user: { id: '999@s.whatsapp.net' }, ev: { on: (name, fn) => { handlers[name] = fn; } }, groupMetadata: async () => ({ subject: 'Test group' }) }),
    downloadMediaMessage: async () => { downloads++; return Buffer.from('POC_CONFIRMED'); },
  });
  const queue = await vm.runInContext(`(async () => { ${source}\nawait startSocket(); return messageQueue; })()`, sandbox);
  const document = { documentMessage: { fileName, contextInfo: { mentionedJid: mention ? ['999@s.whatsapp.net'] : [], stanzaId: reply ? 'quoted' : undefined, participant: reply ? '999@s.whatsapp.net' : undefined } } };
  await handlers['messages.upsert']({ type: 'notify', messages: [{
    key: { id: 'test-message', remoteJid: group ? '456@g.us' : `${sender}@${lid ? 'lid' : 's.whatsapp.net'}`, participant: group ? `${sender}@s.whatsapp.net` : undefined, fromMe },
    message: wrapped ? { documentWithCaptionMessage: { message: document } } : document,
  }] });
  return { downloads, queue, cache, target, contents: fs.readFileSync(target, 'utf8') };
}

test('document metadata cannot escape the cache; authorization precedes downloads', async t => {
  for (const fileName of ['report.pdf', '../../../../../extensions/python/job_loop/sentinel.py', '..\\..\\report.pdf', '/absolute/report.pdf']) {
    const result = await receive(t, { fileName });
    assert.equal(result.contents, 'ORIGINAL', `overwrite from ${fileName}`);
    assert.equal(result.downloads, 1);
    assert.equal(result.queue.length, 1);
    const [saved] = result.queue[0].mediaUrls;
    assert.equal(path.dirname(saved), result.cache);
    assert.equal(fs.readFileSync(saved, 'utf8'), 'POC_CONFIRMED');
  }
  for (const options of [{ sender: '456' }, { group: true }, { group: true, allowGroup: true }, { fromMe: true, mode: 'dedicated' }]) {
    const result = await receive(t, options);
    assert.equal(result.downloads, 0, JSON.stringify(options));
    assert.equal(result.queue.length, 0);
  }
  for (const options of [{ group: true, allowGroup: true, mention: true }, { group: true, allowGroup: true, reply: true }, { sender: '999', allowed: '999', fromMe: true }, { sender: '00123' }, { allowed: '' }, { sender: '777', lid: true }, { wrapped: true, fileName: '../../../../../extensions/python/job_loop/sentinel.py' }]) {
    const result = await receive(t, options);
    assert.equal(result.downloads, 1, JSON.stringify(options));
    assert.equal(result.queue.length, 1);
    assert.equal(result.contents, 'ORIGINAL');
  }
});
