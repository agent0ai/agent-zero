import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { showConfirmDialog } from "/js/confirmDialog.js";
import { store as notifications } from "/components/notifications/notification-store.js";
export async function refreshBrowserSettingsScope(api, settingsContext, current) {
  if (!settingsContext || settingsContext.pluginName !== "_browser" || !current()) return;
  const config = settingsContext.settings;
  const projectName = settingsContext.projectName || "";
  const agentProfile = settingsContext.agentProfileKey || "";
  const result = await api("/plugins", { action: "get_config", plugin_name: "_browser",
    project_name: projectName, agent_profile: agentProfile });
  if (!current() || settingsContext.pluginName !== "_browser" || settingsContext.settings !== config
    || (settingsContext.projectName || "") !== projectName
    || (settingsContext.agentProfileKey || "") !== agentProfile) return;
  if (result?.ok !== true || !result.data || typeof result.data.runtime_backend !== "string"
    || typeof result.data.host_browser_selection !== "string") throw new Error("Settings readback unavailable");
  // The modal may edit Global settings while selection belongs to a project chat.
  // Only authoritative routing for the modal's own scope may replace its draft.
  config.runtime_backend = result.data.runtime_backend;
  config.host_browser_selection = result.data.host_browser_selection;
}


const API = "/plugins/_a0_connector/browser_bridge_selection";
const identifier = (value) => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$/.test(value);
function parseSelection(value, contextId) {
  const isDefault = contextId === undefined;
  const keys = ["contract", ...(isDefault ? [] : ["context_id"]), "bridge_id", "selected", "browser_control_ready", "reconnect_required"];
  if (!value || typeof value !== "object" || Array.isArray(value)
    || Object.keys(value).length !== keys.length || !keys.every((key) => Object.hasOwn(value, key))
    || value.contract !== (isDefault ? "a0.browser-bridge.default-selection.v1" : "a0.browser-bridge.selection.v1")
    || (!isDefault && value.context_id !== contextId)
    || ["selected", "browser_control_ready", "reconnect_required"].some((key) => typeof value[key] !== "boolean")
    || (value.selected ? !identifier(value.bridge_id) : value.bridge_id !== null)
    || (value.browser_control_ready && (!value.selected || value.reconnect_required))
    || (value.reconnect_required && !value.selected)) throw new Error("Invalid browser selection");
  return { bridgeId: value.bridge_id, selected: value.selected, ready: value.browser_control_ready, reconnect: value.reconnect_required };
}

export function createBridgeSelectionModel({ api, context, notify, confirm, onSelected = async () => {},
  schedule = setInterval, unschedule = clearInterval, visible = () => globalThis.document?.visibilityState !== "hidden" }) {
  return {
    active: false, generation: 0, contextId: "", settingsContext: null, timer: null,
    selection: null, defaultSelection: null, contextState: "not_checked", state: "not_checked", busy: false, loading: false,
    async mount(settingsContext) {
      this.cleanup(); this.active = true; this.contextId = context() || "";
      const generation = this.generation;
      this.settingsContext = settingsContext; await this.refresh();
      if (this.current(generation)) this.timer = schedule(() => {
        if (this.current(generation) && visible()) void this.refresh();
      }, 5000);
    },
    cleanup() {
      this.active = false; this.generation += 1; this.contextId = "";
      if (this.timer !== null) unschedule(this.timer);
      this.timer = null;
      this.settingsContext = null; this.selection = null; this.defaultSelection = null; this.contextState = "not_checked"; this.state = "not_checked";
      this.busy = false; this.loading = false;
    },
    current(generation = this.generation) {
      return this.active && this.generation === generation && (context() || "") === this.contextId;
    },
    selectedHere(bridgeId) { return this.current() && this.selection?.selected && this.selection.bridgeId === bridgeId; },
    selectedDefault(bridgeId) { return this.current() && this.defaultSelection?.selected && this.defaultSelection.bridgeId === bridgeId; },
    canSelect(bridgeId) { return this.current() && this.state === "loaded" && identifier(bridgeId) && !this.busy && !this.loading && !this.selectedDefault(bridgeId); },
    statusText() {
      if (!this.current()) return "Reopen Browser settings to check the current browser selection.";
      if (this.loading && this.state !== "loaded") return "Checking browser control…";
      if (this.state === "unavailable") return "Browser control could not be checked. Refresh to retry.";
      if (!this.defaultSelection?.selected) return "Choose your Chrome browser once. Agent Zero will use it across chats unless a project has its own Browser settings.";
      if (this.defaultSelection.ready) return "Chrome is connected. This browser is the default for your chats.";
      return "Browser selected. Waiting for Chrome to connect and complete its security checks. Keep Chrome open; your pairing is saved.";
    },
    contextStatusText() {
      if (!this.current() || !identifier(this.contextId) || !this.defaultSelection?.selected) return "";
      if (this.contextState === "unavailable") return "The default is saved, but this chat's Browser settings could not be checked.";
      if (this.contextState === "loaded" && this.selection?.bridgeId !== this.defaultSelection.bridgeId)
        return "This chat has different Browser settings. Its project settings are kept; changing the default does not override them.";
      return "";
    },
    async refreshContext(generation) {
      if (!identifier(this.contextId)) return;
      try {
        const selected = parseSelection(await api(API, { action: "status", context_id: this.contextId }), this.contextId);
        if (this.current(generation)) { this.selection = selected; this.contextState = "loaded"; }
      } catch { if (this.current(generation)) { this.selection = null; this.contextState = "unavailable"; } }
    },
    async refresh() {
      if (!this.current() || this.loading || this.busy) return;
      const generation = this.generation; this.loading = true;
      try {
        const selected = parseSelection(await api(API, { action: "default_status" }));
        if (this.current(generation)) { this.defaultSelection = selected; this.state = "loaded"; await this.refreshContext(generation); }
      } catch { if (this.current(generation)) { this.defaultSelection = null; this.state = "unavailable"; } }
      finally { if (this.generation === generation) this.loading = false; }
    },
    async useBrowser(bridgeId) {
      if (this.canSelect(bridgeId)) await this.change("use_default", bridgeId);
    },
    async clear() {
      if (!this.current() || this.state !== "loaded" || !this.defaultSelection?.selected || this.busy || this.loading) return;
      const generation = this.generation; const bridgeId = this.defaultSelection.bridgeId;
      this.busy = true;
      try {
        const approved = await confirm({ title: "Stop using Chrome by default?", message: "Chats without their own Browser settings will use the internal browser. Project settings, your saved pairing and Chrome tabs are kept.", confirmText: "Use internal browser" });
        if (!approved || !this.current(generation) || this.defaultSelection?.bridgeId !== bridgeId) return;
        this.busy = false; await this.change("clear_default", bridgeId);
      } catch { if (this.current(generation)) notify("error", "Browser selection could not be changed."); }
      finally { if (this.generation === generation) this.busy = false; }
    },
    async change(action, bridgeId) {
      if (!this.current() || this.busy || this.loading) return;
      const generation = this.generation; const previousBridge = this.defaultSelection?.bridgeId ?? null;
      this.busy = true;
      try {
        const body = { action, ...(action === "use_default" ? { bridge_id: bridgeId } : {}), expected_bridge_id: previousBridge };
        const selected = parseSelection(await api(API, body));
        if ((action === "use_default" && selected.bridgeId !== bridgeId) || (action === "clear_default" && selected.selected)) throw new Error("Selection mismatch");
        if (!this.current(generation)) return;
        this.defaultSelection = selected; this.state = "loaded";
        await onSelected(this.settingsContext, () => this.current(generation));
        if (!this.current(generation)) return;
        await this.refreshContext(generation);
        if (this.current(generation)) notify("success", selected.selected ? "Chrome is now your default browser for Agent Zero. Existing project settings are kept." : "Agent Zero now defaults to its internal browser. Existing project settings are kept.");
      } catch {
        if (this.current(generation)) { this.defaultSelection = null; this.state = "unavailable";
          notify("error", "Browser selection could not be confirmed. Use Check connection before trying again."); }
      } finally { if (this.generation === generation) this.busy = false; }
    },
  };
}

export const store = createStore("browserBridgeSelection", createBridgeSelectionModel({
  api: callJsonApi, context: () => globalThis.Alpine?.store("chats")?.selected || "",
  confirm: showConfirmDialog,
  notify: (type, message) => { void notifications.frontendNotification({ type, message, title: "Browser connection", frontendOnly: true }).catch(() => {}); },
  onSelected: (settingsContext, current) => refreshBrowserSettingsScope(callJsonApi, settingsContext, current),
}));
