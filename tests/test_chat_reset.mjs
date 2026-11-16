import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = path => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
const withoutImports = text => text.replace(/^import[\s\S]*?;\n/gm, '').replace(/^export /gm, '');
const section = (text, start, end) => text.slice(text.indexOf(start), text.indexOf(end)).replace(/^export /gm, '');

function gateHarness() {
  const saved = new Map();
  const sandbox = vm.createContext({
    document: { addEventListener() {} },
    sessionStorage: { getItem: key => saved.get(key), setItem: (key, value) => saved.set(key, value), removeItem: key => saved.delete(key) },
    createStore: (_name, model) => model,
    modelConfigStore: {}, onboardingStore: {},
  });
  const gate = vm.runInContext(withoutImports(source('webui/components/chat/model-gate-store.js')) + '\nstore;', sandbox);
  gate.start({ message: 'Old prompt', messageId: 'old', attachments: [], context: 'chat-a' });
  return { gate, saved, sandbox };
}

test('clear discards pending setup recovery and prevents a late readiness check from resending', async () => {
  const { gate, saved, sandbox } = gateHarness();
  let ready;
  gate.canSendToModel = () => new Promise(resolve => { ready = resolve; });
  sandbox.sendMessage = async () => assert.fail('cleared prompt was dispatched');
  const dispatch = gate.dispatchPendingIfConfigured();
  gate.resetContext('other-chat');
  assert.equal(saved.size, 1, 'resetting another chat discarded this pending prompt');
  gate.resetContext('chat-a');
  ready(true);
  await dispatch;
  assert.equal(gate.pending, null);
  assert.equal(gate.active, false);
  assert.equal(gate.connected, false);
  assert.equal(gate.gateMessageId, '');
  assert.equal(saved.size, 0);
  assert.equal(gate.syntheticMessages('chat-a').length, 0);

  gate.start({ message: 'Next', messageId: 'next', attachments: [], context: 'chat-a' });
  gate.pending = null;
  gate.connected = true;
  gate.resetContext('chat-a');
  assert.equal(gate.connected, false, 'old model-connected chip survived reset');
});

test('chat reset clears its gate only after the backend accepts the reset', async () => {
  const { gate } = gateHarness();
  const calls = [];
  const sandbox = vm.createContext({
    createStore: (_name, model) => model,
    getContext: () => 'chat-a', modelGateStore: gate,
    sendJsonData: async (...args) => { calls.push(args); throw Error('offline'); },
    toastFetchError() {},
  });
  const text = source('webui/components/sidebar/chats/chats-store.js');
  const chats = vm.runInContext(withoutImports(text.slice(0, text.indexOf('export { store };'))) + '\nstore;', sandbox);
  await chats.resetChat();
  assert.ok(gate.pending, 'failed reset lost the pending prompt');
  sandbox.sendJsonData = async (...args) => { calls.push(args); };
  await chats.resetChat();
  assert.equal(calls[1][0], '/chat_reset');
  assert.equal(calls[1][1].context, 'chat-a');
  assert.equal(gate.pending, null);
});

test('a changed log GUID drops cached history and setup state before replaying the new chat', async () => {
  const { gate } = gateHarness();
  const windowModule = await import('data:text/javascript;base64,' + Buffer.from(source('webui/js/message-window.js')).toString('base64'));
  const cache = new windowModule.MessageWindow();
  cache.merge([{ no: 0, id: 'old-history', type: 'user' }, ...gate.syntheticMessages('chat-a')]);
  let cleared = 0, resynced = 0;
  const history = { dataset: {}, replaceChildren() { cleared++; } };
  const sandbox = vm.createContext({
    context: 'chat-a', lastLogGuid: 'old-guid', lastLogVersion: 12, lastSpokenNo: 11,
    modelGateStore: gate, callJsExtensions: async () => {},
    document: { getElementById: () => history }, cancelPendingScroll() {},
    _messageRenderGeneration: 0, _messageWindow: cache, _massRender: false, _windowedRender: false,
    _scrollOnNextProcessGroup: null, _messageWindowFollowTail: false, _messageWindowLoadingDirection: null,
    _messageWindowSuppressScrollEvents: false, _messageWindowPointerActive: false, _messageWindowUserScrollUntil: 0,
    _messageWindowResizeObserver: null, _processGroupStepLimits: new Map(), _renderedProcessGroupPages: new Map(),
    chatsStore: { contexts: [] }, tasksStore: { tasks: [] },
    setMessages: async logs => cache.merge(logs), afterMessagesUpdate() {}, updateProgress() {},
    notificationStore: { updateFromPoll() {} }, inputStore: { applyPausedSnapshot() {} },
    messageQueueStore: { updateFromPoll() {} },
    finishChatLoading() {},
  });
  vm.runInContext(section(source('webui/js/messages.js'), 'export function resetMessageRenderState(', '\nfunction normalizeMessages('), sandbox);
  sandbox.msgs = { resetMessageRenderState: sandbox.resetMessageRenderState };
  vm.runInContext(section(source('webui/index.js'), 'export async function applySnapshot(', 'export async function poll('), sandbox);
  await sandbox.applySnapshot({ context: 'chat-a', log_guid: 'new-guid', log_version: 0, logs: [] }, {
    onLogGuidReset: async () => { resynced++; },
  });
  assert.equal(cache.size, 0);
  assert.equal(cleared, 1);
  assert.equal(gate.pending, null);
  assert.equal(sandbox.lastLogVersion, 0);
  assert.equal(sandbox.lastSpokenNo, 0);
  assert.equal(resynced, 1);
  await sandbox.applySnapshot({ context: 'chat-a', log_guid: 'new-guid', log_version: 3, logs: [
    { no: 0, id: 'new-user', type: 'user' },
    { no: 1, id: 'new-turn', type: 'agent' },
    { no: 2, id: 'new-turn', type: 'response' },
  ] });
  assert.equal(cache.size, 3);
  assert.ok(cache.visibleMessages().every(log => log.id.startsWith('new-')));
});

test('a root response completes its GEN group even when a model setup card is the DOM tail', () => {
  const renderKey = Symbol();
  const info = { id: 'turn', key: 'process:turn' };
  const badge = {};
  let shiny = true, response;
  const group = {
    dataset: {}, classList: { contains: () => false }, hasAttribute: () => false, getAttribute: () => null,
    querySelector: selector => selector === '.process-group-response' ? response
      : selector === '.process-group-header' ? { querySelector: name => name === '.step-badge' ? badge : null } : null,
    querySelectorAll: selector => selector === '.step-title.shiny-text'
      ? [{ classList: { remove: () => { shiny = false; } } }] : [],
  };
  const sandbox = vm.createContext({
    PROCESS_GROUP_RENDER_INFO: renderKey,
    getLastProcessGroup: () => null,
    getOrCreateProcessGroup: (_id, _allowComplete, received) => { assert.equal(received, info); return group; },
    getChatHistoryElementById: () => null,
    getOrCreateMessageContainer: () => assert.fail('response missed its GEN group'),
    ensureChild: parent => { assert.equal(parent, group); return response = {}; },
    preferencesStore: { detailMode: 'collapsed' }, _drawMessage: () => ({}),
    setupCollapsible() {}, isMassRender: () => false,
  });
  const text = source('webui/js/messages.js');
  vm.runInContext(section(text, 'export function drawMessageResponse(', 'export function drawMessageModelSetupGate(')
    + section(text, 'function updateProcessGroupHeader(', '// manually complete last process group'), sandbox);
  sandbox.drawMessageResponse({ id: 'response', content: '', [renderKey]: info });
  assert.equal(shiny, false);
  assert.match(badge.outerHTML, /END/);
});
