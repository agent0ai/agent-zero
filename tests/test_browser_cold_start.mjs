import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

test('empty subscription keeps install budget for the first open; warm commands stay bounded', async () => {
  const calls = [];
  let active = null;
  const websocket = {
    addHandlers() {},
    async request(event, payload, options) {
      calls.push({event, options});
      if (event === 'browser_viewer_command') throw Error('fixture end');
      return {results:[{ok:true, data:{browsers:[], active_browser_id:active}}]};
    },
  };
  const source = readFileSync(new URL('../plugins/_browser/webui/browser-store.js', import.meta.url), 'utf8')
    .replace(/^import [\s\S]*?;\n/gm, '').replace('export const store', 'const store');
  const model = vm.runInNewContext(source + '\nmodel;', {
    getNamespacedClient: () => websocket, createStore: (_, model) => model,
    registerUrlHandler() {}, console, setTimeout, clearTimeout,
  });
  for (const name of ['applyTabScope','applyBrowserListing','applyViewer','applyActiveFrameState','applySnapshot']) model[name]=()=>{};
  model._bindSocketEvents=async()=>{};
  model.currentViewportSize=()=>({width:800,height:600});
  model.requestedViewerTransport=()=> 'interactive';
  model.supportsBinaryFrames=()=>false;
  model.captureDevicePixelRatio=()=>1;
  model.browserById=()=>null;
  model.setActiveBrowserId=id=>{model.activeBrowserId=id;};
  model.contextIdForNewBrowser=async()=> 'fixture';
  model.contextIdForActiveBrowser=async()=> 'fixture';
  model.browserInstallExpected=true;
  await model.connectViewer({contextId:'fixture'});
  assert.equal(model.browserInstallExpected,true);
  await model.command('open',{url:'about:blank'});
  assert.equal(calls.at(-1).options.timeoutMs,1800000);
  active=1;
  await model.connectViewer({contextId:'fixture'});
  assert.equal(model.browserInstallExpected,false);
  await model.command('open',{url:'about:blank'});
  assert.equal(calls.at(-1).options.timeoutMs,45000);
});

test('startup polling reports stages, shares nested requests and ignores late replies after cleanup', async () => {
  const timers = new Map();
  let now = 10000;
  let nextTimer = 0;
  let reply;
  let requests = 0;
  const websocket = {
    addHandlers() {},
    request(event) {
      assert.equal(event, 'browser_startup_status');
      requests += 1;
      return new Promise(resolve => { reply = resolve; });
    },
  };
  const source = readFileSync(new URL('../plugins/_browser/webui/browser-store.js', import.meta.url), 'utf8')
    .replace(/^import [\s\S]*?;\n/gm, '').replace('export const store', 'const store');
  const model = vm.runInNewContext(source + '\nmodel;', {
    getNamespacedClient: () => websocket, createStore: (_, model) => model,
    registerUrlHandler() {}, console,
    Date: class extends Date { static now() { return now; } },
    setTimeout(fn) { const id = ++nextTimer; timers.set(id, fn); return id; },
    clearTimeout(id) { timers.delete(id); },
  });
  model.loading = true;
  const stopFirst = model.startStartupPolling();
  const stopNested = model.startStartupPolling();
  assert.equal(requests, 1);
  assert.equal(model.browserStartupDetail(), '0s elapsed');
  reply({results:[{ok:true, data:{startup:{state:'starting', stage:'chromium',
    message:'Downloading Chromium', elapsed_seconds:70, quiet_seconds:35}}}]});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(model.browserLoadingLabel(), 'Downloading Chromium');
  assert.match(model.browserStartupDetail(), /0s elapsed.*35s/);
  assert.equal(timers.size, 2);
  stopNested();
  assert.equal(timers.size, 2);
  const poll = timers.get(model._startupPollTimer);
  timers.delete(model._startupPollTimer);
  const pending = poll();
  const oldReply = reply;
  // A slow/missing status reply must not freeze the launch clock.
  const tick = timers.get(model._startupClockTimer);
  timers.delete(model._startupClockTimer);
  now += 2500;
  tick();
  assert.match(model.browserStartupDetail(), /^2s elapsed/);
  stopFirst();
  assert.equal(model.startupProgress, null);
  assert.equal(model.browserStartupDetail(), '');
  assert.equal(timers.size, 0);
  const stopNew = model.startStartupPolling();
  assert.equal(model.browserStartupDetail(), '0s elapsed');
  const currentReply = reply;
  oldReply({results:[{ok:true,data:{startup:{state:'error', message:'old failure'}}}]});
  await pending;
  stopFirst();
  assert.equal(model._startupPollUsers, 1);
  assert.equal(model.startupProgress, null);
  currentReply({results:[{ok:true,data:{startup:{state:'ready', elapsed_seconds:140, quiet_seconds:90}}}]});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(model.browserLoadingLabel(), 'Starting Chromium…');
  assert.equal(model.browserStartupDetail(), '0s elapsed');
  const currentTick = timers.get(model._startupClockTimer);
  timers.delete(model._startupClockTimer);
  now += 1000;
  currentTick();
  tick(); // A stale tick from the previous launch cannot overwrite the new clock.
  assert.equal(model.browserStartupDetail(), '1s elapsed');
  model.stopStartupPolling();
  stopNew();
  assert.equal(model.startupProgress, null);
  assert.equal(timers.size, 0);
});
