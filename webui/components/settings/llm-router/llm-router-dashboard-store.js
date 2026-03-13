import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, loadSettings, saveSettings } from "/js/api.js";

const model = {
  // State
  loading: false,
  error: null,
  activeView: "dashboard", // dashboard, models

  // Settings
  routerEnabled: false,
  autoConfigureEnabled: false,

  // Dashboard data
  models: {
    byProvider: {},
    totalCount: 0,
    localCount: 0,
    cloudCount: 0,
  },
  defaults: {
    chat: null,
    utility: null,
    browser: null,
    embedding: null,
    fallback: null,
  },
  usage: {
    lastHour: { calls: 0, costUsd: 0 },
    last24h: { calls: 0, costUsd: 0, byModel: {} },
  },

  // Available models for selection
  availableModels: [],

  // Lifecycle
  async onOpen() {
    await this.loadSettings();
    await this.refresh();
  },

  cleanup() {
    // No polling needed for router (unlike Ralph which has active tasks)
  },

  // View switching
  switchView(view) {
    this.activeView = view;
  },

  // Settings management
  async loadSettings() {
    try {
      const settings = await loadSettings();
      this.routerEnabled = settings.llm_router_enabled || false;
      this.autoConfigureEnabled = settings.llm_router_auto_configure || false;
    } catch (err) {
      console.error("Failed to load settings:", err);
    }
  },

  async toggleRouter() {
    this.routerEnabled = !this.routerEnabled;
    try {
      await saveSettings({ llm_router_enabled: this.routerEnabled });
    } catch (err) {
      this.error = "Failed to save router setting: " + err.message;
      this.routerEnabled = !this.routerEnabled; // Revert
    }
  },

  // API calls
  async refresh() {
    this.loading = true;
    this.error = null;
    try {
      await this.loadDashboard();
    } catch (err) {
      this.error = err.message || "Failed to load dashboard";
    } finally {
      this.loading = false;
    }
  },

  async loadDashboard() {
    const resp = await callJsonApi("/llm_router_dashboard", {});
    if (resp.success) {
      this.models = resp.models || this.models;
      this.defaults = resp.defaults || this.defaults;
      this.usage = resp.usage || this.usage;

      // Build flat list of available models for dropdowns
      this.buildAvailableModelsList();
    } else {
      throw new Error(resp.error || "Dashboard load failed");
    }
  },

  buildAvailableModelsList() {
    this.availableModels = [];
    const byProvider = this.models?.byProvider;
    if (!byProvider || typeof byProvider !== "object") return;
    for (const [provider, models] of Object.entries(byProvider)) {
      for (const model of models) {
        this.availableModels.push({
          provider: provider,
          name: model.name,
          displayName: model.display_name || model.name,
          isLocal: model.is_local,
          contextLength: model.context_length,
        });
      }
    }
  },

  async discoverModels(provider) {
    this.loading = true;
    this.error = null;
    try {
      const resp = await callJsonApi("/llm_router_discover", { provider });
      if (resp.success) {
        await this.loadDashboard(); // Reload to get new models
      } else {
        throw new Error(resp.error || "Discovery failed");
      }
    } catch (err) {
      this.error = err.message;
    } finally {
      this.loading = false;
    }
  },

  async autoConfigureModels() {
    this.loading = true;
    this.error = null;
    try {
      const resp = await callJsonApi("/llm_router_auto_configure", {});
      if (resp.success) {
        await this.loadDashboard(); // Reload to get configured defaults
      } else {
        throw new Error(resp.error || "Auto-configure failed");
      }
    } catch (err) {
      this.error = err.message;
    } finally {
      this.loading = false;
    }
  },

  async setDefault(role, provider, modelName) {
    try {
      const resp = await callJsonApi("/llm_router_set_default", {
        role,
        provider,
        model_name: modelName,
      });
      if (resp.success) {
        this.defaults[role] = { provider, model_name: modelName };
      } else {
        throw new Error(resp.error || "Failed to set default");
      }
    } catch (err) {
      this.error = err.message;
    }
  },

  // Helper methods
  formatCost(cost) {
    if (cost === 0) return "Free";
    if (cost < 0.01) return "<$0.01";
    return "$" + cost.toFixed(2);
  },

  formatContextLength(length) {
    if (length >= 1000000) {
      return (length / 1000000).toFixed(1) + "M";
    }
    if (length >= 1000) {
      return (length / 1000).toFixed(0) + "k";
    }
    return length.toString();
  },

  getProviderIcon(provider) {
    const icons = {
      ollama: "🦙",
      openai: "🤖",
      anthropic: "🧠",
      google: "🔮",
      default: "💬",
    };
    return icons[provider.toLowerCase()] || icons.default;
  },

  getDefaultDisplay(role) {
    const def = this.defaults[role];
    if (!def || !def.provider) return "Not set";
    return `${def.provider}/${def.model_name}`;
  },

  // Model selection for dropdowns
  onModelSelected(role, event) {
    const value = event.target.value;
    if (!value) return;

    const [provider, ...nameParts] = value.split("/");
    const modelName = nameParts.join("/");
    this.setDefault(role, provider, modelName);
  },
};

export const store = createStore("llmRouterStore", model);
