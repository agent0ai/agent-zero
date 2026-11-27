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
    .replace('await import("/plugins/_editor/webui/editor-store.js")', '({ store: editor })')
    .replaceAll('await import("/components/canvas/right-canvas-store.js")', '({ store: globalThis.canvas })');
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
    openSurface: async (target, payload) => calls.push([target, payload?.path]),
    selectSurface: async (target, payload) => calls.push([target, payload?.path]),
    isModalOpen: () => modal,
    openModal: () => { modal = true; return new Promise(resolve => { closeModal = resolve; }); },
    ensureModalOpen: async () => {},
    closeModal: () => { calls.push('close'); modal = false; closeModal?.(); },
    toastFrontendError: message => calls.push(['error', message]),
  });
  let closedPromise;
  context.canvas = {
    isOpen: false, isDetached: false, activeSurfaceId: '',
    async openModalSurface(id, payload) {
      this.isDetached = true; this.activeSurfaceId = id;
      if (!modal) closedPromise = context.openModal();
      await context.api.store.openSurface(payload.path, payload.options);
      return true;
    },
    whenClosed: () => closedPromise,
    async open(id, payload) {
      this.activeSurfaceId = id;
      if (payload) return await this.openModalSurface(id, payload);
      return true;
    },
    close() { this.isDetached = false; context.closeModal(); },
  };
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
  main.uploadFiles = (_files, path) => path;
  main.browser.currentPath = '/upload-a';
  const upload = t.store.handleFileUpload;
  t.chats.selected = 'b';
  assert.equal(await upload({ target: { files: [] } }), '/upload-a', 'captured event handler stays on its originating chat');
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

test('selection follows visible natural order and hidden rows cannot be acted on', () => {
  const { store } = setup();
  const view = store.current;
  const [last, first, middle, hidden] = view.browser.entries = ['file10', 'file1', 'file2', '.private']
    .map(name => ({ name, path: '/' + name, is_dir: false }));
  const names = entries => Array.from(entries, file => file.name);
  assert.deepEqual(names(view.visibleEntries), ['file1', 'file2', 'file10']);
  view.selectEntry(first);
  view.selectEntry(last, { shiftKey: true });
  assert.equal(view.selectedCount, 3);
  view.selectEntry(middle, { metaKey: true });
  assert.deepEqual(names(view.selectedFiles), ['file10', 'file1']);
  view.setFilter('10');
  assert.deepEqual(names(view.selectedFiles), ['file10']);
  view.setFilter('', true);
  view.selectEntry(hidden);
  view.setFilter('', false);
  assert.equal(view.selectedCount, 0);
});

test('a destination picker carries the original selection and blocks moves into descendants', async () => {
  const { store } = setup();
  const view = store.current;
  view.browser.currentPath = '/origin';
  view.browser.entries = [{name: 'folder', path: 'origin/folder', is_dir: true, selected: true}];
  view.chooseDestination('move');
  assert.equal(view.isPickerMode(), true);
  assert.equal(view.canConfirmPicker(), false);
  view.browser.currentPath = '/origin/folder/inside';
  assert.equal(view.canConfirmPicker(), false);
  view.browser.currentPath = '/another';
  let transferred;
  view.transferFiles = async (paths, directory, action) => { transferred = [Array.from(paths), directory, action]; return true; };
  await view.confirmPicker();
  assert.deepEqual(transferred, [['/origin/folder'], '/another', 'move']);
  assert.equal(view.isPickerMode(), false);
});

test('explicit sorting cycles across folders and files before restoring the saved order', () => {
  const { store } = setup();
  const view = store.current;
  view.browser.entries = [{name: 'z', is_dir: true, size: 0}, {name: 'a', is_dir: false, size: 10}];
  const names = () => Array.from(view.visibleEntries, entry => entry.name);
  assert.deepEqual(names(), ['z', 'a']);
  view.toggleSort('name');
  assert.deepEqual(names(), ['a', 'z']);
  view.toggleSort('name');
  assert.deepEqual(names(), ['z', 'a']);
  view.toggleSort('name');
  assert.equal(view.browser.explicitSort, false);
});

test('the Files template keeps drop listeners alive until its host is destroyed', async () => {
  const dir = new URL('../webui/components/modals/file-browser/', import.meta.url);
  const html = readFileSync(new URL('file-browser.html', dir), 'utf8');
  const setup = html.match(/x-create="([^"]*fb\.mountGestures[^"]*)"/)[1];
  const teardown = html.match(/x-destroy="([^"]*_endGestures[^"]*)"/)[1];
  const { mountFileGestures } = await import(new URL('file-gestures.js', dir));
  const host = Object.assign(new EventTarget(), {
    dataset: {}, closest: selector => selector === '.file-browser-root' ? host : null,
    querySelector: () => null,
  });
  const accepted = [];
  const view = {
    mountGestures: mountFileGestures, browser: {currentPath: '/destination'},
    isPickerMode: () => false, remoteAllowed: () => true,
    uploadDrop: (data, path) => accepted.push(path),
  };
  function evaluate(expression) {
    const result = Function('$el', 'fb', 'return ' + expression)(host, view);
    // Alpine also evaluates a function returned from a directive expression.
    if (typeof result === 'function') result();
  }
  function drop() {
    host.dispatchEvent(Object.assign(new Event('drop', { cancelable: true }), {
      dataTransfer: { types: ['Files'] },
    }));
  }
  evaluate(setup);
  drop();
  view.isPickerMode = () => true;
  drop();
  evaluate(teardown);
  view.isPickerMode = () => false;
  drop();
  assert.deepEqual(accepted, ['/destination']);
});

test('a queued close event cannot abort a newly opened media preview', () => {
  const html = readFileSync(new URL('../webui/components/modals/file-browser/file-browser.html', import.meta.url), 'utf8');
  const close = html.match(/<dialog [^>]*files-media-dialog[^>]*@close="([^"]+)"/)[1];
  const onClose = Function('$el', 'clear', close);
  const request = new AbortController();
  const release = () => request.abort();
  onClose({ open: true }, release);
  assert.equal(request.signal.aborted, false);
  onClose({ open: false }, release);
  assert.equal(request.signal.aborted, true);
});

test('Properties combines shared and mixed values and totals selected files', () => {
  const fb = setup().store.current;
  const first = {name: 'a', path: '/work/a', size: 12, uid: 0, mode: '640'};
  const second = {name: 'b', path: '/work/b', size: 15, uid: 0, mode: '600'};
  const summary = fb.summarizeProperties([first, second]);
  assert.equal(summary.rows.Name, '2 items');
  assert.equal(summary.rows.Location, '/work');
  assert.equal(summary.rows.UID, 0);
  assert.equal(summary.mode, 'Multiple');
  assert.equal(summary.size, 27);
  const folder = fb.summarizeProperties([first, {...second, is_dir: true}]);
  assert.equal(folder.rows.Type, 'Multiple');
  assert.equal(folder.size, null);
  assert.equal(folder.canMeasure, true);
  assert.equal(fb.summarizeProperties([{...first, is_symlink: true}]).editable, false);
});
