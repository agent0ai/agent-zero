import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
    frameworks: [],
    selectedFramework: null,
    loading: false,
    error: null,
    _initialized: false,

    async init() {
        if (this._initialized) return;
        this._initialized = true;
        await this.loadFrameworks();
    },

    async loadFrameworks() {
        this.loading = true;
        this.error = null;
        try {
            const response = await callJsonApi("frameworks", { action: "list" });
            if (response.ok) {
                this.frameworks = response.data;
                // Select current framework from settings
                const currentFramework = this.getCurrentFrameworkId();
                this.selectFramework(currentFramework);
            } else {
                this.error = response.error || "Failed to load frameworks";
            }
        } catch (e) {
            this.error = e.message || "Failed to load frameworks";
        } finally {
            this.loading = false;
        }
    },

    getCurrentFrameworkId() {
        // Get from settings store - new structure has settings.dev_framework directly
        const settingsStore = window.Alpine?.store("settingsStore");
        if (settingsStore?.settings?.dev_framework) {
            return settingsStore.settings.dev_framework;
        }
        return "none";
    },

    selectFramework(frameworkId) {
        this.selectedFramework = this.frameworks.find(f => f.id === frameworkId) || null;
    },

    getWorkflowSteps() {
        if (!this.selectedFramework) return [];
        return this.selectedFramework.workflows || [];
    },

    onClose() {
        // Cleanup if needed
    }
};

export const store = createStore("frameworkStore", model);
