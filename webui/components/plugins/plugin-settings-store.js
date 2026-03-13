import { createStore } from "/js/AlpineStore.js";
import { showConfirmDialog } from "/js/confirmDialog.js";
import { store as settingsStore } from "/components/settings/settings-store.js";
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

        // Mirror scope change to pluginToggle so activation state stays in sync
        if (pluginToggleStore?.loadToggleStatus) {
            pluginToggleStore.projectName = nextProject;
            pluginToggleStore.agentProfileKey = nextProfile;
            await pluginToggleStore.loadToggleStatus();
        }
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

    // 'plugin' = save to plugin settings API
    // 'core'   = save via $store.settings.saveSettings() (for plugins that surface core settings)
    saveMode: 'plugin',

    perProjectConfig: true,
    perAgentConfig: true,

    isLoading: false,
    isSaving: false,
    error: null,

    // Called by the subsection button before openModal()
    // Optional scope: { projectName, agentProfileKey } — skips redundant global loadSettings()
    // when the caller already knows which scope to open at.
    async open(pluginName, { projectName = "", agentProfileKey = "", perProjectConfig = true, perAgentConfig = true } = {}) {
        this.pluginName = pluginName;
        this.pluginMeta = null;
        this.settings = {};
        this.settingsSnapshotJson = "";
        this.error = null;
        this.saveMode = 'plugin';
        this.perProjectConfig = perProjectConfig;
        this.perAgentConfig = perAgentConfig;
        this.projectName = projectName;
        this.agentProfileKey = agentProfileKey;
        this.previousProjectName = projectName;
        this.previousAgentProfileKey = agentProfileKey;
        this.loadedPath = "";
        this.loadedProjectName = "";
        this.loadedAgentProfile = "";
        await Promise.all([this.loadProjects(), this.loadAgentProfiles()]);
        await this.loadSettings();
    },

    // Called by x-create inside the modal on every open
    async onModalOpen() {
        if (this.pluginName) await this.loadSettings();
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

        // Core-backed plugins (e.g. memory) delegate to the settings store
        if (this.saveMode === 'core') {
            if (settingsStore?.saveSettings) {
                const ok = await settingsStore.saveSettings();
                if (ok) window.closeModal?.();
            }
            return;
        }

        // Plugin-specific settings: persist to plugin settings API
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
