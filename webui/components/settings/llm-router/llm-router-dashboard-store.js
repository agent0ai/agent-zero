import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, loadSettings, saveSettings } from "/js/api.js";

const model = {
  // State
  loading: false,
  error: null,
  activeView: "dashboard", // dashboard, models, rules

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

  // Rules state
  rules: [],
  showAddRule: false,
  newRule: {
    name: "",
    priority: 0,
    condition: "",
    preferredModels: "",
    excludedModels: "",
    minContextLength: 0,
    maxCostPer1k: 0,
    maxLatencyMs: 0,
    requiredCapabilities: "",
    enabled: true,
  },

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
    if (view === "rules" && this.rules.length === 0) {
      this.loadRules();
    }
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
          displayName: model.displayName || model.name,
          isLocal: model.isLocal,
          contextLength: model.contextLength,
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
        modelName: modelName,
      });
      if (resp.success) {
        this.defaults[role] = { provider, modelName: modelName };
      } else {
        throw new Error(resp.error || "Failed to set default");
      }
    } catch (err) {
      this.error = err.message;
    }
  },

  // Rules management
  async loadRules() {
    try {
      const resp = await callJsonApi("/llm_router_rules", {
        action: "list",
        include_disabled: true,
      });
      if (resp.success) {
        this.rules = resp.rules || [];
      }
    } catch (err) {
      console.error("Failed to load rules:", err);
    }
  },

  resetNewRule() {
    this.newRule = {
      name: "",
      priority: 0,
      condition: "",
      preferredModels: "",
      excludedModels: "",
      minContextLength: 0,
      maxCostPer1k: 0,
      maxLatencyMs: 0,
      requiredCapabilities: "",
      enabled: true,
    };
    this.showAddRule = false;
  },

  async addRule() {
    if (!this.newRule.name.trim()) {
      this.error = "Rule name is required";
      return;
    }
    try {
      const rule = {
        name: this.newRule.name.trim(),
        priority: parseInt(this.newRule.priority) || 0,
        condition: this.newRule.condition,
        preferredModels: this.newRule.preferredModels
          ? this.newRule.preferredModels.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
        excludedModels: this.newRule.excludedModels
          ? this.newRule.excludedModels.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
        minContextLength: parseInt(this.newRule.minContextLength) || 0,
        maxCostPer1k: parseFloat(this.newRule.maxCostPer1k) || 0,
        maxLatencyMs: parseInt(this.newRule.maxLatencyMs) || 0,
        requiredCapabilities: this.newRule.requiredCapabilities
          ? this.newRule.requiredCapabilities.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
        enabled: this.newRule.enabled,
      };
      const resp = await callJsonApi("/llm_router_rules", {
        action: "add",
        rule,
      });
      if (resp.success) {
        this.resetNewRule();
        await this.loadRules();
      } else {
        throw new Error(resp.error || "Failed to add rule");
      }
    } catch (err) {
      this.error = err.message;
    }
  },

  async toggleRule(name, enabled) {
    try {
      const resp = await callJsonApi("/llm_router_rules", {
        action: "toggle",
        name,
        enabled,
      });
      if (resp.success) {
        await this.loadRules();
      } else {
        throw new Error(resp.error || "Failed to toggle rule");
      }
    } catch (err) {
      this.error = err.message;
    }
  },

  async deleteRule(name) {
    try {
      const resp = await callJsonApi("/llm_router_rules", {
        action: "delete",
        name,
      });
      if (resp.success) {
        await this.loadRules();
      } else {
        throw new Error(resp.error || "Failed to delete rule");
      }
    } catch (err) {
      this.error = err.message;
    }
  },

  // Edit rule support
  editingRule: null,  // name of rule being edited, or null

  startEditRule(rule) {
    this.editingRule = rule.name;
    this.newRule = {
      name: rule.name,
      priority: rule.priority || 0,
      condition: rule.condition || "",
      preferredModels: Array.isArray(rule.preferredModels) ? rule.preferredModels.join(", ") : "",
      excludedModels: Array.isArray(rule.excludedModels) ? rule.excludedModels.join(", ") : "",
      minContextLength: rule.minContextLength || 0,
      maxCostPer1k: rule.maxCostPer1k || 0,
      maxLatencyMs: rule.maxLatencyMs || 0,
      requiredCapabilities: Array.isArray(rule.requiredCapabilities) ? rule.requiredCapabilities.join(", ") : "",
      enabled: rule.enabled !== false,
    };
    this.showAddRule = true;
  },

  cancelEditRule() {
    this.editingRule = null;
    this.resetNewRule();
  },

  async updateRule() {
    if (!this.editingRule) return;
    try {
      const rule = {
        name: this.newRule.name.trim(),
        priority: parseInt(this.newRule.priority) || 0,
        condition: this.newRule.condition,
        preferredModels: this.newRule.preferredModels
          ? this.newRule.preferredModels.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
        excludedModels: this.newRule.excludedModels
          ? this.newRule.excludedModels.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
        minContextLength: parseInt(this.newRule.minContextLength) || 0,
        maxCostPer1k: parseFloat(this.newRule.maxCostPer1k) || 0,
        maxLatencyMs: parseInt(this.newRule.maxLatencyMs) || 0,
        requiredCapabilities: this.newRule.requiredCapabilities
          ? this.newRule.requiredCapabilities.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
        enabled: this.newRule.enabled,
      };
      const resp = await callJsonApi("/llm_router_rules", {
        action: "update",
        name: this.editingRule,
        rule,
      });
      if (resp.success) {
        this.editingRule = null;
        this.resetNewRule();
        await this.loadRules();
      } else {
        throw new Error(resp.error || "Failed to update rule");
      }
    } catch (err) {
      this.error = err.message;
    }
  },

  // Helper methods
  formatCost(cost) {
    if (cost == null || cost === undefined) return "$0.00";
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
    return `${def.provider}/${def.modelName}`;
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
