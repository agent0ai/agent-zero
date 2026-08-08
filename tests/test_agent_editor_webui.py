from __future__ import annotations

import base64
from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "plugins" / "_agent_editor" / "webui" / "agent-editor-store.js"
MODAL = ROOT / "plugins" / "_agent_editor" / "webui" / "main.html"
SWITCHER = (
    ROOT
    / "plugins"
    / "_model_config"
    / "extensions"
    / "webui"
    / "chat-input-progress-start"
    / "model-switcher.html"
)
SWITCHER_MIXIN = ROOT / "plugins" / "_model_config" / "webui" / "switcher-mixin.js"


def test_agent_editor_surface_has_normative_entry_points_and_accessible_controls() -> None:
    modal = MODAL.read_text(encoding="utf-8")
    switcher = SWITCHER.read_text(encoding="utf-8")
    tool_section = re.search(
        r'data-agent-editor-section="3".*?(?=<section x-show="\$store\.agentEditor\.section === \'4\'")',
        modal,
        re.DOTALL,
    ).group(0)
    skill_section = re.search(
        r'data-agent-editor-section="4".*?(?=<section x-show="\$store\.agentEditor\.section === \'5\'")',
        modal,
        re.DOTALL,
    ).group(0)
    easy_surface = modal.split('<div class="agent-advanced"', 1)[0]

    assert "Create agent" not in switcher
    assert "Manage agents" in switcher
    assert '<div class="agent-profile-row"' in switcher
    assert 'class="agent-profile-row-edit"' in switcher
    assert ':aria-label="`Edit ${profile.label || profile.key}`"' in switcher
    assert "profileId: profile.key" in switcher
    assert "<span>Edit</span>" in switcher
    assert "profile.customized" not in switcher
    assert 'class="model-switcher-item agent-profile-edit"' not in switcher
    assert "min-height: 24px" in re.search(
        r"\.agent-profile-row-edit\s*\{([^}]*)\}", switcher
    ).group(1)
    assert "createAgentProfileChat" not in switcher
    assert all(
        label in modal
        for label in (
            "Identity & models",
            "Prompt files",
            "Tools",
            "Skills",
            "Review",
            "Save & test",
        )
    )
    assert 'aria-label="Editor mode"' in modal
    assert "Allow selected" in modal and "Block selected" in modal
    assert "No optional tools" not in modal
    assert 'class="agent-model-preset-picker"' in modal
    assert 'x-model="$store.agentEditor.draft.modelPreset"' in modal
    assert '`Use current preset (${$store.agentEditor.state.model_preset.effective})`' in modal
    assert 'x-for="preset in $store.agentEditor.state.model_presets"' in modal
    assert "Edit Presets" in modal
    assert "Manage presets" not in modal
    assert "model-preset-row" not in modal
    assert 'class="easy-tool-details"' not in modal
    assert 'x-for="tool in $store.agentEditor.toolCatalog"' in easy_surface
    assert ':checked="$store.agentEditor.isToolAllowed(tool)"' in easy_surface
    assert "$store.agentEditor.setEasyToolAllowed(tool.id, $event.target.checked)" in easy_surface
    assert "Choose tools in Advanced" not in modal
    assert "To enable or disable skills, click Advanced." in easy_surface
    assert 'x-for="skill in $store.agentEditor' not in easy_surface
    assert 'class="easy-tool-actions"' not in modal
    assert 'class="policy-editor" :disabled="$store.agentEditor.draft.toolPolicy.mode !== \'custom\'"' in tool_section
    assert 'class="policy-editor" :disabled="$store.agentEditor.draft.skillPolicy.mode !== \'custom\'"' in skill_section
    assert 'class="policy-lists"' in tool_section and 'class="policy-lists"' in skill_section
    assert 'aria-label="Block selected tools"' in tool_section
    assert 'aria-label="Allow selected tools"' in tool_section
    assert 'aria-label="Block selected skills"' in skill_section
    assert 'aria-label="Allow selected skills"' in skill_section
    assert '<details class="policy-description"' not in tool_section
    assert '<details class="policy-description"' not in skill_section
    assert tool_section.count('class="policy-item-description"') == 2
    assert skill_section.count('class="policy-item-description"') == 2
    assert "Your changes override the built-in profile. The original files stay unchanged." in modal
    assert 'x-model="$store.agentEditor.projectName"' in modal
    assert 'x-init="$nextTick(() => $el.value = $store.agentEditor.projectName)"' in modal
    assert '@change="$store.agentEditor.onScopeChanged()"' in modal
    assert '<option value="">Global</option>' in modal
    assert 'x-for="project in $store.agentEditor.projects"' in modal
    assert 'x-show="profile.deletable"' in modal
    assert 'x-show="profile.scope_has_overrides"' in modal
    assert "project_override_active" not in modal
    assert "profile.origin === 'Custom'" not in modal
    assert "Scope:" in modal
    assert "Unavailable — kept in your settings" in modal
    assert "Customize this file" not in modal
    assert 'role="tablist" aria-label="Prompt view"' in modal
    assert "No prompt files match your search." in modal
    assert "Saving will change exactly these files — nothing else." in modal
    assert "Review & test" not in modal
    assert "Refresh change plan" not in modal
    assert "Back to Easy" not in modal
    assert "This agent has a detailed prompt" not in modal
    assert "Replace with simple instructions" not in modal
    assert "easyInstructionsEditable" not in modal
    assert '<textarea id="agent-editor-instructions"' in modal
    assert "<h2" not in modal
    assert "Section 1" not in modal
    assert '<textarea id="agent-editor-description" rows="2"' in modal
    assert "When new tools are installed later" in modal
    assert "When new skills are installed later" in modal
    assert "Block until reviewed" in modal
    assert "No blocked tools" in modal and "No blocked skills" in modal
    assert "policy-description" not in modal and "-webkit-line-clamp:2" not in modal
    assert 'class="prompt-file-list" role="region" aria-label="Prompt file list" tabindex="0"' in modal
    assert 'class="prompt-editor" role="region" aria-label="Selected prompt file" tabindex="0"' in modal
    assert 'width:1.5rem; height:1.5rem' in modal
    assert "moveAllVisibleTools(false)" in modal and "moveAllVisibleSkills(false)" in modal
    assert 'class="agent-editor-heading"' in modal
    assert ':aria-invalid=' in modal
    assert modal.count('role="alert"') >= 4
    assert "Fix ${$store.agentEditor.validationIssues().length}" in modal
    assert modal.count("$store.agentEditor.validationIssues().length > 0") == 2
    assert "Delete all customizations in" in modal
    assert 'input[type="checkbox"]' in modal and "appearance:none" in modal
    assert 'promptDisplayState(prompt)' in modal
    assert 'promptSourceChain($store.agentEditor.selectedPromptDraft)' in modal
    assert "Will reset to inherited on save." in modal
    assert ':title="prompt.filename"' not in modal
    assert "promptEditPending($store.agentEditor.selectedPromptDraft)" in modal
    assert 'aria-label="Discard current edit"' in modal
    assert 'aria-label="Accept current edit"' in modal
    assert ':readonly="!$store.agentEditor.isPromptEditing' not in modal
    assert ".prompt-pane textarea:focus-visible { outline-offset:-2px; }" in modal
    assert all(
        label in STORE.read_text(encoding="utf-8")
        for label in (
            "Model preset",
            "Projects using this agent",
            "Open chats using this agent",
            "Saved settings",
        )
    )
    assert "agent-profile-avatar" in switcher
    assert '<button type="button" class="model-switcher-item agent-profile-item"' in switcher
    assert '<div class="model-switcher-item agent-profile-item"' not in switcher
    switcher_mixin = SWITCHER_MIXIN.read_text(encoding="utf-8")
    assert "avatar_url" in switcher_mixin
    assert "BUILT_IN_AGENT_COLORS" in switcher_mixin
    assert "customized: !!profile.has_user_overrides" not in switcher_mixin
    assert 'name="palette"' in modal and 'name="add_photo_alternate"' in modal
    assert ".easy-tool-summary" not in modal
    assert "grid-template-columns:minmax(0,1fr) 2.5rem minmax(0,1fr)" in modal
    assert ".policy-lists .policy-transfer-actions { flex-direction:row; }" in modal
    store_source = STORE.read_text(encoding="utf-8")
    assert "easyToolsOpen" not in store_source
    assert "easySkills" not in store_source
    assert "get toolMode" not in store_source
    assert "get easyTools" not in store_source
    assert "firstSentence" not in store_source
    assert '.agent-editor [aria-invalid="true"]' not in modal
    assert ".field-error { display:block; color:var(--color-text-secondary)" in modal
    assert 'callJsonApi("/plugins/_agent_editor/agent_editor"' in switcher_mixin
    assert "@keydown.ctrl.s.prevent" in modal
    assert "@media (max-width: 760px)" in modal
    assert modal.count("data-modal-footer") == 1


def test_agent_editor_store_has_no_conversational_or_model_builder_path() -> None:
    source = STORE.read_text(encoding="utf-8")
    modal = MODAL.read_text(encoding="utf-8")
    switcher_source = (
        ROOT / "plugins" / "_model_config" / "webui" / "switcher-mixin.js"
    ).read_text(encoding="utf-8")

    assert 'createStore("agentEditor", model)' in source
    assert "CREATE_AGENT_PROFILE_PROMPT" not in switcher_source
    assert "a0-create-agent" not in switcher_source
    assert "save_agent_data" not in source
    assert not re.search(r"utility.?model|call.?model|generate", source, re.IGNORECASE)
    assert "Advanced <span" not in modal


@pytest.mark.skipif(not shutil.which("node"), reason="node is required")
def test_local_slugging_and_fresh_chat_profile_selection_are_deterministic() -> None:
    source = STORE.read_text(encoding="utf-8")
    source = re.sub(r"^import .*?;\n", "", source, flags=re.MULTILINE)
    harness = r"""
const calls = [];
const confirmations = [];
const createStore = (_name, value) => value;
const callJsonApi = async (endpoint, payload) => {
  calls.push({ endpoint, payload });
  return endpoint === "/chat_create" ? { ok: true, ctxid: "fresh-chat" } : { ok: true };
};
const fetchApi = async () => ({ ok: true, json: async () => ({}) });
const closeModal = async () => {};
const openModal = async () => {};
const showConfirmDialog = async options => { confirmations.push(options); return false; };
const chatsStore = {
  selected: "old-chat",
  selectChat: async (id) => calls.push({ endpoint: "selectChat", payload: id }),
};
const modelConfigStore = {
  loadAgentProfiles: async () => {},
  getAgentProfileVisual: (_id, label) => ({ color: "#123456", url: "", initials: label?.[0] || "A" }),
};
globalThis.window = globalThis;
globalThis.document = {
  dispatchEvent: (event) => calls.push({ endpoint: "event", payload: event.type }),
  createElement: () => ({ textContent: "", get innerHTML() { return this.textContent; } }),
  addEventListener: () => {},
  removeEventListener: () => {},
};
globalThis.CustomEvent = class { constructor(type) { this.type = type; } };
globalThis.sessionStorage = { setItem: () => {}, getItem: () => "", removeItem: () => {} };
globalThis.localStorage = { setItem: () => {}, getItem: () => "" };
globalThis.requestAnimationFrame = callback => callback();
"""
    checks = r"""
if (slugifyProfileName("  Crème Brûlée__Lab  ") !== "creme-brulee-lab") throw new Error("slug mismatch");
if (slugifyProfileName("東京") !== "") throw new Error("unsupported slug mismatch");
store.draft = { title: "stale" };
store.initialDraft = { title: "clean" };
store.intent = { view: "manage", contextId: "" };
const modalTitle = { textContent: "" };
const modalElement = { querySelector: selector => selector === ".modal-title" ? modalTitle : null };
const modalInner = { classList: { toggle: () => {} } };
await store.mount({
  closest: selector => selector === ".modal" ? modalElement : selector === ".modal-inner" ? modalInner : null,
  querySelector: () => null,
});
if (store.draft !== null || store.initialDraft !== null || store.dirty || store.loading) throw new Error("manage mount kept stale draft state");
if (modalTitle.textContent !== "Manage agents") throw new Error("manage mount title mismatch");
store.state = {
  profile: { id: "new-agent", avatar_url: "", metadata: { title: {}, description: {}, context: {}, avatar: {} } },
  prompts: [
    { filename: "agent.system.main.specifics.md", group: "2.1", group_label: "Agent instructions", effective: "", inherited: "", source_chain: [] },
    { filename: "agent.system.main.communication.md", group: "2.4", group_label: "Communication", effective: "Inherited comm", inherited: "Inherited comm", source_chain: ["Framework", "Researcher"], state: "Inherited", has_override: false },
  ],
  model_preset: { has_override: false },
  tools: { policy: { mode: "inherit" }, effective_policy: { mode: "inherit", default: "allow", allowed: [], blocked: [] }, has_override: false, catalog: [] },
  skills: { policy: { mode: "inherit" }, effective_policy: { mode: "inherit", default: "allow", allowed: [], blocked: [] }, has_override: false, catalog: [] },
};
store.makeDraft(true);
if (await store.previewPlan()) throw new Error("invalid plan unexpectedly succeeded");
if (store.planStatus !== "blocked" || store.error || store.validationIssues().length !== 2) throw new Error("blocked plan state mismatch");
if (store.fieldIssue("name")?.message !== "Agent name is required.") throw new Error("inline name issue missing");
await store.save();
if (store.error) throw new Error("validation leaked into dismissible error banner");
store.state.profile.id = "new-agent";
store.state.profile.origin = "Built-in";
store.state.profile.metadata.title = { inherited_source: "agents/new-agent/agent.yaml" };
if (store.metadataProvenance("title") !== "Using the default") throw new Error("default provenance mismatch");
store.profiles = [{ id: "researcher", title: "Researcher" }];
store.state.profile.metadata.title = { inherited_source: "agents/researcher/agent.yaml" };
if (store.metadataProvenance("title") !== "Inherited from Researcher") throw new Error("inherited provenance mismatch");
store.state.profile.metadata.title.has_override = true;
if (store.metadataProvenance("title") !== "Customized by you") throw new Error("custom provenance mismatch");
store.state.tools.catalog = [
  { id: "local:shell", name: "shell", label: "Shell", origin: "Agent Zero", available: true },
  { id: "local:gone", name: "gone", label: "Gone", origin: "Unavailable", available: false },
];
store.draft.toolPolicy = { mode: "custom", default: "allow", allowed: [], blocked: ["local:shell"] };
if (JSON.stringify(store.skillWarnings({ allowed_tools: ["shell"] })) !== JSON.stringify(["shell"])) throw new Error("live skill warning missing");
if (store.toolCatalog.length !== 1 || store.isToolAllowed(store.state.tools.catalog[0])) throw new Error("Easy custom tool state mismatch");
await store.moveAllVisibleTools(true);
if (confirmations.at(-1)?.title !== "Allow 1 shown tool?" || store.isToolAllowed(store.state.tools.catalog[0])) throw new Error("filtered bulk confirmation mismatch");
confirmations.length = 0;
store.selectedAllowedTools = ["local:shell"];
store.useStandardTools();
if (store.draft.toolPolicy.mode !== "inherit" || !store.isToolAllowed(store.state.tools.catalog[0]) || store.filteredTools(true).length !== 1 || store.selectedAllowedTools.length) throw new Error("standard tool state mismatch");
store.setEasyToolAllowed("local:shell", false);
if (store.draft.toolPolicy.mode !== "custom" || store.draft.toolPolicy.default !== "allow" || store.isToolAllowed(store.state.tools.catalog[0])) throw new Error("Easy uncheck did not block tool");
store.setEasyToolAllowed("local:shell", true);
if (store.draft.toolPolicy.mode !== "inherit" || !store.isToolAllowed(store.state.tools.catalog[0]) || store.draft.toolPolicy.blocked.length) throw new Error("Easy recheck did not restore standard access");
store.draft.toolPolicy = { mode: "custom", default: "block", allowed: [], blocked: [] };
store.setEasyToolAllowed("local:shell", true);
if (!store.isToolAllowed(store.state.tools.catalog[0]) || !store.draft.toolPolicy.allowed.includes("local:shell")) throw new Error("Easy check ignored block-by-default policy");
store.setEasyToolAllowed("local:shell", false);
if (store.isToolAllowed(store.state.tools.catalog[0]) || store.draft.toolPolicy.allowed.length) throw new Error("Easy uncheck ignored block-by-default policy");
store.useStandardTools();
store.chooseTools();
if (store.draft.toolPolicy.mode !== "custom" || store.draft.toolPolicy.default !== "allow" || store.section !== "3") throw new Error("custom tool editor did not open");
store.useStandardTools();
store.state.tools.effective_policy = { mode: "inherit", default: "block", allowed: [], blocked: ["local:shell"] };
store.chooseTools();
if (store.draft.toolPolicy.default !== "allow" || store.draft.toolPolicy.blocked.length) throw new Error("inactive inherited exceptions leaked into custom policy");
store.projectName = "demo";
store.state.tools.effective_policy = { mode: "custom", default: "allow", allowed: [], blocked: ["local:shell"] };
store.useStandardTools();
if (store.isToolAllowed(store.state.tools.catalog[0])) throw new Error("project scope ignored inherited tool restriction");
store.setEasyToolAllowed("local:shell", true);
if (store.draft.toolPolicy.mode !== "custom" || !store.isToolAllowed(store.state.tools.catalog[0])) throw new Error("project scope did not customize inherited policy");
store.setEasyToolAllowed("local:shell", false);
if (store.draft.toolPolicy.mode !== "inherit" || store.isToolAllowed(store.state.tools.catalog[0])) throw new Error("project scope did not restore inherited policy");
store.projectName = "";
store.state.tools.effective_policy = { mode: "inherit", default: "allow", allowed: [], blocked: [] };
store.state.skills.catalog = [
  { name: "Research", path: "skills/research/SKILL.md", origin: "Agent Zero", description: "Research sources", available: true, tags: [], allowed_tools: [] },
  { name: "Gone", path: "skills/gone/SKILL.md", origin: "Unavailable", description: "Missing skill", available: false, tags: [], allowed_tools: [] },
];
store.draft.skillPolicy = { mode: "custom", default: "allow", allowed: [], blocked: ["Research"] };
if (store.skillCatalog.length !== 1 || store.filteredSkills(false).length !== 1 || store.filteredSkills(true).length !== 1) throw new Error("custom skill catalog mismatch");
store.selectedBlockedSkills = ["Research"];
store.useStandardSkills();
if (store.draft.skillPolicy.mode !== "inherit" || store.filteredSkills(true).length !== 1 || store.filteredSkills(false).length || store.selectedBlockedSkills.length) throw new Error("standard skill summary mismatch");
store.chooseSkills();
if (store.draft.skillPolicy.mode !== "custom" || store.draft.skillPolicy.default !== "allow") throw new Error("custom skill editor did not open");
store.draft.title = "Preserved Agent";
store.onNameInput();
store.instructions.value = "Preserved instructions";
store.draft.creating = false;
store.instructions.value = "";
if (store.fieldIssue("instructions")) throw new Error("existing empty instructions were rejected");
store.instructions.value = "Preserved instructions";
store.markPromptSet("agent.system.main.specifics.md");
if (store.instructions.reset || store.promptEditPending(store.instructions)) throw new Error("Easy instructions did not update its edit checkpoint");
store.restoreInstructions();
if (!store.instructions.reset || store.instructions.value !== "" || store.promptEditPending(store.instructions)) throw new Error("default instructions were not restored");
store.draft.creating = true;
store.instructions.value = "Preserved instructions";
store.instructions.reset = false;
const communication = store.draft.prompts["agent.system.main.communication.md"];
if (store.filteredPromptFiles("2.4")[0] !== communication) throw new Error("grouped prompt filter mismatch");
if (store.promptEditPending(communication) || store.promptDisplayState(communication) !== "Default") throw new Error("default prompt checkpoint mismatch");
communication.value += "\nNew rule";
store.onPromptInput(communication.filename);
if (!store.promptEditPending(communication)) throw new Error("prompt edit actions did not appear");
if (!store.buildPatch().prompts.set[communication.filename].endsWith("New rule")) throw new Error("pending prompt edit missing from sparse patch");
store.discardPromptEdit(communication.filename);
if (store.promptEditPending(communication) || communication.value !== "Inherited comm") throw new Error("prompt edit was not discarded");
if (store.buildPatch().prompts.set[communication.filename]) throw new Error("discarded prompt edit remained in sparse patch");
communication.value += "\nNew rule";
store.onPromptInput(communication.filename);
store.acceptPromptEdit(communication.filename);
if (store.promptEditPending(communication)) throw new Error("prompt edit was not accepted");
if (store.promptDisplayState(communication) !== "Customized by you") throw new Error("customized state missing");
if (store.promptSourceChain(communication) !== "Customized by you") throw new Error("customized provenance missing");
store.resetPrompt(communication.filename);
if (store.promptEditPending(communication) || store.promptDisplayState(communication) !== "Will use the default") throw new Error("reset state mismatch");
const draftBeforeModes = JSON.stringify(store.draft);
store.setMode("advanced", "2");
store.setMode("easy");
if (store.section !== "2" || JSON.stringify(store.draft) !== draftBeforeModes) throw new Error("mode switch lost draft");
store.setMode("advanced", "5");
await Promise.resolve();
await Promise.resolve();
if (store.planStatus !== "ready" || calls.at(-1).payload.action !== "plan") throw new Error("review plan was not computed on entry");
calls.length = 0;
store.intent = { contextId: "source-chat" };
await store.openFreshChat("researcher", true);
const endpoints = calls.map((item) => item.endpoint);
const expected = ["/chat_create", "/projects", "/agent_profile_set", "/plugins/_model_config/model_override", "selectChat", "event"];
if (JSON.stringify(endpoints) !== JSON.stringify(expected)) throw new Error(JSON.stringify(calls));
if (calls[1].payload.action !== "deactivate") throw new Error("global test chat kept a project");
if (calls[2].payload.agent_profile !== "researcher") throw new Error("profile not selected");
if (calls[3].payload.action !== "clear") throw new Error("chat preset override not cleared");
if (store.readyNoteContext !== "fresh-chat") throw new Error("ready note missing");
calls.length = 0;
store.projectName = "demo";
await store.openFreshChat("researcher", false);
if (calls[1].endpoint !== "/projects" || calls[1].payload.action !== "activate" || calls[1].payload.name !== "demo") throw new Error("project test chat did not activate selected scope");
await store.planRemoval(true);
if (!store.pendingMutation?.destructive || store.section !== "5" || store.planStatus !== "ready") throw new Error("removal plan was replaced");
if (calls.at(-1).payload.action !== "plan_remove_changes") throw new Error("removal plan request missing");
if (calls.at(-1).payload.project_name !== "demo") throw new Error("removal request lost selected scope");
store.plan = { written: ["usr/agents/researcher/agent.yaml"], deleted: ["usr/agents/researcher/prompts/old.md"], warnings: [] };
await store.applyPendingMutation();
if (confirmations.length !== 1 || confirmations[0].type !== "danger") throw new Error("danger confirmation missing");
if (!confirmations[0].message.includes("agent.yaml") || !confirmations[0].message.includes("old.md")) throw new Error("planned paths missing from confirmation");
if (confirmations[0].title !== "Delete all customizations for this profile?") throw new Error("cleanup confirmation title mismatch");
"""
    module_source = harness + "\n" + source + "\n" + checks
    module_url = "data:text/javascript;base64," + base64.b64encode(
        module_source.encode("utf-8")
    ).decode("ascii")
    subprocess.run(
        ["node", "--input-type=module", "-e", f"await import('{module_url}')"],
        check=True,
        text=True,
    )
