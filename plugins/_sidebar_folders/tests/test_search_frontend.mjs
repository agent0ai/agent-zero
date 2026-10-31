import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

function setup() {
  const pending = [], selected = [], errors = [];
  const contexts = [{id:'parent',name:'Parent',project:{name:'project'}}, {id:'child',parent_context_id:'parent'}, {id:'other',name:'Other'}];
  const task = {id:'task',task_name:'Daily report'};
  const source = readFileSync(new URL('../webui/sidebar-folders-store.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '').replace('export const store', 'const store');
  const chats = {contexts,displayName:row=>row.name || row.id,selectChat:id=>selected.push(['chat',id])};
  const tasks = {tasks:[task],selectTask:id=>selected.push(['task',id])};
  const store = vm.runInNewContext(`${source}\nstore`, {
    createStore:(_,value)=>value,
    callJsonApi:(url)=>url.endsWith('/search') ? new Promise((resolve,reject)=>pending.push({resolve,reject})) : Promise.resolve({ok:true}),
    toastFrontendError:message=>errors.push(message), chats, tasks,
    sidebar:{unregisterRowListExtension(){}}, projects:{projectList:[{name:'project',title:'Project'}]},
    pins:{isPinned:()=>false,isProjectPinned:()=>false,sortItems:(_,rows)=>rows},
    document:{activeElement:null},clearTimeout,console,
  });
  chats.topLevelContexts=()=>store.sortRows('chat',contexts.filter(row=>!row.parent_context_id));
  tasks.visibleTasks=()=>store.sortRows('task',tasks.tasks);
  return {store,pending,selected,errors,contexts,task};
}

test('one query matches chat descendants and task logs without filtering Welcome sections',async()=>{
  const {store,pending,contexts,task,selected}=setup();
  const original=store.sections('chat');
  store.searchQuery='needle';const request=store.search();
  pending[0].resolve({matches:[{id:'child',title:true,parts:[{text:'needle child',match:true}]},{id:'task',title:false,parts:[{text:'needle output',match:true}]}]});await request;
  assert.equal(store.sections('chat',null,true)[0].rows[0].id,'parent');
  assert.equal(store.sections('task',null,true)[0].rows[0].id,'task');
  assert.equal(store.sections('chat',original),original);
  assert.equal(store.isOpen('chat','project'),false,'search does not save folder expansion');
  store.openSearchMatch(contexts[0],'chat');store.openSearchMatch(task,'task');
  assert.deepEqual(selected,[['chat','child'],['task','task']]);
  store.config.folder_view=false;
  assert.equal(store.sections('chat',null,true)[0].pinned,true,'flat search results use the shared rows without folder headings');
  store.config.project_filter='missing';
  assert.equal(store.sections('chat',null,true).length,0,'existing filters still apply');
});

test('stale queries, clearing, and unmounting cannot restore old search matches',async()=>{
  const {store,pending}=setup();
  store.searchQuery='old';const old=store.search();
  store.searchQuery='new';const current=store.search();
  pending[1].resolve({matches:[{id:'other',title:false,parts:[{text:'new',match:true}]}]});await current;
  pending[0].resolve({matches:[{id:'parent',title:false,parts:[{text:'old',match:true}]}]});await old;
  assert.equal(store.searchResults.other.parts[0].text,'new');
  store.searchQuery='typing';assert.equal(store.searchMatch({id:'other'},'chat'),null,'typing hides stale excerpts before debounce');
  const late=store.search();store.clearSearch();
  pending[2].resolve({matches:[{id:'parent',title:false,parts:[{text:'late',match:true}]}]});await late;
  assert.equal(Object.keys(store.searchResults).length,0);
  assert.equal(store.searchPending,false);
  store.searchQuery='unmounted';const unmounted=store.search();store.unmountList('chat');
  pending[3].resolve({matches:[{id:'parent',title:false,parts:[{text:'late',match:true}]}]});await unmounted;
  assert.equal(store.searchActive,false);
  assert.equal(Object.keys(store.searchResults).length,0);
});

test('No search clears results and late failures cannot disturb a newer query',async()=>{
  const {store,pending,errors}=setup();
  store.searchQuery='old';const old=store.search();store.searchQuery='new';
  pending[0].reject(new Error('old failure'));await old;
  assert.equal(errors.length,0);
  await store.setConfig({search_mode:'none'});
  assert.equal(store.searchQuery,'');assert.equal(store.searchActive,false);
  await store.search();assert.equal(pending.length,1,'hidden search never requests data');
});
