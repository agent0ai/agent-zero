import base64
from pathlib import Path
import shutil
import subprocess

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MESSAGE_WINDOW_JS = PROJECT_ROOT / "webui" / "js" / "message-window.js"
SCROLLER_JS = PROJECT_ROOT / "webui" / "js" / "scroller.js"
PROCESS_GROUP_DOM_JS = (
    PROJECT_ROOT
    / "webui"
    / "components"
    / "messages"
    / "process-group"
    / "process-group-dom.js"
)
MESSAGE_COLLAPSE_JS = PROJECT_ROOT / "webui" / "js" / "message-collapse.js"


def test_text_editor_and_code_execution_keep_memory_search_in_the_process_group():
    if not shutil.which("node"):
        pytest.skip("Node.js is required to execute the message-window regression.")

    module_url = "data:text/javascript;base64," + base64.b64encode(
        MESSAGE_WINDOW_JS.read_bytes()
    ).decode("ascii")
    script = f"""
import assert from "node:assert/strict";
import {{ MessageWindow, PROCESS_STEP_TYPES, classifyMessageRenderUnits }} from {module_url!r};

for (const type of ["code_exe", "text_editor", "custom_plugin_step"]) {{
  const classify = messages => classifyMessageRenderUnits(messages, new Set([...PROCESS_STEP_TYPES, type]));
  const logs = [{{ no: 0, type: "user" }}, {{ no: 1, type: "agent" }},
    ...Array.from({{ length: 65 }}, (_, i) => ({{ no: i + 2, type }}))];
  const windowed = new MessageWindow({{
    getUnitKeys: messages => classify(messages).map(unit => unit.key),
  }});
  windowed.reset(logs);
  windowed.merge([{{ no: 67, type: "util", heading: "Searching memories..." }}]);
  const units = classify(windowed.visibleMessages());
  assert.equal(units.length, 67, `${{type}} must retain the whole process group`);
  assert.ok(units.every(unit => unit.group === units[0].group && unit.isStep),
    `${{type}} must keep memory search inside the substantive group`);

  const prefixed = classify([{{ type: "util" }}, {{ type }}]);
  assert.ok(prefixed[0].group && prefixed[0].group === prefixed[1].group);
  const completed = classify([
    {{ type }}, {{ type: "response", agentno: 0 }}, {{ type: "util" }},
  ]);
  assert.equal(completed[0].group, completed[1].group);
  assert.equal(completed[2].group, null, "post-response utilities must stay separate");
}}
"""
    subprocess.run(["node", "--input-type=module", "-e", script], check=True, text=True)


def test_message_window_keeps_tail_and_pages_bidirectionally():
    if not shutil.which("node"):
        pytest.skip("Node.js is required to execute the message-window regression.")

    source = MESSAGE_WINDOW_JS.read_bytes()
    module_url = "data:text/javascript;base64," + base64.b64encode(source).decode("ascii")
    script = f"""
import {{ MessageWindow, PROCESS_STEP_TYPES, classifyMessageRenderUnits }} from {module_url!r};

function assert(condition, message) {{
  if (!condition) throw new Error(message);
}}

const pluginBackedGroup = [
  {{ no: 1, id: "step-1", type: "info" }},
  {{ no: 2, id: "step-2", type: "agent" }},
  {{ no: 3, id: "step-3", type: "code_exe" }},
  {{ no: 4, id: "step-4", type: "agent" }},
  {{ no: 5, id: "step-5", type: "code_exe" }},
  {{ no: 6, id: "response-1", type: "response", agentno: 0 }},
];
const pluginBackedUnits = classifyMessageRenderUnits(pluginBackedGroup, new Set([...PROCESS_STEP_TYPES, "code_exe"]));
assert(
  pluginBackedUnits.every((unit) => unit.key === pluginBackedUnits[0].key),
  "code execution records must remain inside their surrounding process group",
);
assert(
  pluginBackedUnits.filter((unit) => unit.isStep).length === 5,
  "the root response must close the group without becoming a process step",
);

const prefixedUtilityGroup = [
  {{ no: 20, type: "util" }},
  {{ no: 21, type: "util" }},
  {{ no: 22, type: "agent", id: "agent-with-prefix" }},
  {{ no: 23, type: "response", id: "agent-with-prefix", agentno: 0 }},
];
const prefixedUtilityUnits = classifyMessageRenderUnits(prefixedUtilityGroup);
assert(
  prefixedUtilityUnits.every((unit) => unit.key === prefixedUtilityUnits[0].key),
  "utilities immediately before a real process step must stay in that group",
);

const utilityOnlyResponse = [
  {{ no: 30, type: "util" }},
  {{ no: 31, type: "util" }},
  {{ no: 32, type: "response", id: "response-without-step", agentno: 0 }},
  {{ no: 33, type: "util" }},
  {{ no: 34, type: "user", id: "next-user" }},
];
const utilityOnlyUnits = classifyMessageRenderUnits(utilityOnlyResponse);
assert(
  utilityOnlyUnits.every((unit) => unit.group === null && !unit.isStep),
  "orphan utilities must not create or reopen a process group around a response",
);

const sharedIdGroup = new MessageWindow({{ initialLimit: 60 }});
const sharedIdKeys = sharedIdGroup.merge([
  {{ no: 1, id: "shared-run-id", type: "agent", content: "final generation" }},
  {{ no: 2, id: "shared-run-id", type: "response", content: "final response" }},
]);
assert(
  sharedIdKeys.has("id:shared-run-id:type:response"),
  "merge must report a newly added step",
);
const updatedSharedIdKeys = sharedIdGroup.merge([
  {{ no: 2, id: "shared-run-id", type: "response", content: "updated response" }},
]);
assert(
  updatedSharedIdKeys.size === 0,
  "merge must not report an existing record update as newly added",
);
assert(sharedIdGroup.size === 2, "a shared id must not merge GEN and response records");
assert(
  sharedIdGroup.visibleMessages().map((entry) => entry.type).join(",") ===
    "agent,response",
  "replay must retain the final GEN immediately before its response",
);
sharedIdGroup.merge([
  {{ no: 2, id: "shared-run-id", type: "response", content: "updated response" }},
]);
assert(sharedIdGroup.size === 2, "updates to one typed record must not duplicate it");
assert(
  sharedIdGroup.visibleMessages().at(-1).content === "updated response",
  "typed cache keys must still replace updates to the same message",
);

const logs = Array.from({{ length: 1000 }}, (_, no) => ({{
  no,
  type: no % 20 === 0 ? "user" : "tool",
  content: `log-${{no}}`,
}}));
const windowed = new MessageWindow({{ initialLimit: 60, pageSize: 60, maxWindow: 120 }});
windowed.reset(logs);

assert(windowed.start === 940 && windowed.end === 1000, "initial render must start at the tail");
assert(windowed.visibleMessages()[0].no === 940, "tail slice must be ordered");
assert(windowed.olderCount === 940 && windowed.newerCount === 0, "tail counts must be accurate");

const unordered = new MessageWindow({{ initialLimit: 3, pageSize: 2, maxWindow: 4 }});
unordered.reset([logs[2], logs[0], logs[1]]);
assert(unordered.visibleMessages().map((entry) => entry.no).join(",") === "0,1,2", "out-of-order records must be sorted once");

const groupedLogs = Array.from({{ length: 300 }}, (_, no) => ({{
  no,
  unit: no >= 135 && no < 195 ? "large-process-group" : `entry-${{no}}`,
}}));
const groupedWindow = new MessageWindow({{
  initialLimit: 60,
  pageSize: 60,
  maxWindow: 120,
  getUnitKeys: (messages) => messages.map((message) => message.unit),
}});
groupedWindow.reset(groupedLogs);
groupedWindow.shiftOlder();
assert(groupedWindow.visibleStart === 135 && groupedWindow.visibleEnd === 300, "a page boundary must expand to the complete process group");
assert(groupedWindow.visibleMessages().filter((message) => message.unit === "large-process-group").length === 60, "a process group must never be split across the window");
groupedWindow.shiftOlder();
assert(groupedWindow.visibleStart === 120 && groupedWindow.visibleEnd === 240, "older paging must retain the whole intersecting group");
groupedWindow.shiftNewer();
assert(groupedWindow.visibleStart === 135 && groupedWindow.visibleEnd === 300, "newer paging must restore the whole-group tail range");

windowed.shiftOlder();
assert(windowed.start === 880 && windowed.end === 1000, "first older page should retain the tail overlap");
windowed.shiftOlder();
assert(windowed.start === 820 && windowed.end === 940, "older paging must retain exactly the adjacent page");
assert(windowed.hasOlder && windowed.hasNewer, "a historical window must page in both directions");

windowed.shiftNewer();
assert(windowed.start === 880 && windowed.end === 1000, "newer paging must reverse the older-page swap exactly");
assert(windowed.renderedCount === 120, "a shifted window must contain exactly two pages");

windowed.showHead();
assert(windowed.start === 0 && windowed.end === 60, "the initial head view must contain one page");
windowed.shiftNewer();
assert(windowed.start === 0 && windowed.end === 120, "the first forward shift must retain page A and append page B");
windowed.shiftNewer();
assert(windowed.start === 60 && windowed.end === 180, "the second forward shift must retain B and append C");
windowed.shiftNewer();
assert(windowed.start === 120 && windowed.end === 240, "the third forward shift must retain C and append D");
windowed.shiftOlder();
assert(windowed.start === 60 && windowed.end === 180, "a reverse shift must restore B beside C");
windowed.shiftOlder();
assert(windowed.start === 0 && windowed.end === 120, "a second reverse shift must restore A beside B");

windowed.showTail();
windowed.shiftOlder();
assert(windowed.start === 880 && windowed.end === 1000, "tail paging must restore a two-page live window");

windowed.merge(Array.from({{ length: 20 }}, (_, offset) => ({{
  no: 1000 + offset,
  type: "tool",
  content: `new-${{offset}}`,
}})));
assert(windowed.end === 1020, "live tail appends must remain visible");
assert(windowed.compactTailIfNeeded(), "an oversized live window must compact");
assert(windowed.start === 900 && windowed.end === 1020, "compaction must retain two complete tail pages");
assert(windowed.renderedCount === 120, "tail compaction must use the same two-page bound");

windowed.merge([{{ no: 1019, type: "response", content: "updated" }}]);
const updated = windowed.visibleMessages().at(-1);
assert(updated.type === "response" && updated.content === "updated", "existing log updates must replace cached data");

windowed.reset(logs);
windowed.merge([{{ no: 1000, type: "tool", content: "unread" }}], {{ followTail: false }});
assert(windowed.end === 1000, "an unfollowed live append must not move the visible window");
assert(windowed.newerCount === 1, "an unfollowed live append must remain available as a newer page");
"""
    subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        text=True,
    )


def test_warning_replay_prefers_classified_process_group():
    messages = (PROJECT_ROOT / "webui" / "js" / "messages.js").read_text(
        encoding="utf-8"
    )
    warning_handler = messages.split(
        "export function drawMessageWarning", maxsplit=1
    )[1].split("export function drawMessageError", maxsplit=1)[0]

    assert "arguments[0][PROCESS_GROUP_RENDER_INFO]" in warning_handler
    assert "getLastProcessGroup(false)" in warning_handler


def test_collapsed_process_details_are_deferred_and_discarded():
    messages = (PROJECT_ROOT / "webui" / "js" / "messages.js").read_text(
        encoding="utf-8"
    )
    process_group_dom = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "messages"
        / "process-group"
        / "process-group-dom.js"
    ).read_text(encoding="utf-8")

    assert "detailPending: !shouldRenderDetail" in messages
    assert "discardProcessStepDetail(step)" in messages
    assert 'step.__renderDetail !== "function"' in messages
    assert "estimateKvpTextSize(kvps)" in messages
    assert "kvps: expanded ? kvps : null" in messages
    assert "await Promise.allSettled(pending)" in process_group_dom
    assert "step.__setExpanded(shouldExpandStep)" in process_group_dom


def test_user_messages_share_collapse_behavior_without_clipping_attachments():
    messages = (PROJECT_ROOT / "webui" / "js" / "messages.js").read_text(
        encoding="utf-8"
    )
    message_css = (PROJECT_ROOT / "webui" / "css" / "messages.css").read_text(
        encoding="utf-8"
    )
    action_button_css = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "messages"
        / "action-buttons"
        / "simple-action-buttons.css"
    ).read_text(encoding="utf-8")

    assert 'contentSelector = ":scope > .message-body"' in messages
    assert 'collapseContent?.classList.add("message-collapse-content")' in messages
    assert 'refreshCollapsibleMessageOverflow(history)' in messages
    assert 'refreshCollapsibleMessageOverflow(entry.target)' in messages
    assert 'measureMessageCollapseOverflow(collapseContent' in messages
    assert '":scope > .message-text",\n  );' in messages
    assert "attachmentsContainer.classList.add(\"attachments-container\")" in messages
    assert ".message.message-collapsible .message-collapse-content" in message_css
    assert ".message.message-agent-response.message-collapsible" in message_css
    assert ".attachments-container.message-collapse-content" not in message_css
    assert ".message-user .step-action-buttons .expand-btn" in action_button_css
    assert "order: 1" in action_button_css


def test_message_collapse_ignores_hidden_replay_geometry_and_real_short_text():
    if not shutil.which("node"):
        pytest.skip("Node.js is required to execute the collapse regression.")

    source = MESSAGE_COLLAPSE_JS.read_bytes()
    module_url = "data:text/javascript;base64," + base64.b64encode(source).decode(
        "ascii"
    )
    script = f"""
import {{ measureMessageCollapseOverflow }} from {module_url!r};

function assert(condition, message) {{
  if (!condition) throw new Error(message);
}}

let historyWidth = 0;
const history = {{
  get clientWidth() {{ return historyWidth || 24; }},
}};
const content = {{
  isConnected: true,
  clientWidth: 210,
  clientHeight: 34,
  scrollHeight: 280,
  getBoundingClientRect: () => ({{ width: 210 }}),
  closest: (selector) => selector === "#chat-history" ? history : null,
}};
globalThis.getComputedStyle = (element) => ({{
  fontSize: "16px",
  paddingLeft: element === history ? "12px" : "0px",
  paddingRight: element === history ? "12px" : "0px",
}});

assert(
  measureMessageCollapseOverflow(content) === null,
  "zero-width replay staging must not mark short text as overflowing",
);

historyWidth = 800;
content.scrollHeight = 34;
assert(
  measureMessageCollapseOverflow(content) === false,
  "a laid-out one-line message must not expose Show More",
);

content.clientHeight = 240;
content.scrollHeight = 420;
assert(
  measureMessageCollapseOverflow(content) === true,
  "a body taller than the collapsed preview must expose Show More",
);
assert(
  measureMessageCollapseOverflow(content, {{ expanded: true }}) === true,
  "expanded long bodies must retain their Show Less control",
);
"""
    subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        text=True,
    )


def test_process_groups_are_atomic_and_page_steps_in_fifties():
    messages = (PROJECT_ROOT / "webui" / "js" / "messages.js").read_text(
        encoding="utf-8"
    )
    group_css = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "messages"
        / "process-group"
        / "process-group.css"
    ).read_text(encoding="utf-8")

    assert "const PROCESS_GROUP_STEP_PAGE_SIZE = 50" in messages
    assert 'classifyMessageRenderUnits(messages, _processStepTypes)' in messages
    assert "getUnitKeys: getMessageRenderUnitKeys" in messages
    assert "getProcessGroupRenderMessages(windowMessages)" in messages
    assert "const addedMessageKeys = _messageWindow.merge" in messages
    assert "addedMessageKeys.has(getMessageCacheKey(message))" in messages
    assert 'button.className = "process-group-show-more"' in messages
    assert "current + PROCESS_GROUP_STEP_PAGE_SIZE" in messages
    assert "group.dataset.fullStartTimestamp" in messages
    assert 'else if (log.type === "util")' in messages
    assert 'group?.classList.contains("utility-only")' in messages
    assert "allowCompletedGroup: false" in messages
    assert ".process-group.utility-only {" in group_css
    assert ".show-utility-messages .process-group.utility-only" in group_css
    assert ".process-group.utility-only[hidden]" not in group_css
    assert ".process-group-show-more" in group_css
    show_more_css = group_css.split(".process-group-show-more {", 1)[1].split(
        "}", 1
    )[0]
    assert "text-decoration: none" in show_more_css
    assert "opacity: 0.7" in show_more_css
    assert "text-decoration: underline" not in show_more_css


def test_detail_preferences_await_materialization_and_select_current_step():
    if not shutil.which("node"):
        pytest.skip("Node.js is required to execute the detail-mode regression.")

    source = PROCESS_GROUP_DOM_JS.read_text(encoding="utf-8").replace(
        'import { store as preferencesStore } from '
        '"/components/sidebar/bottom/preferences/preferences-store.js";\n',
        'const preferencesStore = { detailMode: "current", showUtils: false };\n',
    )
    module_url = "data:text/javascript;base64," + base64.b64encode(
        source.encode("utf-8")
    ).decode("ascii")
    script = f"""
import {{ applyModeSteps }} from {module_url!r};

function assert(condition, message) {{
  if (!condition) throw new Error(message);
}}

function makeClasses(initial = []) {{
  const values = new Set(initial);
  return {{
    contains: (name) => values.has(name),
    toggle(name, force) {{
      if (force) values.add(name);
      else values.delete(name);
    }},
  }};
}}

function makeStep(name, util = false) {{
  const step = {{
    name,
    classList: makeClasses(util ? ["message-util"] : []),
    detailReady: false,
  }};
  step.__setExpanded = (expanded) => new Promise((resolve) => {{
    queueMicrotask(() => {{
      step.classList.toggle("expanded", expanded);
      step.detailReady = expanded;
      resolve();
    }});
  }});
  return step;
}}

function makeGroup(steps, complete = false) {{
  const group = {{
    steps,
    complete,
    classList: makeClasses(),
    hasAttribute: (name) => complete && name === "data-group-complete",
    querySelector: (selector) =>
      complete && selector === ".process-group-response" ? {{}} : null,
    querySelectorAll: (selector) => selector === ".process-step" ? steps : [],
  }};
  group.__setExpanded = async (expanded) => {{
    group.classList.toggle("expanded", expanded);
  }};
  return group;
}}

const completedSteps = [makeStep("old")];
const currentSteps = [makeStep("first"), makeStep("current"), makeStep("util", true)];
const groups = [makeGroup(completedSteps, true), makeGroup(currentSteps)];
const history = {{
  dataset: {{ messageWindowEnd: "100", messageWindowTotal: "100" }},
  querySelectorAll: (selector) => selector === ".process-group" ? groups : [],
}};
globalThis.document = {{
  getElementById: (id) => id === "chat-history" ? history : null,
}};

await applyModeSteps("expanded", false);
assert(
  [...completedSteps, ...currentSteps].every((step) => step.detailReady),
  "ALL must await every visible step detail",
);

await applyModeSteps("collapsed", false);
assert(
  [...completedSteps, ...currentSteps].every((step) => !step.detailReady),
  "NO must collapse every visible step",
);

await applyModeSteps("current", false);
assert(!completedSteps[0].detailReady, "STEP must not open completed history");
assert(!currentSteps[0].detailReady, "STEP must collapse older active steps");
assert(currentSteps[1].detailReady, "STEP must materialize the current visible step");
assert(!currentSteps[2].detailReady, "hidden utility steps must not become current");

history.dataset.messageWindowEnd = "50";
await applyModeSteps("current", false);
assert(
  currentSteps.every((step) => !step.detailReady),
  "STEP must not treat a historical window boundary as the live current step",
);
"""
    subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        text=True,
    )


def test_virtual_rebuild_cancels_stale_scroller_effects():
    if not shutil.which("node"):
        pytest.skip("Node.js is required to execute the scroller regression.")

    source = SCROLLER_JS.read_bytes()
    module_url = "data:text/javascript;base64," + base64.b64encode(source).decode(
        "ascii"
    )
    script = f"""
import {{ cancelPendingScroll }} from {module_url!r};

function assert(condition, message) {{
  if (!condition) throw new Error(message);
}}

let delayedScrollRan = false;
const timeoutId = setTimeout(() => {{ delayedScrollRan = true; }}, 30);
const element = {{
  dataset: {{
    scrollerTimeout: String(Number(timeoutId)),
    scrollerReapplySnapshot: "200",
    scrollingTo: "900",
  }},
  scrollTop: 240,
  scrollCalls: [],
  scrollTo(options) {{ this.scrollCalls.push(options); }},
}};

cancelPendingScroll(element);
await new Promise((resolve) => setTimeout(resolve, 60));

assert(!delayedScrollRan, "a stale delayed auto-scroll must be canceled");
assert(element.scrollCalls.length === 1, "an in-flight smooth scroll must be stopped");
assert(element.scrollCalls[0].top === 240, "canceling must retain the current offset");
assert(!("scrollerTimeout" in element.dataset), "timeout state must be cleared");
assert(!("scrollingTo" in element.dataset), "smooth-scroll state must be cleared");
"""
    subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        text=True,
    )


def test_virtual_window_preserves_live_and_navigation_contracts():
    messages = (PROJECT_ROOT / "webui" / "js" / "messages.js").read_text(
        encoding="utf-8"
    )
    message_css = (PROJECT_ROOT / "webui" / "css" / "messages.css").read_text(
        encoding="utf-8"
    )
    navigation = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "chat"
        / "navigation"
        / "chat-navigation-store.js"
    ).read_text(encoding="utf-8")

    assert "_messageRenderGeneration" in messages
    assert "result: { element: null, virtualized: true, dontScroll: true }" in messages
    assert 'scrollMessageWindowToEdge("start")' in navigation
    assert 'scrollMessageWindowToEdge("end")' in navigation
    assert 'loadAdjacentMessageWindow("older")' in navigation
    assert 'loadAdjacentMessageWindow("newer")' in navigation
    assert "_messageWindowFollowTail" in messages
    assert "hasUserScrollIntent" in messages
    assert "cancelPendingScroll(history)" in messages
    assert "createMessageWindowStagingHistory(history)" in messages
    assert "history.replaceChildren(...stagedChildren)" in messages
    assert 'element.classList.add("message-window-restored")' in messages
    assert "createMessageWindowIndicator" in messages
    assert 'document.createElement("div")' in messages
    assert "Loading ${label} messages" in messages
    assert "Load ${Math.min" not in messages
    assert "overflow-anchor: none" in message_css
    assert ".message-container.message-window-restored" in message_css
