import { createStore } from "/js/AlpineStore.js";
import { store as settingsStore } from "/components/plugins/plugin-settings-store.js";

const fetchApi = globalThis.fetchApi;

const model = {
    pluginName: null,
    
    // Context selectors
    projects: [],
    agentProfiles: [],
    projectName: "",
    agentProfileKey: "",

    // State
    isLoading: false,
    isSaving: false,
    error: null,
    
    // Status: 'enabled' | 'disabled'
    status: 'enabled',
    alwaysEnabled: false,
    perProjectConfig: true,
    perAgentConfig: true,
    hasExplicitRuleForScope: false,
    hasConfigScreen: false,

    // Where the effective toggle was actually resolved (mirrors plugin-settings-store loadedXxx fields)
    loadedPath: "",
    loadedProjectName: "",
    loadedAgentProfile: "",

    configs: [],

    async open(plugin, { projectName = "", agentProfileKey = "" } = {}) {
        this.isLoading = true;
        this.error = null;
        this.projects = [];
        this.agentProfiles = [];
        this.projectName = projectName || "";
        this.agentProfileKey = agentProfileKey || "";
        this.configs = [];
        this.status = 'enabled';
        this.hasExplicitRuleForScope = false;
        this.loadedPath = "";
        this.loadedProjectName = "";
        this.loadedAgentProfile = "";

        const pluginName = typeof plugin === 'string' ? plugin : plugin?.name;
        this.pluginName = pluginName;
        this.alwaysEnabled = typeof plugin === 'object' ? !!plugin.always_enabled : false;
        this.perProjectConfig = typeof plugin === 'object' ? !!plugin.per_project_config : true;
        this.perAgentConfig = typeof plugin === 'object' ? !!plugin.per_agent_config : true;
        this.hasConfigScreen = typeof plugin === 'object' ? !!plugin.has_config_screen : false;

        try {
            await Promise.all([this.loadProjects(), this.loadAgentProfiles()]);
            await this.loadConfigs();
        } finally {
            this.isLoading = false;
        }
    },

    cleanup() {
        this.pluginName = null;
        this.projectName = "";
        this.agentProfileKey = "";
        this.error = null;
        this.configs = [];
        this.perProjectConfig = true;
        this.perAgentConfig = true;
        this.alwaysEnabled = false;
        this.hasConfigScreen = false;
        this.hasExplicitRuleForScope = false;
        this.loadedPath = "";
        this.loadedProjectName = "";
        this.loadedAgentProfile = "";
        this.isLoading = false;
        this.isSaving = false;
    },

    async loadProjects() {
        try {
            const response = await fetchApi("/projects", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "list_options" }),
            });
            const data = await response.json().catch(() => ({}));
            this.projects = data.ok ? (data.data || []) : [];
        } catch {
            this.projects = [];
        }
    },

    async loadAgentProfiles() {
        try {
            const response = await fetchApi("/agents", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "list" }),
            });
            const data = await response.json().catch(() => ({}));
            this.agentProfiles = data.ok ? (data.data || []) : [];
        } catch {
            this.agentProfiles = [];
        }
    },

    async loadConfigs() {
        if (!this.pluginName) return;
        this.isLoading = true;
        try {
            const response = await fetchApi("/plugins", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "list_configs",
                    plugin_name: this.pluginName,
                    asset_type: "toggle"
                }),
            });
            const result = await response.json().catch(() => ({}));
            this.configs = result.ok ? (result.data || []) : [];
            await this.loadToggleStatus();
        } catch (e) {
            this.error = e?.message || "Failed to load configurations";
        } finally {
            this.isLoading = false;
        }
    },

    async loadToggleStatus() {
        if (!this.pluginName) return;

        if (this.alwaysEnabled) {
            this.status = 'enabled';
            this.hasExplicitRuleForScope = true;
            this.loadedPath = "";
            this.loadedProjectName = this.projectName || "";
            this.loadedAgentProfile = this.agentProfileKey || "";
            return;
        }

        try {
            const response = await fetchApi("/plugins", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "get_toggle_status",
                    plugin_name: this.pluginName,
                    project_name: this.projectName || "",
                    agent_profile: this.agentProfileKey || "",
                }),
            });
            const result = await response.json().catch(() => ({}));
            if (result.ok) {
                this.status = result.status || 'enabled';
                this.loadedPath = result.loaded_path || "";
                this.loadedProjectName = result.loaded_project_name || "";
                this.loadedAgentProfile = result.loaded_agent_profile || "";
                const p = this.projectName || "";
                const a = this.agentProfileKey || "";
                this.hasExplicitRuleForScope = !!(this.loadedPath) &&
                    this.loadedProjectName === p &&
                    this.loadedAgentProfile === a;
            }
        } catch (e) {
            this.error = e?.message || "Failed to load toggle status";
        }
    },

    async openConfigWithScope() {
        if (!this.pluginName) return;
        this.error = null;
        try {
            await settingsStore.openConfig(
                this.pluginName,
                this.projectName || "",
                this.agentProfileKey || ""
            );
        } catch (e) {
            this.error = e?.message || "Failed to open plugin config";
        }
    },

    async openConfigListModal() {
        await window.openModal?.("/components/plugins/toggle/plugin-toggles.html");
    },

    async switchToConfig(projectName, agentProfile) {
        this.projectName = projectName || "";
        this.agentProfileKey = agentProfile || "";
        await this.onScopeChanged();
        await window.closeModal?.();
    },

    async deleteConfig(path) {
        if (!this.pluginName || !path) return;
        this.isLoading = true;
        try {
            const response = await fetchApi("/plugins", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "delete_config",
                    plugin_name: this.pluginName,
                    path: path
                }),
            });
            const result = await response.json();
            if (!result.ok) throw new Error(result.error);
            await this.loadConfigs();
        } catch (e) {
            this.error = e.message || "Delete failed";
        } finally {
            this.isLoading = false;
        }
    },

    async setEnabled(enabled) {
        if (!this.pluginName || this.alwaysEnabled) return;
        this.isSaving = true;
        try {
            const response = await fetchApi("/plugins", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "toggle_plugin",
                    plugin_name: this.pluginName,
                    project_name: this.projectName || "",
                    agent_profile: this.agentProfileKey || "",
                    enabled: enabled
                }),
            });
            const result = await response.json();
            if (!result.ok) throw new Error(result.error);
            await new Promise(r => setTimeout(r, 100));
            await this.loadConfigs();
        } catch (e) {
            this.error = e.message || "Failed to save";
        } finally {
            this.isSaving = false;
        }
    },

    async onScopeChanged() {
        await this.loadToggleStatus();

        // Sync scope with settings store so its loadSettings picks up the right context
        settingsStore.projectName = this.projectName || "";
        settingsStore.agentProfileKey = this.agentProfileKey || "";
        await settingsStore.loadSettings();
    },

    async addRule() {
        await this.setEnabled(this.status === 'enabled');
    },

    projectLabel(key) {
        if (!key) return "Global";
        const found = (this.projects || []).find(p => p.key === key);
        return found?.label || key;
    },

    agentProfileLabel(key) {
        if (!key) return "All profiles";
        const found = (this.agentProfiles || []).find(p => p.key === key);
        return found?.label || key;
    },

    get statusLabel() {
        return this.status === 'enabled' ? 'ON' : 'OFF';
    },

    get noScopeRuleMessage() {
        if (this.alwaysEnabled || this.isLoading) return "";
        if (this.hasExplicitRuleForScope) return "";

        if (!this.loadedPath) {
            return this.configs.length === 0
                ? "No activation rule exists yet. This plugin is currently ON by default."
                : "No activation rule exists for this scope yet. This scope is currently ON by default.";
        }

        // Inherited from a parent scope - mirrors plugin-settings-store scopeMismatchMessage
        const pLabel = this.projectLabel(this.loadedProjectName || "");
        const aLabel = this.agentProfileLabel(this.loadedAgentProfile || "");
        const state = this.status === 'enabled' ? 'ON' : 'OFF';
        return `No rule for this scope. Inheriting from ${pLabel}, ${aLabel}: ${state}.`;
    }
};

export const store = createStore("pluginToggle", model);
