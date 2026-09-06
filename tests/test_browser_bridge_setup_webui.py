from __future__ import annotations
import re
import shutil
import pytest
from pathlib import Path
from browser_bridge_test_support import run_model, run_node


def test_os_links_stay_scoped_and_unverified_metadata_never_means_ready():
    run_model("browser-bridge-setup-store.js", r'''
import assert from "node:assert/strict";
assert.equal(browserHostPlatform({platform:"MacIntel"}),"macos");
assert.equal(browserHostPlatform({userAgentData:{platform:"Windows"}}),"windows");
assert.equal(browserHostPlatform({platform:"Linux x86_64"}),"linux");
assert.equal(browserHostPlatform({platform:"Linux",userAgent:"Android"}),"");
const setup={contract:"a0.browser-bridge.setup.v1",setup_enabled:true,browser_control_ready:false,
 install_target:"browser_host",host_verification_required:true,extension_id:"a".repeat(32),
 extension_url:"https://chromewebstore.google.com/detail/"+"a".repeat(32),companion_version:"2.12.0",
 installers:[{platform:"macos",arch:"universal2",url:"https://releases.example.test/bridge.dmg"}]};
const calls=[];
const model=createBrowserSetupModel({platform:"macos",api:async(_,body)=>{calls.push(body);return setup;}});
await model.mount();assert.deepEqual(calls,[{}]);assert.equal(model.installers().length,1);
model.platform="windows";assert.equal(model.installers().length,0);assert.match(model.availabilityText(),/No Windows/);
model.platform="linux";assert.equal(model.installers().length,0);assert.match(model.availabilityText(),/No Linux/);
for (const invalid of [{...setup,browser_control_ready:true},{...setup,setup_enabled:false},
 {...setup,extension_url:"https://example.test"},{...setup,installers:[{...setup.installers[0],url:"javascript:alert(1)"}]},
 {...setup,installers:[...setup.installers,...setup.installers]}]) assert.throws(()=>parseSetup(invalid));
model.cleanup();assert.equal(model.setup,null);
''')


def test_setup_closed_panel_discards_async_response():
    run_model("browser-bridge-setup-store.js", r'''
import assert from "node:assert/strict";
let finish;const model=createBrowserSetupModel({api:()=>new Promise(resolve=>finish=resolve)});
const request=model.mount();model.cleanup();finish({});await request;
assert.equal(model.setup,null);assert.equal(model.state,"not_checked");
''')


def test_alpine_store_registration_does_not_start_pairing_without_modal_config():
    source = (Path(__file__).resolve().parents[1] / "plugins/_browser/webui/browser-config-store.js").read_text()
    source = re.sub(r"^import .*;\n", "", source, flags=re.M).replace("export const store =", "const store =")
    script = "const createStore=(_,model)=>model; const callJsonApi=()=>{throw Error('Unexpected API call')};\n" + source
    script += "\nawait store.init(); if(store.pairingPanelActive || store.pairingStatusLoading)throw Error('Registration started pairing');"
    run_node(script)


ROOT = Path(__file__).resolve().parents[1]


def test_selection_readback_respects_modal_scope_and_preserves_unrelated_drafts():
    run_model("browser-bridge-selection-store.js", r'''
import assert from "node:assert/strict";
const modal={pluginName:"_browser",projectName:"",agentProfileKey:"",
 settings:{runtime_backend:"container",host_browser_selection:"",proxy_server:"unsaved"}};
const calls=[];
const api=async(endpoint,body)=>{calls.push({endpoint,body});return {ok:true,data:{
 runtime_backend:body.project_name?"host_required":"container",
 host_browser_selection:body.project_name?"extension:bridge-1":"",proxy_server:"stored"}};};
await refreshBrowserSettingsScope(api,modal,()=>true);
assert.equal(modal.settings.runtime_backend,"container");
assert.equal(modal.settings.host_browser_selection,"");
assert.equal(modal.settings.proxy_server,"unsaved");
assert.deepEqual(calls[0],{endpoint:"/plugins",body:{action:"get_config",plugin_name:"_browser",project_name:"",agent_profile:""}});
modal.projectName="project-1";await refreshBrowserSettingsScope(api,modal,()=>true);
assert.equal(modal.settings.host_browser_selection,"extension:bridge-1");
let resolve;const pending=refreshBrowserSettingsScope(()=>new Promise(done=>resolve=done),modal,()=>true);
modal.projectName="project-2";modal.settings={runtime_backend:"container",host_browser_selection:""};
resolve({ok:true,data:{runtime_backend:"host_required",host_browser_selection:"extension:stale"}});
await pending;assert.equal(modal.settings.host_browser_selection,"");
await refreshBrowserSettingsScope(api,modal,()=>false);assert.equal(calls.length,2);
''')


def test_selection_status_is_read_only_and_changes_require_exact_readback():
    run_model("browser-bridge-selection-store.js", r'''
import assert from "node:assert/strict";
let bridge = null, wrong = false;
const calls = [], notices = [], updates = [];
const reply = (chat=false) => ({contract:chat?"a0.browser-bridge.selection.v1":"a0.browser-bridge.default-selection.v1",...(chat?{context_id:"chat-1"}:{}),
 bridge_id:bridge,selected:bridge !== null,browser_control_ready:false,reconnect_required:bridge !== null});
const model = createBridgeSelectionModel({context:()=>"chat-1",confirm:async()=>true,
 notify:(...v)=>notices.push(v),onSelected:v=>updates.push(v),api:async(_,body)=>{
 calls.push(body);if(body.action === "use_default")bridge = wrong ? "other" : body.bridge_id;
 if(body.action === "clear_default")bridge = null;return reply(body.action === "status");}});
const modal = {settings:{proxy_server:"unsaved"}};
await model.mount(modal);
assert.deepEqual(calls,[{action:"default_status"},{action:"status",context_id:"chat-1"}]);
assert.equal(updates.length,0);assert.equal(model.selection.ready,false);
await model.useBrowser("browser-1");
assert.deepEqual(calls.at(-2),{action:"use_default",bridge_id:"browser-1",expected_bridge_id:null});
assert.equal(model.selectedHere("browser-1"),true);assert.deepEqual(updates,[modal]);
assert.equal(model.selectedDefault("browser-1"),true);
await model.clear();
assert.deepEqual(calls.at(-2),{action:"clear_default",expected_bridge_id:"browser-1"});
assert.equal(model.selection.selected,false);
wrong=true;await model.useBrowser("browser-2");
assert.equal(model.defaultSelection,null);assert.equal(model.state,"unavailable");
assert.equal(updates.length,2);assert.equal(notices.at(-1)[0],"error");
model.cleanup();
''')


def test_readiness_timer_is_read_only_visible_nonoverlapping_and_cleanup_fenced():
    run_model("browser-bridge-selection-store.js", r'''
import assert from "node:assert/strict";
let chat="",visible=true,ready=false,defer=false,resolve,next=0;
const timers=new Map(),calls=[];
const reply=()=>({contract:"a0.browser-bridge.default-selection.v1",bridge_id:"chrome-1",selected:true,
 browser_control_ready:ready,reconnect_required:!ready});
const model=createBridgeSelectionModel({context:()=>chat,confirm:async()=>false,notify:()=>{},visible:()=>visible,
 schedule:(fn,ms)=>{assert.equal(ms,5000);timers.set(++next,fn);return next;},unschedule:id=>timers.delete(id),
 api:async(_,body)=>{calls.push(body);if(defer)return new Promise(done=>resolve=done);return reply();}});
await model.mount({});assert.equal(timers.size,1);const tick=[...timers.values()][0];
assert.equal(model.defaultSelection.ready,false);
ready=true;tick();await new Promise(done=>setImmediate(done));assert.equal(model.defaultSelection.ready,true);
assert.deepEqual(calls,[{action:"default_status"},{action:"default_status"}]);
visible=false;tick();assert.equal(calls.length,2);visible=true;
model.busy=true;tick();assert.equal(calls.length,2);model.busy=false;
defer=true;tick();tick();assert.equal(calls.length,3);
chat="different-chat";resolve(reply());await new Promise(done=>setImmediate(done));tick();assert.equal(calls.length,3);
model.cleanup();assert.equal(timers.size,0);assert.equal(model.timer,null);tick();assert.equal(calls.length,3);
chat="";const pending=model.mount({});model.cleanup();resolve(reply());await pending;
assert.equal(timers.size,0);assert.equal(model.defaultSelection,null);
''')


def test_selection_ignores_stale_chat_and_rejects_forged_readiness():
    run_model("browser-bridge-selection-store.js", r'''
import assert from "node:assert/strict";
const base={contract:"a0.browser-bridge.selection.v1",context_id:"chat-1",
 bridge_id:null,selected:false,browser_control_ready:false,reconnect_required:false};
let context="chat-1", resolve;
const updates=[], notices=[], calls=[];
const model=createBridgeSelectionModel({context:()=>context,confirm:async()=>true,
 notify:(...v)=>notices.push(v),onSelected:v=>updates.push(v),api:async(_,body)=>{
 calls.push(body);if(body.action==="status")return base;
 if(body.action==="default_status"){const {context_id,...rest}=base;return {...rest,contract:"a0.browser-bridge.default-selection.v1"};}
 return new Promise(done=>resolve=done);}});
await model.mount({});const pending=model.useBrowser("browser-1");context="chat-2";
const {context_id,...defaultBase}=base;
resolve({...defaultBase,contract:"a0.browser-bridge.default-selection.v1",bridge_id:"browser-1",selected:true,reconnect_required:true});await pending;
assert.equal(updates.length,0);assert.equal(notices.length,0);
assert.equal(model.canSelect("browser-2"),false);await model.useBrowser("browser-2");
assert.equal(calls.length,3);model.cleanup();assert.equal(model.selection,null);
for(const invalid of [{...base,browser_control_ready:true},{...base,extra:true},
 {...base,selected:true,bridge_id:"browser-1",browser_control_ready:true,reconnect_required:true}]) {
 assert.throws(()=>parseSelection(invalid,"chat-1"));
}
''')


def test_default_selection_works_without_chat_and_preserves_project_override():
    run_model("browser-bridge-selection-store.js", r'''
import assert from "node:assert/strict";
let chat="",bridge=null;const calls=[];
const model=createBridgeSelectionModel({context:()=>chat,confirm:async()=>true,notify:()=>{},api:async(_,body)=>{
 calls.push(body);if(body.action==="use_default")bridge=body.bridge_id;
 if(body.action==="clear_default")bridge=null;
 if(body.action==="status")return {contract:"a0.browser-bridge.selection.v1",context_id:chat,bridge_id:"project-browser",selected:true,browser_control_ready:false,reconnect_required:true};
 return {contract:"a0.browser-bridge.default-selection.v1",bridge_id:bridge,selected:bridge!==null,browser_control_ready:bridge!==null,reconnect_required:false};
}});
await model.mount({});assert.deepEqual(calls,[{action:"default_status"}]);
assert.equal(model.canSelect("chrome-1"),true);await model.useBrowser("chrome-1");
assert.deepEqual(calls.at(-1),{action:"use_default",bridge_id:"chrome-1",expected_bridge_id:null});
assert.equal(model.selectedDefault("chrome-1"),true);assert.match(model.statusText(),/Chrome is connected/);
assert.equal(model.contextStatusText(),"");
model.cleanup();chat="chat-1";await model.mount({});assert.match(model.contextStatusText(),/project settings are kept/);
await model.useBrowser("chrome-2");assert.deepEqual(calls.at(-2),{action:"use_default",bridge_id:"chrome-2",expected_bridge_id:"chrome-1"});
assert.equal(model.selection.bridgeId,"project-browser");assert.equal(model.defaultSelection.bridgeId,"chrome-2");
await model.clear();assert.deepEqual(calls.at(-2),{action:"clear_default",expected_bridge_id:"chrome-2"});
assert.equal(model.selection.bridgeId,"project-browser");model.cleanup();
''')


ROOT = Path(__file__).resolve().parents[1]


SOURCE = ROOT / "plugins/_browser/webui/browser-bridge-access-store.js"


ACCESS_FIXTURES = r'''
import assert from "node:assert/strict";
const bridge = (id, state="active") => ({bridge_id:id,display_name:"Browser " + id,state,key_generation:1});
const inventory = (bridges) => ({contract:"a0.browser-bridge.bridges.v1",trust_version:1,browser_control_ready:false,bridges});
const policy = (id, grants=[]) => ({contract:"a0.browser-bridge.site-policy.v1",policy_version:1,bridge_id:id,site_mode:"ask_per_site",operation_grants_enabled:false,browser_control_ready:false,grants});
const grant = {grant_id:"grant-1",origin:"https://example.com"};
'''


@pytest.mark.skipif(not shutil.which("node"), reason="Node required")
def test_access_model_scopes_mutations_confirms_revocation_and_does_not_infer_readiness():
    run_model("browser-bridge-access-store.js", ACCESS_FIXTURES + r'''
const calls = [], notices = [];
let revoked = false, approved = false;
const model = createBridgeAccessModel({
  confirm: async () => approved, notify: (...args) => notices.push(args),
  api: async (endpoint, body) => {
    calls.push({endpoint, body});
    if (endpoint.endsWith("_bridges")) {
      if (body.action === "revoke") { revoked = true; return {...inventory([]),revoked:true,bridge:bridge("bridge-1","revoked")}; }
      return inventory([bridge("bridge-1",revoked?"revoked":"active")]);
    }
    return policy(body.bridge_id, body.action === "allow" ? [grant] : []);
  },
});
await model.mount();
assert.equal(model.selectedId,"bridge-1");
assert.equal(model.policyState,"loaded");
for (const value of ["https://example.com/path","https://example.com?","https://example.com#","https://u:p@example.com","https://*.example.com","https://example.com\\path","file:///tmp/a","https://example.com."]) assert.equal(normalizeSiteOrigin(value), "");
model.originDraft="HTTPS://EXAMPLE.COM:443/";
assert.equal(model.canAllowSite(), true);
await model.allowSite();
assert.deepEqual(calls.at(-1).body,{action:"allow",bridge_id:"bridge-1",origin:"https://example.com"});
assert.deepEqual(model.grants,[{id:"grant-1",origin:"https://example.com"}]);
assert.equal(model.originDraft, "");
await model.revokeSite("https://other.example");
assert.equal(calls.at(-1).body.action,"allow");
await model.revokeBridge();
assert.equal(revoked,false);
approved=true;
await model.revokeBridge();
assert.equal(revoked,true);
assert.equal(model.selectedBridge().state,"revoked");
assert.equal(model.canManageSites(),false);
assert.equal(model.grants.length,0);
model.cleanup();
assert.equal(model.bridges.length,0);
assert.equal(model.selectedId,"");
assert.equal(notices.length,2);
''')


@pytest.mark.skipif(not shutil.which("node"), reason="Node required")
def test_access_model_discards_stale_host_responses_and_closed_panel_confirmation():
    run_model("browser-bridge-access-store.js", ACCESS_FIXTURES + r'''
let resolveOld, resolveConfirm, defer=false;
let writes=0;
const model=createBridgeAccessModel({notify:()=>{},confirm:()=>new Promise(r=>{resolveConfirm=r;}),api:async(endpoint,body)=>{
  if(body.action!=="list") writes++;
  if(endpoint.endsWith("_bridges")) return inventory([bridge("bridge-1"),bridge("bridge-2")]);
  if(defer && body.bridge_id==="bridge-1") return await new Promise(r=>{resolveOld=r;});
  return policy(body.bridge_id);
}});
await model.mount();
defer=true;
const pending=model.selectBridge("bridge-1");
await model.selectBridge("bridge-2");
resolveOld(policy("bridge-1",[grant])); await pending;
assert.equal(model.selectedId,"bridge-2");
assert.deepEqual(model.grants,[]);
const confirmation=model.revokeBridge();
model.cleanup();resolveConfirm(true);await confirmation;
assert.equal(writes,0);
assert.equal(model.active,false);
''')


def test_management_ui_uses_plain_text_and_existing_notification_system():
    source = SOURCE.read_text()
    html = (ROOT / "plugins/_browser/webui/config.html").read_text()
    assert 'x-destroy="$store.browserBridgeAccess.cleanup(); $store.browserBridgeSelection.cleanup()"' in html
    assert 'x-text="grant.origin"' in html
    assert "Revoke browser access" in html
    assert "frontendNotification" in source and "frontendOnly: true" in source
    assert "localStorage" not in source and "sessionStorage" not in source
    assert "browser_bridge_exchange" not in source


def test_quiet_inventory_refresh_preserves_draft_and_never_changes_consent():
    run_model("browser-bridge-access-store.js", ACCESS_FIXTURES + r'''
const calls=[];const model=createBridgeAccessModel({notify:()=>{},confirm:async()=>false,
 api:async(endpoint,body)=>{calls.push(body);return endpoint.endsWith("_bridges")?inventory([bridge("bridge-1")]):policy(body.bridge_id);}});
await model.mount();model.originDraft="https://still-typing.example";
await model.refresh({background:true});
assert.equal(model.originDraft,"https://still-typing.example");
assert.deepEqual(calls.at(-1),{action:"list"});
assert.equal(calls.length,3);
model.busy=true;await model.refresh({background:true});assert.equal(calls.length,3);
''')


def test_all_websites_requires_confirmation_and_discards_stale_setting_response():
    run_model("browser-bridge-access-store.js", ACCESS_FIXTURES + r'''
let approved=false, pendingConfirm, writes=0;
const model=createBridgeAccessModel({notify:()=>{},confirm:async()=>approved,
 api:async(endpoint,body)=>{
  if(endpoint.endsWith("_bridges"))return inventory([bridge("bridge-1"),bridge("bridge-2")]);
  if(body.action==="set_mode"){writes++;return {...policy(body.bridge_id),site_mode:body.site_mode};}
  return policy(body.bridge_id);
 }});
await model.mount();assert.equal(model.siteMode,"ask_per_site");
await model.setAllWebsites(true);assert.equal(writes,0);
approved=true;await model.setAllWebsites(true);
assert.equal(writes,1);assert.equal(model.siteMode,"allow_all_websites");
await model.setAllWebsites(false);assert.equal(model.siteMode,"ask_per_site");
await model.selectBridge("bridge-2");assert.equal(model.siteMode,"ask_per_site");
model.cleanup();await model.setAllWebsites(true);assert.equal(writes,2);
let resolveConfirm;
const other=createBridgeAccessModel({notify:()=>{},confirm:()=>new Promise(r=>resolveConfirm=r),
 api:async(endpoint,body)=>{if(body.action!=="list")writes++;return endpoint.endsWith("_bridges")?inventory([bridge("bridge-1")]):policy(body.bridge_id);}});
await other.mount();const pending=other.setAllWebsites(true);other.cleanup();resolveConfirm(true);await pending;
assert.equal(writes,2);
''')


PROJECT_ROOT = Path(__file__).resolve().parents[1]


CONFIG_HTML = PROJECT_ROOT / "plugins" / "_browser" / "webui" / "config.html"


CONFIG_STORE = (
    PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-config-store.js"
)


def _store_source() -> str:
    source = CONFIG_STORE.read_text(encoding="utf-8")
    source = re.sub(r"^import .*;\n", "", source, flags=re.M)
    return "const notifications = {frontendNotification: async () => {}};\n" + source.replace(
        'export const store = createStore("browserConfig", {',
        'const store = createStore("browserConfig", {',
    )


def test_pairing_panel_is_transient_redacted_and_explicitly_browser_host_only() -> None:
    html = CONFIG_HTML.read_text(encoding="utf-8")
    store = CONFIG_STORE.read_text(encoding="utf-8")

    assert 'id="browser-pairing-title"' in html
    assert "Single-use pairing code" in html
    assert "five-minute lifetime" in html
    assert "Copy code" in html
    assert "Regenerate" in html
    assert "Cancel pending code" in html
    assert "Install the companion on the computer running Chrome." in html
    assert "Never install it inside Docker." in html
    assert "Your saved pairing stays on that computer" in html
    assert 'x-text="$store.browserConfig.pairingCode"' in html
    assert 'x-html="$store.browserConfig.pairingCode"' not in html
    assert "browser_bridge_exchange" not in html + store
    assert "localStorage" not in store
    assert "sessionStorage" not in store
    assert "clearPairingCode();" in store
    assert 'action: "create"' in store
    assert 'action: "status"' in store
    assert 'action: "cancel"' in store


@pytest.mark.skipif(not shutil.which("node"), reason="node is required")
def test_pairing_store_creates_copies_cancels_and_clears_code_without_persistence() -> None:
    source = _store_source()
    script = """
const calls = [];
let copied = "";
const createStore = (_name, value) => value;
const showConfirmDialog = async () => false;
const window = { setInterval: () => 1, clearInterval: () => {}, isSecureContext: true };
Object.defineProperty(globalThis, "navigator", {
  configurable: true,
  value: { clipboard: { writeText: async (value) => { copied = value; } } },
});
const code = "A0B1-11111111-00000000000000000000000000000000";
const callJsonApi = async (endpoint, payload) => {
  calls.push({ endpoint, payload });
  const now = Date.now();
  if (payload.action === "create") {
    return {
      contract: "a0.browser-bridge.trust.v1",
      trust_version: 1,
      state: "pairing_pending",
      pairing_id: "11111111-1111-4111-8111-111111111111",
      pairing_code: code,
      server: {
        base_url: "http://localhost:50080",
        instance_fingerprint: "sha256:00000000000000000000",
      },
      extension_id: "abcdefghijklmnopabcdefghijklmnop",
      display_name: payload.display_name,
      created_at_ms: now,
      expires_at_ms: now + 300000,
      expires_in_seconds: 300,
      native_runtime_location: "user_browser_host",
      docker_install_target: false,
      connector_session_ready: false,
      browser_control_ready: false,
    };
  }
  if (payload.action === "cancel") {
    return {
      contract: "a0.browser-bridge.trust.v1",
      trust_version: 1,
      state: "unpaired",
      reason_code: "no_active_bridge_record",
      pairing_id: null,
      server_base_url: null,
      extension_id: null,
      display_name: null,
      expires_at_ms: null,
      pairing_code_present: false,
      native_runtime_location: "user_browser_host",
      docker_install_target: false,
      connector_session_ready: false,
      browser_control_ready: false,
      server_pairing_enabled: true,
      canceled: true,
    };
  }
  throw new Error("unexpected action");
};
""" + source + """
store.pairingPanelActive = true;
store.pairingPanelGeneration = 1;
store.pairingDisplayName = "My browser host";
store.pairingStatus = {
  state: "unpaired",
  reasonCode: "no_active_bridge_record",
  pairingId: "",
  expiresAtMs: 0,
  serverPairingEnabled: true,
};
await store.createBrowserBridgePairing();
if (store.pairingCode !== code) throw new Error("pairing code was not presented");
if (!store.pairingCodeAvailable()) throw new Error("fresh pairing code was unavailable");
if (calls[0].endpoint !== "/plugins/_a0_connector/browser_bridge_pairing") {
  throw new Error("wrong pairing endpoint");
}
if (JSON.stringify(calls[0].payload) !== JSON.stringify({
  action: "create",
  display_name: "My browser host",
})) throw new Error("create request was not exact");
await store.copyBrowserBridgePairingCode();
if (copied !== code) throw new Error("explicit copy did not use current code");
await store.cancelBrowserBridgePairing();
if (store.pairingError) throw new Error(store.pairingError);
if (store.pairingCode !== "") throw new Error("cancel retained pairing code");
if (calls[1].payload.action !== "cancel") throw new Error("cancel was not sent");
if ("extension_id" in calls[0].payload || "server_base_url" in calls[0].payload) {
  throw new Error("UI supplied server-owned identity");
}
store.pairingCode = code;
store.pairingCodePairingId = "stale";
store.cleanup();
if (store.pairingCode !== "") throw new Error("panel cleanup retained pairing code");
"""

    run_node(script)


@pytest.mark.skipif(not shutil.which("node"), reason="node is required")
def test_pairing_status_projection_drops_server_secrets_and_never_claims_control() -> None:
    source = _store_source()
    script = """
const createStore = (_name, value) => value;
const showConfirmDialog = async () => false;
const window = { setInterval: () => 1, clearInterval: () => {} };
const navigator = {};
const callJsonApi = async (_endpoint, payload) => {
  if (payload.action !== "status") throw new Error("unexpected action");
  return {
    contract: "a0.browser-bridge.trust.v1",
    trust_version: 1,
    state: "pairing_pending",
    reason_code: "pairing_intent_active",
    pairing_id: "11111111-1111-4111-8111-111111111111",
    expires_at_ms: Date.now() + 300000,
    pairing_code_present: false,
    pairing_code: "MUST-NOT-ENTER-STORE",
    extension_id: "abcdefghijklmnopabcdefghijklmnop",
    public_key: { value: "MUST-NOT-ENTER-STORE" },
    server_base_url: "http://localhost:50080",
    server_pairing_enabled: true,
    connector_session_ready: false,
    browser_control_ready: false,
  };
};
""" + source + """
store.pairingPanelActive = true;
store.pairingPanelGeneration = 1;
await store.loadBrowserBridgePairingStatus();
const serialized = JSON.stringify(store.pairingStatus);
if (serialized.includes("MUST-NOT-ENTER-STORE")) throw new Error("secret entered status");
if (serialized.includes("extension_id") || serialized.includes("public_key")) {
  throw new Error("identity entered status projection");
}
if (store.pairingCode !== "") throw new Error("status restored a pairing code");
if (store.pairingStatus.state !== "not_checked") {
  throw new Error("secret-bearing status was not rejected");
}
if (!store.pairingStatusLabel().includes("not been checked")) {
  throw new Error("rejected status claimed a known state");
}
const redactedPending = normalizePairingStatus({
  contract: "a0.browser-bridge.trust.v1",
  trust_version: 1,
  state: "pairing_pending",
  reason_code: "pairing_intent_active",
  pairing_id: "11111111-1111-4111-8111-111111111111",
  expires_at_ms: Date.now() + 300000,
  pairing_code_present: false,
  extension_id: "abcdefghijklmnopabcdefghijklmnop",
  server_base_url: "http://localhost:50080",
  display_name: "Browser host",
  server_pairing_enabled: true,
  native_runtime_location: "user_browser_host",
  docker_install_target: false,
  connector_session_ready: false,
  browser_control_ready: false,
});
if (!redactedPending) throw new Error("valid redacted status was rejected");
if (JSON.stringify(redactedPending).includes("abcdefghijklmnop")) {
  throw new Error("extension identity entered status projection");
}
store.pairingStatus = redactedPending;
store.pairingNowMs = Date.now();
if (!store.pairingStatusLabel().includes("Regenerate")) {
  throw new Error("redacted pending status lacked regeneration guidance");
}
if (store.pairingStatus.connectorSessionReady || store.pairingStatus.browserControlReady) {
  throw new Error("UI claimed runtime readiness");
}
"""

    run_node(script)


@pytest.mark.skipif(not shutil.which("node"), reason="node is required")
def test_late_pairing_response_cannot_restore_code_after_panel_teardown() -> None:
    source = _store_source()
    script = """
let resolveCreate;
const createStore = (_name, value) => value;
const showConfirmDialog = async () => false;
const window = { setInterval: () => 1, clearInterval: () => {} };
const navigator = {};
const callJsonApi = async (_endpoint, payload) => {
  if (payload.action !== "create") throw new Error("unexpected action");
  return await new Promise((resolve) => { resolveCreate = resolve; });
};
""" + source + """
store.pairingPanelActive = true;
store.pairingPanelGeneration = 7;
store.pairingStatus = {
  state: "unpaired",
  reasonCode: "no_active_bridge_record",
  pairingId: "",
  expiresAtMs: 0,
  serverPairingEnabled: true,
};
const pending = store.createBrowserBridgePairing();
await Promise.resolve();
store.cleanup();
const now = Date.now();
resolveCreate({
  contract: "a0.browser-bridge.trust.v1",
  trust_version: 1,
  state: "pairing_pending",
  pairing_id: "11111111-1111-4111-8111-111111111111",
  pairing_code: "A0B1-11111111-00000000000000000000000000000000",
  server: {
    base_url: "http://localhost:50080",
    instance_fingerprint: "sha256:00000000000000000000",
  },
  extension_id: "abcdefghijklmnopabcdefghijklmnop",
  display_name: "My browser host",
  created_at_ms: now,
  expires_at_ms: now + 300000,
  expires_in_seconds: 300,
  native_runtime_location: "user_browser_host",
  docker_install_target: false,
  connector_session_ready: false,
  browser_control_ready: false,
});
await pending;
if (store.pairingCode !== "") throw new Error("late response restored pairing code");
if (store.pairingPanelActive) throw new Error("panel was reactivated by late response");
"""

    run_node(script)
