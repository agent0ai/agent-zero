import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";
import { showConfirmDialog } from "/js/confirmDialog.js";
import { store as pluginToggleStore } from "/components/plugins/toggle/plugin-toggle-store.js";

const fetchApi = globalThis.fetchApi;
const justToast = globalThis.justToast;

const model = {
    // which plugin this modal is showing
    pluginName: null,
    pluginMeta: null,

    // context selectors (mirrors skills list pattern)
    projects: [],
    agentProfiles: [],
    projectName: "",
    agentProfileKey: "",

    // plugin settings data (plugins bind their fields here)
    settings: {},

    settingsSnapshotJson: "",
    previousProjectName: "",
    previousAgentProfileKey: "",

    _toComparableJson(value) {
        try {
            return JSON.stringify(value ?? {});
        } catch {
            return "";
        }
    },

    get hasUnsavedChanges() {
        return this._toComparableJson(this.settings) !== (this.settingsSnapshotJson || "");
    },

    confirmDiscardUnsavedChanges() {
        if (!this.hasUnsavedChanges) return true;
        return window.confirm("You have unsaved changes that will be lost. Continue?");
    },

    async _loadPluginMeta(pluginName) {
        const response = await api.callJsonApi("plugins_list", {
            filter: { custom: true, builtin: true, search: "" },
        });
        const plugins = Array.isArray(response?.plugins) ? response.plugins : [];
        return plugins.find((plugin) => plugin?.name === pluginName) || null;
    },

    _hasProject(projectName) {
        if (!projectName) return false;
        return (this.projects || []).some((project) => project?.key === projectName);
    },

    _hasAgentProfile(agentProfileKey) {
        if (!agentProfileKey) return false;
        return (this.agentProfiles || []).some((profile) => profile?.key === agentProfileKey);
    },

    _resolveScope(pluginMeta, projectName = "", agentProfileKey = "") {
        const resolvedProjectName =
            pluginMeta?.per_project_config && this._hasProject(projectName)
                ? projectName
                : "";
        const resolvedAgentProfileKey =
            pluginMeta?.per_agent_config && this._hasAgentProfile(agentProfileKey)
                ? agentProfileKey
                : "";

        return {
            projectName: resolvedProjectName,
            agentProfileKey: resolvedAgentProfileKey,
        };
    },

    _applyPluginState(pluginMeta, { projectName = "", agentProfileKey = "" } = {}) {
        this.pluginName = pluginMeta?.name || null;
        this.pluginMeta = pluginMeta || null;
        this.settings = {};
        this.settingsSnapshotJson = "";
        this.error = null;
        this.projectName = projectName;
        this.agentProfileKey = agentProfileKey;
        this.previousProjectName = projectName;
        this.previousAgentProfileKey = agentProfileKey;
        this.loadedPath = "";
        this.loadedProjectName = "";
        this.loadedAgentProfile = "";
        this.perProjectConfig = !!pluginMeta?.per_project_config;
        this.perAgentConfig = !!pluginMeta?.per_agent_config;
    },

    async _syncToggleScope(projectName = "", agentProfileKey = "") {
        if (!pluginToggleStore?.loadToggleStatus) return;
        pluginToggleStore.projectName = projectName;
        pluginToggleStore.agentProfileKey = agentProfileKey;
        await pluginToggleStore.loadToggleStatus();
    },

    async onScopeChanged() {
        const nextProject = this.projectName || "";
        const nextProfile = this.agentProfileKey || "";
        const prevProject = this.previousProjectName || "";
        const prevProfile = this.previousAgentProfileKey || "";

        if (nextProject === prevProject && nextProfile === prevProfile) return;

        if (!this.confirmDiscardUnsavedChanges()) {
            this.projectName = prevProject;
            this.agentProfileKey = prevProfile;
            return;
        }

        await this.loadSettings();
        await this._syncToggleScope(nextProject, nextProfile);
    },

    // where the settings were actually loaded from
    loadedPath: "",
    loadedProjectName: "",
    loadedAgentProfile: "",

    projectLabel(key) {
        if (!key) return "Global";
        const found = (this.projects || []).find((p) => p.key === key);
        return found?.label || key;
    },

    agentProfileLabel(key) {
        if (!key) return "All profiles";
        const found = (this.agentProfiles || []).find((p) => p.key === key);
        return found?.label || key;
    },

    get scopeMismatchMessage() {
        const selectedProject = this.projectName || "";
        const selectedProfile = this.agentProfileKey || "";
        const loadedProject = this.loadedProjectName || "";
        const loadedProfile = this.loadedAgentProfile || "";

        if (!this.loadedPath) return "";
        if (selectedProject === loadedProject && selectedProfile === loadedProfile) return "";

        return `Settings do not yet exist for this combination, settings from ${this.projectLabel(loadedProject)}, ${this.agentProfileLabel(loadedProfile)} (${this.loadedPath}) will apply.`;
    },

    configs: [],
    isListingConfigs: false,
    configsError: null,

    async openConfigListModal() {
        await window.openModal?.("/components/plugins/plugin-configs.html");
    },

    async loadConfigList() {
        if (!this.pluginName) return;
        this.isListingConfigs = true;
        this.configsError = null;
        try {
            const response = await fetchApi("/plugins", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "list_configs",
                    plugin_name: this.pluginName,
                }),
            });
            const result = await response.json().catch(() => ({}));
            this.configs = result.ok ? (result.data || []) : [];
            if (!result.ok) this.configsError = result.error || "Failed to load configurations";
        } catch (e) {
            this.configsError = e?.message || "Failed to load configurations";
            this.configs = [];
        } finally {
            this.isListingConfigs = false;
        }
    },

    async switchToConfig(projectName, agentProfile) {
        if (!this.confirmDiscardUnsavedChanges()) return;
        this.projectName = projectName || "";
        this.agentProfileKey = agentProfile || "";
        await this.loadSettings();
        await this._syncToggleScope(this.projectName, this.agentProfileKey);
        await window.closeModal?.();
    },

    async deleteConfig(projectName, agentProfile) {
        if (!this.pluginName) return;
        try {
            const cfg = (this.configs || []).find(
                (c) => (c?.project_name || "") === (projectName || "") && (c?.agent_profile || "") === (agentProfile || "")
            );
            const path = cfg?.path || "";
            if (!path) {
                this.configsError = "Configuration path not found";
                return;
            }

            const response = await fetchApi("/plugins", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "delete_config",
                    plugin_name: this.pluginName,
                    path,
                }),
            });
            const result = await response.json().catch(() => ({}));
            if (!result.ok) {
                this.configsError = result.error || "Delete failed";
                return;
            }

            this.configsError = null;
            await this.loadConfigList();
        } catch (e) {
            this.configsError = e?.message || "Delete failed";
        }
    },

    perProjectConfig: true,
    perAgentConfig: true,

    isLoading: false,
    isSaving: false,
    error: null,

    async openConfig(pluginName, projectName = "", agentProfile = "") {
        if (!pluginName) {
            throw new Error("Missing plugin name.");
        }

        this.cleanup();
        const pluginMeta = await this._loadPluginMeta(pluginName);
        if (!pluginMeta) {
            throw new Error(`Plugin "${pluginName}" not found.`);
        }
        if (!pluginMeta.has_config_screen) {
            throw new Error(`Plugin "${pluginName}" has no config screen.`);
        }

        await Promise.all([this.loadProjects(), this.loadAgentProfiles()]);
        const resolvedScope = this._resolveScope(pluginMeta, projectName || "", agentProfile || "");
        this._applyPluginState(pluginMeta, resolvedScope);
        await this.loadSettings();

        if (!pluginToggleStore?.open) {
            throw new Error("Plugin toggle store is unavailable.");
        }
        await pluginToggleStore.open(pluginMeta, resolvedScope);
        await window.openModal?.("/components/plugins/plugin-settings.html");
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

    async loadSettings() {
        if (!this.pluginName) return;
        this.isLoading = true;
        this.error = null;
        try {
            const response = await fetchApi("/plugins", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "get_config",
                    plugin_name: this.pluginName,
                    project_name: this.projectName || "",
                    agent_profile: this.agentProfileKey || "",
                }),
            });
            const result = await response.json().catch(() => ({}));
            this.settings = result.ok ? (result.data || {}) : {};
            this.loadedPath = result.loaded_path || "";
            this.loadedProjectName = result.loaded_project_name || "";
            this.loadedAgentProfile = result.loaded_agent_profile || "";
            if (!result.ok) this.error = result.error || "Failed to load settings";
        } catch (e) {
            this.error = e?.message || "Failed to load settings";
            this.settings = {};
        } finally {
            this.settingsSnapshotJson = this._toComparableJson(this.settings);
            this.previousProjectName = this.projectName || "";
            this.previousAgentProfileKey = this.agentProfileKey || "";
            this.isLoading = false;
        }
    },

    async resetToDefault() {
        if (!this.pluginName) return;
        const confirmed = await showConfirmDialog({
            title: "Reset to Default",
            message: "This will replace the current settings with the plugin defaults. Any unsaved changes will be lost.",
            confirmText: "Reset",
            type: "warning",
        });
        if (!confirmed) return;
        const response = await fetchApi("/plugins", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "get_default_config", plugin_name: this.pluginName }),
        });
        const result = await response.json().catch(() => ({}));
        if (result.ok) {
            this.settings = result.data || {};
            justToast("Settings reset to default.", "info");
        }
    },

    async save() {
        if (!this.pluginName) return;
        this.isSaving = true;
        this.error = null;
        try {
            const response = await fetchApi("/plugins", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "save_config",
                    plugin_name: this.pluginName,
                    project_name: this.projectName || "",
                    agent_profile: this.agentProfileKey || "",
                    settings: this.settings,
                }),
            });
            const result = await response.json().catch(() => ({}));
            if (!result.ok) this.error = result.error || "Save failed";
            else {
                this.settingsSnapshotJson = this._toComparableJson(this.settings);
                window.closeModal?.();
            }
        } catch (e) {
            this.error = e?.message || "Save failed";
        } finally {
            this.isSaving = false;
        }
    },

    cleanup() {
        this.pluginName = null;
        this.pluginMeta = null;
        this.projects = [];
        this.agentProfiles = [];
        this.projectName = "";
        this.agentProfileKey = "";
        this.settings = {};
        this.settingsSnapshotJson = "";
        this.previousProjectName = "";
        this.previousAgentProfileKey = "";
        this.loadedPath = "";
        this.loadedProjectName = "";
        this.loadedAgentProfile = "";
        this.error = null;
        this.isLoading = false;
        this.isSaving = false;
        this.isListingConfigs = false;
        this.configsError = null;
        this.configs = [];
        this.perProjectConfig = true;
        this.perAgentConfig = true;
    },

    // Reactive URL for the plugin's settings component (used with x-html injection)
    get settingsComponentHtml() {
        if (!this.pluginName) return "";
        return `<x-component path="/plugins/${this.pluginName}/webui/config.html"></x-component>`;
    },
};

export const store = createStore("pluginSettingsPrototype", model);
