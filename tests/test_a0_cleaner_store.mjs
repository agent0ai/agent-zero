import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const report = { id: 'scan-one', at: Date.now()/1000, groups: [
  {id:'pip',automatic:true,auto_supported:true,files:1,bytes:1024},
  {id:'profiles',automatic:false,auto_supported:true,files:2,bytes:2048},
  {id:'embeddings',automatic:false,auto_supported:false,files:3,bytes:4096},
], bytes:7168 };
const config = {automatic:true,automatic_areas:['pip'],custom_folders:[]};

function load(api) {
  const source=readFileSync(new URL('../plugins/_a0_cleaner/webui/cleaner-store.js', import.meta.url),'utf8')
    .replace(/^import .*;\n/gm,'').replace('export const store','const store');
  return vm.runInNewContext(`${source}\nstore`, {createStore:(_,value)=>value, callJsonApi:api,
    schedulerStore:{fetchTasks:async()=>{},showTaskDetail:()=>{}},setTimeout,clearTimeout,console});
}

test('scan selects only enabled automatic areas and never cleans', async()=>{
  const calls=[];
  const store=load(async(_path,data)=>{
    calls.push(data.action);
    return data.action==='scan'?{ok:true,report:structuredClone(report)}:
      {ok:true,report:structuredClone(report),activity:[],scheduled:null,schedule:null,config,status:{}};
  });
  await store.scan();
  assert.deepEqual(calls,['scan','status']);
  assert.equal(store.selected.join(','),'pip');
  assert.equal(store.selectedBytes(),1024);
  assert.equal(store.groups(true).length,2);
});

test('review does not delete and confirmation uses the frozen preview selection',async()=>{
  const calls=[];
  const store=load(async(_path,data)=>{
    calls.push(data);
    if(data.action==='preview')return {ok:true,preview:{id:'scan-one',groups:[report.groups[1]],files:2,bytes:2048}};
    if(data.action==='clean')return {ok:true,result:{bytes:2048,skipped:0},report:{...report,id:'scan-two'}};
    return {ok:true,report:{...report,id:'scan-two'},activity:[],config,status:{}};
  });
  store.applyReport(structuredClone(report)); store.selected=['profiles'];
  await store.review();
  assert.equal(calls.length,1); assert.equal(calls[0].action,'preview');
  store.selected=['pip'];
  await store.clean();
  const clean=calls.find(c=>c.action==='clean');
  assert.equal(clean.confirmed,true);assert.equal(clean.groups.join(','),'profiles');
  assert.equal(clean.scan_id,'scan-one');
});

test('area opt-outs persist without changing the master switch',async()=>{
  let saved;
  const store=load(async(_path,data)=>{
    if(data.action==='settings'){saved=data.settings;return {ok:true,config:saved};}
    return {ok:true,report:structuredClone(report)};
  });
  store.config=structuredClone(config);
  await store.automaticAreaChanged('pip',false);
  assert.equal(saved.automatic,true);assert.equal(saved.automatic_areas.length,0);
});

test('closing during a status request ignores its late response',async()=>{
  let resolve;
  const store=load(()=>new Promise(done=>resolve=done));
  const pending=store.refresh();store.unmount();
  resolve({ok:true,report,activity:[],config,status:{}});
  await pending; assert.equal(store.report,null);
});

test('opening confirmation again after a new scan cannot reuse stale preview',()=>{
  const store=load(async()=>({ok:true}));
  store.applyReport(structuredClone(report));store.preview={id:'scan-one'};
  store.applyReport({...structuredClone(report),id:'scan-two'});
  assert.equal(store.preview,null);
});

test('a delayed older report cannot replace a completed scan',()=>{
  const store=load(async()=>({ok:true}));
  store.applyReport({...structuredClone(report),id:'new',at:200});
  store.applyReport({...structuredClone(report),id:'old',at:100});
  assert.equal(store.report.id,'new');
});
