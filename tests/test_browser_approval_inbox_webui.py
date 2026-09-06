import shutil
import pytest
from pathlib import Path
from browser_bridge_test_support import run_model


ROOT = Path(__file__).resolve().parents[1]


WEBUI = ROOT / "plugins/_browser/webui"


@pytest.mark.skipif(not shutil.which("node"), reason="Node required")
@pytest.mark.parametrize("lane", ["site", "action"])
def test_pending_consent_survives_failed_poll_disabled_until_revalidated(lane):
    action = lane == "action"
    factory = "createActionRequestsModel" if action else "createSiteRequestsModel"
    contract = "approval" if action else "site-authority"
    script = f'''
import assert from "node:assert/strict";
const base={{contract:"a0.browser-bridge.{contract}.v1",{('approval_version' if action else 'authority_version')}:1,browser_control_ready:false}};
const request={{challenge_id:"request-1",origin:"https://example.com",expires_at_ms:2000,
 action_class:"{'unknown' if action else 'navigate'}",summary:"Do not render",{('action:"click",' if action else '')}
 options:{'["decline","approve_once"]' if action else '["deny","allow_once","allow_turn"]'}}};
let failed=false,empty=true,time=1000,chat="chat-1";const calls=[];
const model={factory}({{selection:()=>{'({contextId:chat})' if action else 'chat'},now:()=>time,schedule:()=>1,unschedule:()=>{{}},
 api:async(endpoint,body)=>{{calls.push(body);if(failed)throw Error("offline");return {{...base,challenges:empty?[]:[request]}};}}}});
await model.mount();assert.equal(model.visibleRequests().length,0);
empty=false;await model.refresh();assert.equal(model.canDecide(model.requests[0]),true);
failed=true;await model.refresh();assert.equal(model.visibleRequests().length,1);
assert.equal(model.canDecide(model.requests[0]),false);
const count=calls.length;await model.decide(model.requests[0],"{'approve_once' if action else 'allow_once'}");assert.equal(calls.length,count);
chat="chat-2";assert.equal(model.visibleRequests().length,0);assert.equal(model.unavailableHere(),false);
chat="chat-1";time=2001;assert.equal(model.visibleRequests().length,0);
time=1000;failed=false;await model.refresh();assert.equal(model.canDecide(model.requests[0]),true);
empty=true;await model.refresh();assert.equal(model.visibleRequests().length,0);model.cleanup();
'''
    run_model("browser-action-requests-store.js" if action else "browser-site-requests-store.js", script)


@pytest.mark.skipif(not shutil.which("node"), reason="Node required")
def test_one_notification_without_composer_recovery_for_both_lanes():
    run_model("browser-approval-inbox-store.js", r'''
import assert from "node:assert/strict";
let failed=false,chat="chat-1",refreshes=0;const notices=[];
const stores=Array.from({length:2},()=>({active:true,unavailableHere:()=>failed,refresh:async()=>{refreshes++;}}));
const model=createApprovalInboxModel({stores:()=>stores,selection:()=>chat,notify:message=>notices.push(message)});
model.observe();assert.equal(model.unavailable(),false);assert.equal(notices.length,0);
failed=true;model.observe();model.observe();assert.equal(notices.length,1);
assert.equal(model.retry,undefined);assert.equal(refreshes,0);model.observe();assert.equal(notices.length,1);
assert.match(notices[0],/check again automatically/);assert.doesNotMatch(notices[0],/Use Check|try again/);
chat="chat-2";model.observe();assert.equal(notices.length,2);
failed=false;model.observe();failed=true;model.observe();assert.equal(notices.length,3);
stores.forEach(store=>store.active=false);assert.equal(model.unavailable(),false);
''')
    for name in ["browser-site-requests.html", "browser-action-requests.html"]:
        template = (WEBUI / name).read_text()
        assert "unavailableHere()" not in template
        assert "visibleRequests().length" in template
        assert "x-cloak" in template
        assert "canDecide(request)" in template
    composer = (ROOT / "plugins/_browser/extensions/webui/chat-input-start/browser-approvals.html").read_text()
    assert "browserApprovalInbox.retry()" not in composer
    assert "browser-approval-recovery" not in composer
    assert "Check browser requests" not in composer
    coordinator = (WEBUI / "browser-approval-inbox-store.js").read_text()
    assert "notifications.addOrUpdateNotification(" in coordinator
    assert "notifications.updateUnreadCount()" in coordinator
    assert "notifications.frontendNotification(" not in coordinator


@pytest.mark.skipif(not shutil.which("node"), reason="Node required")
def test_action_ui_sends_only_explicit_choice_and_never_retries_uncertainty():
    script = r'''
import assert from "node:assert/strict";
const base={contract:"a0.browser-bridge.approval.v1",approval_version:1,browser_control_ready:false};
const challenge={challenge_id:"action-1",action:"click",origin:"https://example.com",action_class:"unknown",options:["decline","approve_once"],expires_at_ms:2000,summary:"Do not render <script>"};
const calls=[],timers=new Map();let time=1000,next=0,uncertain=false,pending=null;
let selected={contextId:"context-1"};
const model=createActionRequestsModel({selection:()=>selected,now:()=>time,schedule:fn=>{timers.set(++next,fn);return next;},unschedule:id=>timers.delete(id),api:async(_endpoint,body)=>{
  calls.push(body);
  if(body.action==="list")return {...base,challenges:[challenge]};
  if(uncertain)throw new Error("unknown response");
  return {...base,challenge_id:body.challenge_id,decision:body.choice==="approve_once"?"approved":"declined",control_id:"control-1",status:"accepted"};
}});
await model.mount();assert.equal(model.requests[0].summary,undefined);
assert.deepEqual(calls[0],{action:"list",context_id:"context-1"});
selected={...selected,contextId:"other-context"};assert.equal(model.visibleRequests().length,0);assert.equal(model.canDecide(model.requests[0]),false);
selected={contextId:"context-1"};
await model.decide(model.requests[0],"approve_once");
assert.deepEqual(calls.at(-1),{challenge_id:"action-1",choice:"approve_once"});assert.equal(model.requests.length,0);
assert.match(model.visibleNotice(),/Approval recorded/);
time=3999;assert.notEqual(model.visibleNotice(),"");time=4000;assert.equal(model.visibleNotice(),"");time=1000;
await model.refresh();time=2001;const count=calls.length;
await model.decide(model.requests[0],"approve_once");assert.equal(calls.length,count);
time=1000;await model.refresh();uncertain=true;await model.decide(model.requests[0],"decline");
assert.equal(model.decisionUnconfirmed,true);assert.equal(model.requests.length,0);
assert.equal(model.hasUnconfirmedDecision(),true);selected={contextId:"context-2"};assert.equal(model.visibleNotice(),"");assert.equal(model.hasUnconfirmedDecision(),false);selected={contextId:"context-1"};assert.equal(model.hasUnconfirmedDecision(),true);
time=2001;assert.equal(model.visibleNotice(),"");assert.equal(model.hasUnconfirmedDecision(),false);time=1000;
// The expiry check legitimately pruned the quarantine; create a new uncertain
// decision to keep exercising no-replay through refresh and close/reopen.
await model.refresh();await model.decide(model.requests[0],"decline");
const mutations=calls.filter(body=>body.choice).length;
await model.refresh();assert.equal(calls.filter(body=>body.choice).length,mutations);
assert.equal(model.visibleRequests().length,0);assert.equal(model.canDecide(model.requests[0]),false);
await model.decide(model.requests[0],"approve_once");assert.equal(calls.filter(body=>body.choice).length,mutations);
model.cleanup();assert.equal(timers.size,0);assert.equal(model.notice,"");
await model.mount();assert.equal(model.visibleRequests().length,0);assert.equal(model.canDecide(model.requests[0]),false);model.cleanup();
const late=createActionRequestsModel({selection:()=>selected,schedule:()=>1,unschedule:()=>{},api:()=>new Promise(resolve=>pending=resolve)});
const mounted=late.mount();late.cleanup();pending({...base,challenges:[challenge]});await mounted;
assert.equal(late.requests.length,0);assert.equal(late.loading,false);
const typing=createActionRequestsModel({selection:()=>selected,now:()=>1000,schedule:()=>1,unschedule:()=>{},api:async()=>({...base,challenges:[{...challenge,action:"type",action_class:"sensitive_input",text:"never display",data_classification:{text_sha256:"secret"}}]})});
await typing.mount();assert.equal(typing.requests[0].action,"type");assert.equal(typing.requests[0].text,undefined);assert.equal(typing.requests[0].data_classification,undefined);typing.cleanup();
const upload=createActionRequestsModel({selection:()=>selected,now:()=>1000,schedule:()=>1,unschedule:()=>{},api:async()=>({...base,challenges:[{...challenge,action:"upload_file",action_class:"external_side_effect",path:"/never/project",artifact_id:"never-project"}]})});
await upload.mount();assert.equal(upload.requests[0].action,"upload_file");assert.equal(upload.requests[0].path,undefined);assert.equal(upload.requests[0].artifact_id,undefined);upload.cleanup();
'''
    run_model("browser-action-requests-store.js", script)


ROOT = Path(__file__).resolve().parents[1]


def test_site_prompt_keeps_scope_explicit_and_secondary_choices_disclosed():
    html = (ROOT / "plugins/_browser/webui/browser-site-requests.html").read_text()
    main, details = html.split('<details class="browser-site-request-options">', 1)
    assert 'x-text="request.origin"' in main
    assert "Remember for future chats." in main
    assert "Always allow site" in main and "Deny</button>" in main
    assert '<summary>More options</summary>' in details
    assert "Allow once" in details and "Allow this turn" in details
    assert "consequential actions need separate approval" in details
    assert 'class="button confirm"' in main
    assert "Check status" in details and "Refresh requests" not in html


@pytest.mark.skipif(not shutil.which("node"), reason="Node required")
def test_site_requests_are_decision_only_expiring_and_fenced_after_cleanup():
    script = r'''
import assert from "node:assert/strict";
const contract="a0.browser-bridge.site-authority.v1";
const responseBase={contract,authority_version:1,browser_control_ready:false};
const challenge={challenge_id:"challenge-1",origin:"https://next.example",action_class:"navigate",summary:"Never render this <img>",options:["deny","allow_once","allow_turn"],expires_at_ms:2000};
assert.equal(parseRequests({...responseBase,challenges:[{...challenge,action_class:"open",options:firstOpenDecisions}]},"context-1",PRODUCTION_PROFILE)[0].canRemember,true);
assert.throws(()=>parseRequests({...responseBase,challenges:[{...challenge,options:firstOpenDecisions}]},"context-1",PRODUCTION_PROFILE));
assert.throws(()=>parseRequests({...responseBase,contract:"a0.browser-bridge.development-site-authority.v1",challenges:[challenge]},"context-1",PRODUCTION_PROFILE), /Invalid site authority/);
const calls=[],timers=new Map(); let time=1000, next=0, pending=null, defer=false;
let selectedContext="context-1";
const model=createSiteRequestsModel({selection:()=>selectedContext,now:()=>time,schedule:(fn)=>{timers.set(++next,fn);return next;},unschedule:id=>timers.delete(id),api:async(endpoint,body)=>{
  calls.push(body);
  if(defer) return await new Promise(resolve=>{pending=resolve;});
  if(body.action==="list") return {...responseBase,challenges:[challenge]};
  return {...responseBase,challenge_id:body.challenge_id,decision:body.decision,control_id:"control-1",status:"accepted",expires_at_ms:2000};
}});
await model.mount();
assert.equal(model.requests[0].origin,"https://next.example");
assert.equal(model.requests[0].summary,undefined);
assert.deepEqual(calls[0],{action:"list",context_id:"context-1"});
selectedContext="context-2";assert.equal(model.visibleRequests().length,0);assert.equal(model.canDecide(model.requests[0]),false);selectedContext="context-1";
assert.equal(timers.size,1);
await model.decide(model.requests[0],"allow_once");
assert.deepEqual(calls.at(-1),{action:"decide",challenge_id:"challenge-1",decision:"allow_once"});
assert.equal(model.requests.length,0);
assert.notEqual(model.visibleNotice(),"");selectedContext="context-2";assert.equal(model.visibleNotice(),"");selectedContext="context-1";
await model.refresh();time=2001;
assert.equal(model.visibleNotice(),"");assert.equal(model.hasUnconfirmedDecision(),false);
const count=calls.length;await model.decide(model.requests[0],"allow_turn");assert.equal(calls.length,count);
time=1000;defer=true;
const old=model.refresh();model.cleanup();pending({...responseBase,challenges:[challenge]});await old;
assert.deepEqual(model.requests,[]);assert.equal(timers.size,0);assert.equal(model.loading,false);
defer=false;await model.mount();
defer=true;const decision=model.decide(model.requests[0],"deny");model.cleanup();
pending({...responseBase,challenge_id:"challenge-1",decision:"deny",control_id:"control-2",status:"accepted",expires_at_ms:2000});await decision;
assert.equal(model.notice,"");assert.equal(model.busyId,"");assert.equal(timers.size,0);
defer=false;time=1000;challenge.action_class="open";challenge.options=firstOpenDecisions;challenge.expires_at_ms=120000;
await model.mount();await model.decide(model.requests[0],"allow_site");
assert.equal(calls.at(-1).decision,"allow_site");assert.equal(model.noticeExpires,4000);
time=4001;assert.equal(model.visibleNotice(),"");
await model.refresh();const savedApi=model.noticeExpires;
defer=true;const uncertain=model.decide(model.requests[0],"allow_site");pending({});await uncertain;
assert.equal(model.decisionUnconfirmed,true);assert.equal(model.noticeExpires,120000);
model.cleanup();
'''
    run_model("browser-site-requests-store.js", script)
