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

// API key placeholder used in backend
const API_KEY_PLACEHOLDER = "************";

// Settings Store
const model = {
  // State
  isLoading: false,
  error: null,
  settings: null,
  additional: null,
  
  // Dynamic model options fetched from provider APIs
  chatModels: [{ value: "__custom__", label: "Custom (enter manually)" }],
  utilModels: [{ value: "__custom__", label: "Custom (enter manually)" }],
  embedModels: [{ value: "__custom__", label: "Custom (enter manually)" }],
  browserModels: [{ value: "__custom__", label: "Custom (enter manually)" }],
  
  // Loading state for model refresh
  isRefreshingModels: {
    chat: false,
    util: false,
    embed: false,
    browser: false,
  },
  
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
    
    // Fetch dynamic model options in background
    this.refreshAllModels();
  },

  cleanup() {
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
      if (seen.has(key)) return;
      seen.add(key);
      options.push({ value: prov.value, label: prov.label || prov.value });
    };
    (this.additional?.chat_providers || []).forEach(addProvider);
    (this.additional?.embedding_providers || []).forEach(addProvider);
    options.sort((a, b) => a.label.localeCompare(b.label));
    return options;
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

  // Collect API keys from settings for model refresh calls
  _collectApiKeys() {
    const apiKeys = {};
    if (this.settings?.api_keys) {
      for (const [provider, key] of Object.entries(this.settings.api_keys)) {
        if (key && key.length > 0) {
          apiKeys[provider] = key;
        }
      }
    }
    return apiKeys;
  },

  // Refresh model options for a specific model type and provider
  async refreshModels(modelPrefix, forceRefresh = false) {
    if (!this.settings) return;

    const modelType = modelPrefix === "embed" ? "embedding" : "chat";
    const providerKey = `${modelPrefix}_model_provider`;
    const nameKey = `${modelPrefix}_model_name`;
    const apiBaseKey = `${modelPrefix}_model_api_base`;
    
    const provider = this.settings[providerKey];
    const currentValue = this.settings[nameKey];
    const apiBase = this.settings[apiBaseKey] || "";
    
    if (!provider) return;

    const modelsKey = `${modelPrefix}Models`;
    this.isRefreshingModels[modelPrefix] = true;

    try {
      const response = await API.callJsonApi("settings_refresh_models", {
        model_type: modelType,
        provider: provider,
        api_keys: this._collectApiKeys(),
        api_base: apiBase,
        force_refresh: forceRefresh,
      });

      if (response && response.models && response.models.length > 0) {
        let newOptions = [...response.models];
        
        // Ensure current value is in options if not already there
        if (currentValue && currentValue !== "__custom__") {
          const hasCurrentValue = newOptions.some(m => m.value === currentValue);
          if (!hasCurrentValue) {
            newOptions.unshift({
              value: currentValue,
              label: `${currentValue} (current)`,
            });
          }
        }
        
        this[modelsKey] = newOptions;
      }
    } catch (e) {
      console.error(`Error refreshing ${modelPrefix} models:`, e);
    } finally {
      this.isRefreshingModels[modelPrefix] = false;
    }
  },

  // Refresh all model options in parallel
  async refreshAllModels() {
    await Promise.all([
      this.refreshModels("chat"),
      this.refreshModels("util"),
      this.refreshModels("embed"),
      this.refreshModels("browser"),
    ]);
  },

  // Handler for when a provider dropdown changes
  async handleProviderChange(modelPrefix) {
    await this.refreshModels(modelPrefix, true);
  },

  // Apply custom model value when user enters it manually
  applyCustomModel(modelPrefix, customValue) {
    if (!customValue || !customValue.trim()) return;
    
    const nameKey = `${modelPrefix}_model_name`;
    const modelsKey = `${modelPrefix}Models`;
    const trimmedValue = customValue.trim();
    
    // Add custom value as an option
    const customOption = {
      value: trimmedValue,
      label: trimmedValue,
    };
    
    // Insert before __custom__ option
    const customIndex = this[modelsKey].findIndex(o => o.value === "__custom__");
    if (customIndex > -1) {
      this[modelsKey].splice(customIndex, 0, customOption);
    } else {
      this[modelsKey].push(customOption);
    }
    
    // Select the custom value
    this.settings[nameKey] = trimmedValue;
  },
};

const store = createStore("settingsStore", model);

export { store };

