import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

// Constants
const VIEW_MODE_STORAGE_KEY = "settingsActiveTab";
const DEFAULT_TAB = "agent";

// Field button actions (field id -> modal path)
const FIELD_BUTTON_MODAL_BY_ID = Object.freeze({
  mcp_servers_config: "settings/mcp/client/mcp-servers.html",
  backup_create: "settings/backup/backup.html",
  backup_restore: "settings/backup/restore.html",
  show_a2a_connection: "settings/a2a/a2a-connection.html",
  external_api_examples: "settings/external/api-examples.html",
});

// Helper for toasts
function toast(text, type = "info", timeout = 5000) {
  notificationStore.addFrontendToastOnly(type, text, "", timeout / 1000);
}

// Settings Store
const model = {
  // State
  isLoading: false,
  error: null,
  settings: null,
  additional: null,
  workdirFileStructureTestOutput: "",
  codexActionLoading: false,
  codexLastMessage: "",
  codexPollHandle: null,
  
  // Tab state
  _activeTab: DEFAULT_TAB,
  get activeTab() {
    return this._activeTab;
  },
  set activeTab(value) {
    const previous = this._activeTab;
    this._activeTab = value;
    this.applyActiveTab(previous, value);
  },

  // Lifecycle
  init() {
    // Restore persisted tab
    try {
      const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
      if (saved) this._activeTab = saved;
    } catch {}
  },

  async onOpen() {
    this.error = null;
    this.isLoading = true;
    
    try {
      const response = await API.callJsonApi("settings_get", null);
      if (response && response.settings) {
        this.settings = response.settings;
        this.additional = response.additional || null;
      } else {
        throw new Error("Invalid settings response");
      }
    } catch (e) {
      console.error("Failed to load settings:", e);
      this.error = e.message || "Failed to load settings";
      toast("Failed to load settings", "error");
    } finally {
      this.isLoading = false;
    }

    // Trigger tab activation for current tab
    this.applyActiveTab(null, this._activeTab);

    // Keep Codex subscription state fresh when settings open
    await this.refreshCodexSubscriptionStatus();
  },

  cleanup() {
    this.stopCodexLoginPolling();
    this.settings = null;
    this.additional = null;
    this.error = null;
    this.isLoading = false;
  },

  // Tab management
  applyActiveTab(previous, current) {
    // Persist
    try {
      localStorage.setItem(VIEW_MODE_STORAGE_KEY, current);
    } catch {}
  },

  switchTab(tabName) {
    this.activeTab = tabName;
  },



  get apiKeyProviders() {
    const seen = new Set();
    const options = [];
    const addProvider = (prov) => {
      if (!prov?.value) return;
      const key = prov.value.toLowerCase();
      if (key === "codex") return;
      if (seen.has(key)) return;
      seen.add(key);
      options.push({ value: prov.value, label: prov.label || prov.value });
    };
    (this.additional?.chat_providers || []).forEach(addProvider);
    (this.additional?.embedding_providers || []).forEach(addProvider);
    options.sort((a, b) => a.label.localeCompare(b.label));
    return options;
  },

  isCodexProvider(provider) {
    return String(provider || "").toLowerCase() === "codex";
  },

  getCodexStatus() {
    return this.additional?.runtime_settings?.codex_status || null;
  },

  getCodexLoginState() {
    return this.additional?.runtime_settings?.codex_login || null;
  },

  getCodexModelPayload() {
    return this.additional?.runtime_settings?.codex_models || null;
  },

  getCodexModelOptions(selectedModel = "", roleKey = "codex-model") {
    const payload = this.getCodexModelPayload();
    let models = Array.isArray(payload?.models)
      ? payload.models.map((model) => ({ ...model }))
      : [];
    if (!models.length) {
      models = [{ value: "gpt-5-codex", label: "GPT-5-Codex", available: null }];
    }
    const selected = String(selectedModel || "").trim();
    if (selected && !models.find((m) => m.value === selected)) {
      models.unshift({
        value: selected,
        label: selected,
        available: null,
      });
    }
    return models.map((model, index) => ({
      ...model,
      key: `${roleKey}-${index}-${model.value}`,
    }));
  },

  _setCodexRuntime(status = null, login = null, models = null) {
    if (!this.additional) this.additional = {};
    if (!this.additional.runtime_settings) this.additional.runtime_settings = {};
    if (status) this.additional.runtime_settings.codex_status = status;
    if (login) this.additional.runtime_settings.codex_login = login;
    if (models) this.additional.runtime_settings.codex_models = models;
  },

  startCodexLoginPolling() {
    this.stopCodexLoginPolling();
    this.codexPollHandle = setInterval(async () => {
      const response = await this.refreshCodexSubscriptionStatus();
      const running = !!response?.login?.running;
      const connected = !!response?.status?.logged_in;
      if (!running) {
        this.stopCodexLoginPolling();
      }
      if (connected) {
        await this.refreshCodexModels(true);
      }
    }, 2000);
  },

  stopCodexLoginPolling() {
    if (this.codexPollHandle) {
      clearInterval(this.codexPollHandle);
      this.codexPollHandle = null;
    }
  },

  async refreshCodexSubscriptionStatus() {
    this.codexActionLoading = true;
    try {
      const response = await API.callJsonApi("codex_subscription_status", {});
      this._setCodexRuntime(response?.status || null, response?.login || null, response?.models || null);
      if (response?.login?.message) this.codexLastMessage = response.login.message;
      return response;
    } catch (e) {
      toast("Failed to check ChatGPT subscription status: " + e.message, "error");
      return null;
    } finally {
      this.codexActionLoading = false;
    }
  },

  async connectChatGptSubscription() {
    this.codexActionLoading = true;
    try {
      const response = await API.callJsonApi("codex_subscription_start", {});
      this._setCodexRuntime(response?.status || null, response?.login || null, response?.models || null);
      if (response?.login?.message) this.codexLastMessage = response.login.message;

      const authUrl = response?.login?.auth_url || "";
      if (authUrl) {
        window.open(authUrl, "_blank", "noopener,noreferrer");
        toast("Opened ChatGPT login page. Finish authorization in browser.", "info");
        this.startCodexLoginPolling();
      } else {
        toast("Started login flow. If browser did not open, click Check Status.", "info");
      }
      return response;
    } catch (e) {
      toast("Failed to start ChatGPT subscription login: " + e.message, "error");
      return null;
    } finally {
      this.codexActionLoading = false;
    }
  },

  async disconnectChatGptSubscription() {
    this.stopCodexLoginPolling();
    this.codexActionLoading = true;
    try {
      const response = await API.callJsonApi("codex_subscription_logout", {});
      this._setCodexRuntime(response?.status || null, response?.login || null, response?.models || null);
      this.codexLastMessage = response?.message || "Disconnected.";
      toast(response?.ok ? "ChatGPT subscription disconnected" : "Disconnect finished with warnings", response?.ok ? "success" : "warning");
      return response;
    } catch (e) {
      toast("Failed to disconnect ChatGPT subscription: " + e.message, "error");
      return null;
    } finally {
      this.codexActionLoading = false;
    }
  },

  async refreshCodexModels(forceRefresh = true) {
    this.codexActionLoading = true;
    try {
      const response = await API.callJsonApi("codex_models_get", { force_refresh: forceRefresh });
      this._setCodexRuntime(response?.status || null, null, response?.models || null);
      const diagnostic = response?.models?.diagnostic || "";
      if (diagnostic) this.codexLastMessage = diagnostic;
      toast("Codex models refreshed", "success");
      return response;
    } catch (e) {
      toast("Failed to refresh Codex models: " + e.message, "error");
      return null;
    } finally {
      this.codexActionLoading = false;
    }
  },

  // Save settings
  async saveSettings() {
    if (!this.settings) {
      toast("No settings to save", "warning");
      return false;
    }

    this.isLoading = true;
    try {
      const response = await API.callJsonApi("settings_set", { settings: this.settings });
      if (response && response.settings) {
        this.settings = response.settings;
        this.additional = response.additional || this.additional;
        toast("Settings saved successfully", "success");
        document.dispatchEvent(
          new CustomEvent("settings-updated", { detail: response.settings })
        );
        return true;
      } else {
        throw new Error("Failed to save settings");
      }
    } catch (e) {
      console.error("Failed to save settings:", e);
      toast("Failed to save settings: " + e.message, "error");
      return false;
    } finally {
      this.isLoading = false;
    }
  },

  // Close the modal
  closeSettings() {
    window.closeModal("settings/settings.html");
  },

  // Save and close
  async saveAndClose() {
    const success = await this.saveSettings();
    if (success) {
      this.closeSettings();
    }
  },

  async testWorkdirFileStructure() {
    if (!this.settings) return;
    try {
      const response = await API.callJsonApi("settings_workdir_file_structure", {
        workdir_path: this.settings.workdir_path,
        workdir_max_depth: this.settings.workdir_max_depth,
        workdir_max_files: this.settings.workdir_max_files,
        workdir_max_folders: this.settings.workdir_max_folders,
        workdir_max_lines: this.settings.workdir_max_lines,
        workdir_gitignore: this.settings.workdir_gitignore,
      });
      this.workdirFileStructureTestOutput = response?.data || "";
      window.openModal("settings/agent/workdir-file-structure-test.html");
    } catch (e) {
      console.error("Error testing workdir file structure:", e);
      toast("Error testing workdir file structure", "error");
    }
  },

  // Field helpers for external components
  // Handle button field clicks (opens sub-modals)
  async handleFieldButton(field) {
    const modalPath = FIELD_BUTTON_MODAL_BY_ID[field?.id];
    if (modalPath) window.openModal(modalPath);
  },

  // Open settings modal from external callers
  async open(initialTab = null) {
    if (initialTab) {
      this._activeTab = initialTab;
    }
    await window.openModal("settings/settings.html");
  },
};

const store = createStore("settings", model);

export { store };
