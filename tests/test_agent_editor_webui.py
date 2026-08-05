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

    assert "Create agent" in switcher
    assert "Edit agent" in switcher
    assert "Manage agents" in switcher
    assert "createAgentProfileChat" not in switcher
    assert all(
        label in modal
        for label in (
            "Identity & models",
            "Prompt files",
            "Tools",
            "Skills",
            "Review & test",
            "Standard tools — recommended",
            "No optional tools",
            "Custom selection",
            "Save & test",
        )
    )
    assert 'aria-label="Editor mode"' in modal
    assert "Allow selected" in modal and "Block selected" in modal
    assert "Your changes override the built-in profile. The original files stay unchanged." in modal
    assert "This project has a higher-priority tool policy." in modal
    assert "Unavailable · retained" in modal
    assert "Edit / Create override" in modal
    assert 'promptDisplayState(prompt)' in modal
    assert 'promptSourceChain($store.agentEditor.selectedPromptDraft)' in modal
    assert "Will reset to inherited on save." in modal
    assert all(
        label in STORE.read_text(encoding="utf-8")
        for label in (
            "Model preset",
            "Project references",
            "Active sessions",
            "Profile content",
        )
    )
    assert "agent-profile-avatar" in switcher
    switcher_mixin = SWITCHER_MIXIN.read_text(encoding="utf-8")
    assert "avatar_url" in switcher_mixin
    assert 'callJsonApi("/plugins/_agent_editor/agent_editor"' in switcher_mixin
    assert "@keydown.ctrl.s.prevent" in modal
    assert "@media (max-width: 760px)" in modal
    assert modal.count("data-modal-footer") == 1


def test_agent_editor_store_has_no_conversational_or_model_builder_path() -> None:
    source = STORE.read_text(encoding="utf-8")
    switcher_source = (
        ROOT / "plugins" / "_model_config" / "webui" / "switcher-mixin.js"
    ).read_text(encoding="utf-8")

    assert 'createStore("agentEditor", model)' in source
    assert "CREATE_AGENT_PROFILE_PROMPT" not in switcher_source
    assert "a0-create-agent" not in switcher_source
    assert "save_agent_data" not in source
    assert not re.search(r"utility.?model|call.?model|generate", source, re.IGNORECASE)
    assert all(
        f"setMode('advanced', '{section}')" in MODAL.read_text(encoding="utf-8")
        for section in ("1", "2", "3")
    )


@pytest.mark.skipif(not shutil.which("node"), reason="node is required")
def test_local_slugging_and_fresh_chat_profile_selection_are_deterministic() -> None:
    source = STORE.read_text(encoding="utf-8")
    source = re.sub(r"^import .*?;\n", "", source, flags=re.MULTILINE)
    harness = r"""
const calls = [];
const createStore = (_name, value) => value;
const callJsonApi = async (endpoint, payload) => {
  calls.push({ endpoint, payload });
  return endpoint === "/chat_create" ? { ok: true, ctxid: "fresh-chat" } : { ok: true };
};
const fetchApi = async () => ({ ok: true, json: async () => ({}) });
const closeModal = async () => {};
const openModal = async () => {};
const showConfirmDialog = async () => true;
const chatsStore = {
  selected: "old-chat",
  selectChat: async (id) => calls.push({ endpoint: "selectChat", payload: id }),
};
const modelConfigStore = { loadAgentProfiles: async () => {} };
globalThis.window = globalThis;
globalThis.document = { dispatchEvent: (event) => calls.push({ endpoint: "event", payload: event.type }) };
globalThis.CustomEvent = class { constructor(type) { this.type = type; } };
globalThis.sessionStorage = { setItem: () => {}, getItem: () => "", removeItem: () => {} };
globalThis.localStorage = { setItem: () => {}, getItem: () => "" };
globalThis.requestAnimationFrame = callback => callback();
"""
    checks = r"""
if (slugifyProfileName("  Crème Brûlée__Lab  ") !== "creme-brulee-lab") throw new Error("slug mismatch");
if (slugifyProfileName("東京") !== "") throw new Error("unsupported slug mismatch");
store.state = {
  profile: { id: "new-agent", avatar_url: "", metadata: { title: {}, description: {}, context: {}, avatar: {} } },
  prompts: [
    { filename: "agent.system.main.specifics.md", group: "2.1", group_label: "Agent instructions", effective: "", inherited: "", source_chain: [] },
    { filename: "agent.system.main.communication.md", group: "2.4", group_label: "Communication", effective: "Inherited comm", inherited: "Inherited comm", source_chain: ["Framework", "Researcher"], state: "Inherited", has_override: false },
  ],
  model_preset: { has_override: false },
  tools: { policy: { mode: "inherit" }, has_override: false, catalog: [] },
  skills: { policy: { mode: "inherit" }, has_override: false, catalog: [] },
};
store.makeDraft(true);
store.state.tools.catalog = [{ id: "local:shell", name: "shell", label: "Shell", origin: "Agent Zero", available: true }];
store.draft.toolPolicy = { mode: "custom", default: "allow", allowed: [], blocked: ["local:shell"] };
if (JSON.stringify(store.skillWarnings({ allowed_tools: ["shell"] })) !== JSON.stringify(["shell"])) throw new Error("live skill warning missing");
store.draft.title = "Preserved Agent";
store.onNameInput();
store.instructions.value = "Preserved instructions";
store.setEasyToolMode("off");
const communication = store.draft.prompts["agent.system.main.communication.md"];
if (store.isPromptEditing(communication.filename) || store.promptDisplayState(communication) !== "Inherited") throw new Error("inherited prompt was editable");
store.beginPromptEdit(communication.filename);
communication.value += "\nNew rule";
store.markPromptSet(communication.filename);
if (store.promptDisplayState(communication) !== "Overridden here") throw new Error("override state missing");
if (store.promptSourceChain(communication) !== "Framework → Researcher → Your override") throw new Error("override chain missing");
store.resetPrompt(communication.filename);
if (store.isPromptEditing(communication.filename) || store.promptDisplayState(communication) !== "Reset to inherited") throw new Error("reset state mismatch");
const draftBeforeModes = JSON.stringify(store.draft);
store.setMode("advanced", "2");
store.setMode("easy");
if (store.section !== "2" || JSON.stringify(store.draft) !== draftBeforeModes) throw new Error("mode switch lost draft");
store.intent = { contextId: "source-chat" };
await store.openFreshChat("researcher", true);
const endpoints = calls.map((item) => item.endpoint);
const expected = ["/chat_create", "/agent_profile_set", "/plugins/_model_config/model_override", "selectChat", "event"];
if (JSON.stringify(endpoints) !== JSON.stringify(expected)) throw new Error(JSON.stringify(calls));
if (calls[1].payload.agent_profile !== "researcher") throw new Error("profile not selected");
if (calls[2].payload.action !== "clear") throw new Error("chat preset override not cleared");
if (store.readyNoteContext !== "fresh-chat") throw new Error("ready note missing");
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
