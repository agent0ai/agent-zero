import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const ok = data => ({results:[{ok:true, data}]});
const idle = {state:'idle', stage:'idle', pending:false, step:null, steps:6};
const ready = {...idle, state:'ready', stage:'ready', step:6};
const empty = {context_id:'fixture', browsers:[], active_browser_id:null};
const visible = {...empty, browsers:[{id:1, context_id:'fixture'}], active_browser_id:1,
  viewer_transport:'interactive', interactive_view:{available:true, url:'/fixture-viewer'}, result:{id:1}};
const deferred = () => { let resolve, reject; const promise = new Promise((yes,no) => {resolve=yes; reject=no;}); return {promise,resolve,reject}; };
const flush = () => new Promise(resolve => setImmediate(resolve));

function setup(request, rightCanvasStore = {}) {
  const timers = new Map(); let nextTimer = 0;
  const websocket = {addHandlers() {}, request};
  const source = readFileSync(new URL('../plugins/_browser/webui/browser-store.js', import.meta.url), 'utf8')
    .replace(/^import [\s\S]*?;\n/gm, '').replace('export const store', 'const store');
  const model = vm.runInNewContext(source+'\nmodel;', {
    getNamespacedClient:()=>websocket, createStore:(_, model)=>model,
    registerUrlHandler() {}, console, Error, rightCanvasStore,
    setTimeout(fn) {const id=++nextTimer;timers.set(id,fn);return id;},
    clearTimeout(id) {timers.delete(id);},
  });
  Object.assign(model, {
    loading:false, contextId:'fixture',
    _bindSocketEvents:async()=>{}, currentViewportSize:()=>({width:800,height:600}),
    captureDevicePixelRatio:()=>1, supportsBinaryFrames:()=>false,
    contextIdForNewBrowser:async()=> 'fixture', contextIdForActiveBrowser:async()=> 'fixture',
  });
  for(const name of ['applyActiveFrameState','applySnapshot','cancelAnnotationDraft','clearAnnotationHover']) model[name]=()=>{};
  return {model,timers, async recoveryTick() {
    const entry=[...timers].find(([,fn])=>fn.name !== 'poll');
    assert.ok(entry,'Expected pending recovery, not a second launch');
    timers.delete(entry[0]);entry[1]();await flush();
  }};
}

test('checking an empty session never pretends a ready dependency worker is launching Chromium', async () => {
  const pending=deferred();
  const {model,timers}=setup(async event => event==='browser_startup_status' ? ok({startup:ready}) : pending.promise);
  const connecting=model.connectViewer({contextId:'fixture'});
  await flush();
  assert.equal(model.browserLoadingLabel(),'Checking existing browser session…');
  assert.equal(model.isBusy(),true);
  assert.equal(model.browserStartupDetail(),'');
  pending.resolve(ok(empty));await connecting;
  assert.equal(model.isBusy(),false);
  assert.equal(model.activeBrowserId,null);
  assert.equal(timers.size,0);
});

test('first launch stays busy through all numbered stages and rejects duplicate clicks', async () => {
  const pending=deferred();let opens=0;let progress=idle;const deadlines=[];
  const {model,timers}=setup(async (event,data,options)=>{
    if(event==='browser_startup_status')return ok({startup:progress});
    if(event==='browser_viewer_subscribe')return ok(visible);
    opens++;deadlines.push(options.timeoutMs);return pending.promise;
  });
  const launching=model.command('open');await flush();
  await model.command('open');assert.equal(opens,1);
  for(let step=1;step<=6;step++) {
    progress={state:'starting',pending:true,step,steps:6,message:'Actual stage '+step};
    await model.refreshStartupProgress();
    assert.equal(model.browserLoadingLabel(),`${step}/6 Actual stage ${step}…`);
    assert.equal(model.isBusy(),true);
    assert.equal(model.browserStartupDetail(),'Running the web browser for the first time will take a little while to install dependencies.');
  }
  pending.resolve(ok(visible));await launching;
  assert.equal(model.activeBrowserId,1);assert.equal(model.hasFrame(),true);
  assert.equal(model.isBusy(),false);assert.equal(timers.size,0);
  assert.equal(deadlines[0],2100000);
  await model.command('open');assert.equal(deadlines[1],45000);
});

test('lost launch acknowledgement keeps busy until the server finishes, then attaches without reopening', async () => {
  const pending=deferred();let opens=0;let subscriptions=0;
  let progress={state:'starting',pending:true,stage:'browser',step:5,steps:6,message:'Launching Chromium'};
  const {model,timers,recoveryTick}=setup(async event=>{
    if(event==='browser_startup_status')return ok({startup:progress});
    if(event==='browser_viewer_subscribe'){subscriptions++;return ok(visible);}
    opens++;return pending.promise;
  });
  const launching=model.command('open');await flush();
  pending.reject(new Error('Request timeout'));await flush();
  assert.equal(model._startupRecovering,true);
  assert.equal(model.isBusy(),true);
  assert.equal(model.error,'');
  await model.command('open');assert.equal(opens,1);
  // Chromium can be ready before tab creation and the original request finish.
  progress={...ready,pending:true};await recoveryTick();
  assert.equal(model.isBusy(),true);assert.equal(subscriptions,0);
  progress=ready;await recoveryTick();await launching;
  assert.equal(subscriptions,1);assert.equal(opens,1);
  assert.equal(model.activeBrowserId,1);assert.equal(model.hasFrame(),true);
  assert.equal(model.isBusy(),false);assert.equal(model.error,'');
  assert.equal(timers.size,0);
});

test('server-confirmed failures expose retry only after startup finishes', async () => {
  let opens=0;
  const {model}=setup(async event=>{
    if(event==='browser_startup_status')return ok({startup:idle});
    opens++;return {results:[{ok:false,error:{error:'Chromium launch failed'}}]};
  });
  await model.command('open');
  assert.equal(model.error,'Chromium launch failed');
  assert.equal(model.isBusy(),false);assert.equal(model.activeBrowserId,null);
  assert.equal(opens,1);
});

test('an unavailable status connection never makes an unconfirmed launch look stopped', async () => {
  let calls=0;const pending=deferred();
  const {model,recoveryTick}=setup(async event=>{
    if(event==='browser_startup_status') {if(++calls>1)throw new Error('offline');return ok({startup:idle});}
    return pending.promise;
  });
  const launching=model.command('open');await flush();
  pending.reject(new Error('Request timeout'));await flush();
  assert.equal(model.isBusy(),true);
  assert.match(model.browserStartupDetail(),/Reconnecting/);
  // Leaving the context invalidates recovery and any late progress response.
  model._contextSequence++;model.stopStartupPolling();model.commandInFlight=false;
  await recoveryTick();await launching;
  assert.equal(model.isBusy(),false);assert.equal(model.error,'');
});

test('recovery reports confirmed failure without relaunching', async () => {
  let opens=0;
  const {model}=setup(async event=>{
    if(event==='browser_startup_status')return ok({startup:{state:'error',pending:false,message:'Display failed'}});
    opens++;throw new Error('Request timeout');
  });
  await model.command('open');
  assert.equal(opens,1);assert.equal(model.error,'Display failed');
  assert.equal(model.isBusy(),false);
});

test('a late recovery subscription cannot set an error in another context', async () => {
  const pending=deferred();let subscribing=false;
  const {model}=setup(async event=>{
    if(event==='browser_startup_status')return ok({startup:ready});
    if(event==='browser_viewer_subscribe'){subscribing=true;return pending.promise;}
    throw new Error('Request timeout');
  });
  const launching=model.command('open');await flush();
  assert.equal(subscribing,true);
  model._contextSequence++;model._connectSequence++;model.stopStartupPolling();
  model.commandInFlight=false;model.error='';
  pending.resolve(ok(empty));await launching;
  assert.equal(model.isBusy(),false);assert.equal(model.error,'');
});

test('nested polling and late responses cannot clear another launch state', async () => {
  let reply;const {model,timers}=setup(()=>new Promise(resolve=>{reply=resolve;}));
  const stopFirst=model.startStartupPolling();const stopNested=model.startStartupPolling();
  const oldReply=reply;
  stopNested();assert.equal(model._startupPollUsers,1);
  stopFirst();const stopNew=model.startStartupPolling();
  oldReply(ok({startup:{state:'error',message:'old failure'}}));await flush();
  assert.equal(model.startupProgress,null);assert.equal(model.isBusy(),true);
  reply(ok({startup:{state:'starting',step:2,steps:6,message:'Installing Chromium dependencies'}}));await flush();
  assert.equal(model.browserLoadingLabel(),'2/6 Installing Chromium dependencies…');
  assert.equal(timers.size,1);stopNew();assert.equal(timers.size,0);
});

test('an inactive Browser panel with layout cannot open and create a chat', async () => {
  let active = false;
  const canvas = {isSurfaceVisible: id => active && id === 'browser'};
  const {model} = setup(async () => assert.fail('Unexpected startup request'), canvas);
  const panel = {
    isConnected: true,
    closest: () => ({}),
    getBoundingClientRect: () => ({width: 800, height: 600}),
  };
  let opens = 0;
  model.openSurface = async () => { opens++; };
  await model.onOpen(panel, {mode: 'canvas'});
  assert.equal(opens, 0);
  active = true;
  await model.onOpen(panel, {mode: 'canvas'});
  assert.equal(opens, 1);
});

test('closing a tab in Chromium retains the connected viewer until the final tab closes', async () => {
  const {model} = setup(async () => ok(visible));
  await model.connectViewer({contextId:'fixture'});
  model.applyBrowserListing([{id:2, visible:true}], 'fixture', {replaceAll:true});
  assert.equal(model.activeBrowserId, 2);
  assert.equal(model.interactiveViewUrl, '/fixture-viewer');
  model.applyBrowserListing([], 'fixture', {replaceAll:true});
  assert.equal(model.activeBrowserId, null);
  assert.equal(model.interactiveViewUrl, '');
});

test('window buttons follow each window’s selected tab and count its open tabs', () => {
  const {model} = setup();
  const brief = {id:1, window_id:10, title:'Project brief', visible:true};
  const notes = {id:2, window_id:10, title:'Notes', visible:false};
  const reference = {id:3, window_id:20, title:'Reference', visible:true};
  const labels = () => Array.from(model.browserWindows(), ({tab, count}) => [tab.title, count]);
  model.browsers = [brief, reference, notes];
  assert.deepEqual(labels(), [['Project brief', 2], ['Reference', 1]]);
  brief.visible = false;
  notes.visible = true;
  assert.deepEqual(labels(), [['Notes', 2], ['Reference', 1]]);
  model.browsers = [reference, notes];
  assert.deepEqual(labels(), [['Reference', 1], ['Notes', 1]]);
});
