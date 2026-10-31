import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function setup() {
  const stores = new Map(), storage = {}, calls = [];
  const chats = { selected: '' };
  stores.set('chats', chats);
  const limits = { max_text_bytes: 100000, max_file_bytes: 1000000 };
  const listing = path => ({ ok: true, json: async () => ({ limits, data: {
    current_path: path, parent_path: '/', entries: [{ name: 'note.txt', path: `${path}/note.txt`, size: 1, type: 'text' }],
  } }) });
  let fetcher = async url => url.includes('limits=1')
    ? { ok: true, json: async () => ({ limits }) }
    : listing(new URL(url, 'http://local').searchParams.get('path'));
  let modal = false, closeModal;
  const document = Object.assign(new EventTarget(), {
    querySelector: () => null, querySelectorAll: () => [], activeElement: null,
  });
  const editor = { session: { path: '/folder/note.txt' }, openPath: async path => ({ path }) };
  const source = readFileSync(new URL('../webui/components/modals/file-browser/file-browser-store.js', import.meta.url), 'utf8')
    .replace(/^import\b[\s\S]*?;\n/gm, '')
    .replace(/export (const|function) /g, '$1 ')
    .replace('await import("/plugins/_editor/webui/editor-store.js")', '({ store: editor })');
  const context = vm.createContext({
    console, URL, setTimeout, clearTimeout, CustomEvent, FormData, File,
    requestAnimationFrame: callback => callback(), document, editor,
    localStorage: {
      getItem: key => storage[key] ?? null,
      setItem: (key, value) => { storage[key] = value; },
      removeItem: key => { delete storage[key]; },
    },
    createStore: (name, value) => { stores.set(name, value); value.init?.(); return value; },
    getStore: name => stores.get(name),
    createFileTree: (open, root) => ({ shown: false, open, getRoot: root, follow: async () => {} }),
    fetchApi: (...args) => fetcher(...args),
    callJsonApi: async () => ({ settings: { file_browser_remember_last_directory: true } }),
    formatDateTime: value => value,
    setupFloatingSurfaceModalChrome: () => { calls.push('floating'); return () => calls.push('cleanup'); },
    openLatestSurface: async (target, payload) => calls.push([target, payload?.path]),
    isModalOpen: () => modal,
    openModal: () => { modal = true; return new Promise(resolve => { closeModal = resolve; }); },
    ensureModalOpen: async () => {},
    closeModal: () => { calls.push('close'); modal = false; closeModal?.(); },
    toastFrontendError: message => calls.push(['error', message]),
  });
  vm.runInContext('const window = globalThis;\n' + source + '\nglobalThis.api = { store, createFileBrowserView };', context);
  return { ...context.api, chats, storage, calls, context, listing,
    fetch: fn => { fetcher = fn; }, setModal: value => { modal = value; } };
}

const settle = () => new Promise(setImmediate);

test('chat views keep navigation, selection and pending requests independent; shared mode is reversible', async () => {
  const t = setup();
  assert.equal(t.store.preferences.independent, true);
  t.chats.selected = 'a';
  const a = t.store.current;
  await t.store.navigateToFolder('/a');
  a.browser.entries[0].selected = true;
  let finish;
  t.fetch(() => new Promise(resolve => { finish = resolve; }));
  const pending = t.store.navigateToFolder('/a/next');
  t.chats.selected = 'b';
  const b = t.store.current;
  assert.notEqual(a, b);
  assert.equal(b.browser.currentPath, '');
  finish(t.listing('/a/next'));
  await pending;
  assert.equal(a.browser.currentPath, '/a/next');
  assert.equal(b.browser.currentPath, '');
  t.store.preferences.independent = false;
  const shared = t.store.current;
  t.chats.selected = 'a';
  assert.equal(t.store.current, shared);
  t.store.preferences.independent = true;
  assert.equal(t.store.current, a);
  assert.ok(a.history.includes('/a'));
  assert.equal(t.storage['fileBrowser.lastDirectory.a'], '/a/next');
  assert.equal(t.storage['fileBrowser.lastDirectory.b'], undefined);
});

test('Welcome shares preferences and limits while its navigation and callbacks remain separate', async () => {
  const t = setup();
  t.chats.selected = 'a';
  const main = t.store.current;
  const welcome = t.createFileBrowserView('welcome', { embedded: true, rememberKey: 'welcomeFiles.path' });
  assert.equal(welcome, t.createFileBrowserView('welcome'));
  await welcome.fileTree.open({ is_dir: true, path: '/welcome' });
  assert.equal(welcome.browser.currentPath, '/welcome');
  assert.equal(main.browser.currentPath, '');
  welcome.preferences.pathBar = 'raw';
  welcome.preferences.sortBy = 'size';
  await welcome.savePreferences();
  assert.equal(main.preferences, welcome.preferences);
  assert.equal(main.browser.sortBy, 'size');
  assert.equal(main.preferences.pathBar, 'raw');
  assert.equal(main.limits, welcome.limits);
  main._handleFileUpload = () => main.browser.currentPath;
  main.browser.currentPath = '/upload-a';
  const upload = t.store.handleFileUpload;
  t.chats.selected = 'b';
  assert.equal(await upload({}), '/upload-a', 'captured event handler stays on its originating chat');
  assert.equal(t.storage['welcomeFiles.path'], '/welcome');
});

test('embedded teardown cancels only its own listing and never configures modal chrome', async () => {
  const t = setup();
  const welcome = t.createFileBrowserView('welcome', { embedded: true });
  const host = { querySelector: () => null };
  welcome.onMount(host, { mode: 'embedded' });
  assert.equal(t.calls.includes('floating'), false);
  const main = t.store.current;
  main.pickerMode = 'text-open';
  const requests = [];
  t.fetch(() => new Promise(resolve => requests.push(resolve)));
  const w = welcome.fetchFiles('/late'), m = main.fetchFiles('/main');
  welcome.onUnmount(host);
  requests[0](t.listing('/late')); requests[1](t.listing('/main'));
  await Promise.all([w, m]);
  assert.equal(welcome.browser.currentPath, '');
  assert.equal(main.browser.currentPath, '/main');
  assert.equal(main.pickerMode, 'text-open');
});

test('Welcome file opening and inline creation never close an unrelated Files modal', async () => {
  const t = setup();
  const welcome = t.createFileBrowserView('welcome', { embedded: true });
  t.setModal(true);
  await welcome.openInSurface({ path: '/folder/note.txt' }, 'editor');
  assert.equal(t.calls.includes('close'), false);
  welcome.browser.currentPath = '/folder';
  welcome.configurePicker({ pickerMode: 'save-as', filename: 'new.txt', onConfirm: async () => true });
  await welcome.confirmPicker();
  assert.equal(welcome.pickerMode, '');
  assert.equal(t.calls.includes('close'), false);
});

test('external picker stays attached to its original chat until it closes', async () => {
  const t = setup();
  t.chats.selected = 'a';
  const a = t.store.current;
  const picker = t.store.openTextPicker('/pick');
  await settle();
  t.chats.selected = 'b';
  assert.equal(t.store.current, a);
  assert.equal(t.store.current.pickerMode, 'text-open');
  t.context.closeModal();
  await picker;
  assert.notEqual(t.store.current, a);
  assert.equal(t.store.current.pickerMode, '');
});

test('remote permissions and dropdowns belong to the view that loaded them', async () => {
  const t = setup();
  const a = t.store.current, b = t.createFileBrowserView('welcome', { embedded: true });
  a.browser.currentPath = '/@connections/ssh/a'; a.remotePermissions = { browse: true, delete: true };
  b.browser.currentPath = '/@connections/ssh/b'; b.remotePermissions = { browse: true };
  assert.equal(a.remoteAllowed('delete'), true);
  assert.equal(b.remoteAllowed('delete'), false);
  a.openDropdownPath = '/a'; b.openDropdownPath = '/b';
  b.closeDropdown();
  assert.equal(a.openDropdownPath, '/a');
});

test('a hidden canvas cannot replace modal ownership, and closing the modal restores the canvas', () => {
  const t = setup();
  const view = t.store.current;
  const canvas = { isConnected: true, querySelector: () => null };
  const modal = { isConnected: true, closest: () => modal, querySelector: () => null };
  view.onMount(modal);
  view.onMount(canvas, { mode: 'canvas' });
  assert.equal(view._mountedElement, modal);
  view.onUnmount(canvas);
  assert.equal(view._mountedElement, modal);
  view.onMount(canvas, { mode: 'canvas' });
  view.onUnmount(modal);
  assert.equal(view._mountedElement, canvas);
  view.onUnmount(canvas);
});

test('turning off remembered locations clears paths and prevents either view from saving new ones', () => {
  const t = setup();
  t.chats.selected = 'a';
  const main = t.store.current;
  const welcome = t.createFileBrowserView('welcome', { embedded: true, rememberKey: 'welcomeFiles.path' });
  main.rememberCurrentDirectory('/a'); welcome.rememberCurrentDirectory('/welcome');
  t.context.document.dispatchEvent(new CustomEvent('settings-updated', { detail: { file_browser_remember_last_directory: false } }));
  assert.equal(main.getRememberedDirectory(), '');
  assert.equal(welcome.getRememberedDirectory(), '');
  assert.equal(t.storage['fileBrowser.lastDirectory.a'], undefined);
  assert.equal(t.storage['welcomeFiles.path'], undefined);
  welcome.rememberCurrentDirectory('/not-saved');
  assert.equal(t.storage['welcomeFiles.path'], undefined);
});


test('uploads retain their selected destination and cannot replace a subsequently navigated folder', async () => {
  const t = setup();
  t.chats.selected = 'a';
  const a = t.store.current;
  a.browser.currentPath = '/upload';
  let finishLimits, finishUpload, destination;
  a.ensureLimits = () => new Promise(resolve => { finishLimits = resolve; });
  t.fetch((url, options) => {
    assert.equal(url, '/upload_work_dir_files');
    destination = options.body.get('path');
    return new Promise(resolve => { finishUpload = resolve; });
  });
  const input = { files: [new File(['hello'], 'test.txt')], value: 'selected' };
  const pending = t.store.handleFileUpload({ target: input });
  t.chats.selected = 'b';
  t.store.browser.currentPath = '/another-chat';
  a.browser.currentPath = '/next-folder';
  finishLimits({ max_file_bytes: 1000 });
  await settle();
  assert.equal(destination, '/upload');
  finishUpload(t.listing('/upload'));
  await pending;
  assert.equal(a.browser.currentPath, '/next-folder');
  assert.equal(t.store.browser.currentPath, '/another-chat');
  assert.equal(input.value, '');
});

test('an external rename prompt retains its initiating chat and callback', async () => {
  const t = setup();
  t.chats.selected = 'a';
  const a = t.store.current;
  let renamed;
  a.openRenameModal({ name: 'old.txt', path: '/origin/old.txt' }, {
    currentPath: '/origin', entries: [],
    performRename: async payload => { renamed = payload.path; return { refreshFiles: false }; },
  });
  a.renameName = 'new.txt';
  t.chats.selected = 'b';
  assert.equal(t.store.renameView, a);
  assert.notEqual(t.store.current, a);
  await t.store.renameView.confirmRename();
  assert.equal(renamed, '/origin/new.txt');
  a.releaseRenameModal();
  assert.equal(t.store.renameView, t.store.current);
  assert.equal(t.store.renameTarget, null);
});
