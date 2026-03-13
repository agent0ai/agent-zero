import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, loadSettings, saveSettings } from "/js/api.js";

const model = {
    // Model selection state
    currentModel: null,        // {provider, name, displayName}
    availableModels: {},       // Models grouped by provider
    modelPickerOpen: false,    // Dropdown visibility
    searchQuery: "",           // Model search filter
    loading: false,
    error: null,
    currentBackend: "native",
    backendOptions: [
        { value: "native", label: "Native" },
        { value: "claude_code", label: "Claude Code" },
        { value: "codex", label: "Codex" },
    ],

    // Thinking mode state
    thinkingEnabled: false,
    thinkingBudget: 1024,

    // Favorites (stored in localStorage)
    favorites: [],

    // Initialize on component mount
    async init() {
        await this.loadModels();
        await this.loadExecutionBackend();
        await this.loadThinkingSettings();
        this.loadFavorites();
    },

    async loadExecutionBackend() {
        try {
            const settings = await loadSettings();
            this.currentBackend = settings.chat_execution_backend || "native";
        } catch (err) {
            console.error("Failed to load chat execution backend:", err);
            this.currentBackend = "native";
        }
    },

    // Load available models from LLM Router
    async loadModels() {
        this.loading = true;
        try {
            const resp = await callJsonApi("/llm_router_dashboard", {});
            if (resp.success) {
                this.availableModels = resp.models?.byProvider || {};
                // Set current model from defaults or settings
                if (resp.defaults?.chat) {
                    this.currentModel = {
                        provider: resp.defaults.chat.provider,
                        name: resp.defaults.chat.modelName,
                        displayName: resp.defaults.chat.modelName
                    };
                }
            }
        } catch (err) {
            console.error("Failed to load models:", err);
            this.error = err.message;
        } finally {
            this.loading = false;
        }
    },

    // Load thinking settings
    async loadThinkingSettings() {
        try {
            const settings = await loadSettings();
            this.thinkingEnabled = settings.thinking_enabled || false;
            this.thinkingBudget = settings.thinking_budget || 1024;
        } catch (err) {
            console.error("Failed to load thinking settings:", err);
        }
    },

    // Load favorites from localStorage
    loadFavorites() {
        try {
            const stored = localStorage.getItem("model_favorites");
            this.favorites = stored ? JSON.parse(stored) : [];
        } catch (err) {
            this.favorites = [];
        }
    },

    // Save favorites to localStorage
    saveFavorites() {
        try {
            localStorage.setItem("model_favorites", JSON.stringify(this.favorites));
        } catch (err) {
            console.error("Failed to save favorites:", err);
        }
    },

    // Toggle a model as favorite
    toggleFavorite(provider, modelName) {
        const key = `${provider}/${modelName}`;
        const idx = this.favorites.indexOf(key);
        if (idx >= 0) {
            this.favorites.splice(idx, 1);
        } else {
            this.favorites.push(key);
        }
        this.saveFavorites();
    },

    // Check if model is favorite
    isFavorite(provider, modelName) {
        return this.favorites.includes(`${provider}/${modelName}`);
    },

    // Get favorite models as array
    getFavoriteModels() {
        const result = [];
        for (const key of this.favorites) {
            const [provider, ...nameParts] = key.split("/");
            const modelName = nameParts.join("/");
            const providerModels = this.availableModels[provider];
            if (providerModels) {
                const modelInfo = providerModels.find(m => m.name === modelName);
                if (modelInfo) {
                    result.push({ provider, ...modelInfo });
                }
            }
        }
        return result;
    },

    // Switch to a different model
    async switchModel(provider, modelName) {
        this.loading = true;
        try {
            const resp = await callJsonApi("/model_selector_quick_switch", {
                provider,
                modelName: modelName
            });
            if (resp.success) {
                this.currentModel = {
                    provider,
                    name: modelName,
                    displayName: modelName
                };
                this.modelPickerOpen = false;
            } else {
                this.error = resp.error || "Failed to switch model";
            }
        } catch (err) {
            this.error = err.message;
        } finally {
            this.loading = false;
        }
    },

    async switchBackend(backend) {
        if (!backend || backend === this.currentBackend) return;
        const previous = this.currentBackend;
        this.currentBackend = backend;
        try {
            await saveSettings({
                chat_execution_backend: backend,
            });
        } catch (err) {
            this.currentBackend = previous;
            this.error = "Failed to switch backend: " + err.message;
        }
    },

    // Toggle thinking mode
    async toggleThinking() {
        this.thinkingEnabled = !this.thinkingEnabled;
        try {
            await saveSettings({
                thinking_enabled: this.thinkingEnabled,
                thinking_budget: this.thinkingBudget
            });
        } catch (err) {
            // Revert on error
            this.thinkingEnabled = !this.thinkingEnabled;
            this.error = "Failed to save thinking setting: " + err.message;
        }
    },

    // Update thinking budget
    async setThinkingBudget(budget) {
        this.thinkingBudget = budget;
        try {
            await saveSettings({
                thinking_enabled: this.thinkingEnabled,
                thinking_budget: budget
            });
        } catch (err) {
            this.error = "Failed to save thinking budget: " + err.message;
        }
    },

    // Toggle model picker dropdown
    togglePicker() {
        this.modelPickerOpen = !this.modelPickerOpen;
        if (this.modelPickerOpen) {
            this.searchQuery = "";
        }
    },

    // Close picker when clicking outside
    closePicker() {
        this.modelPickerOpen = false;
    },

    // Filter models based on search query
    getFilteredModels() {
        if (!this.searchQuery) {
            return this.availableModels;
        }
        const query = this.searchQuery.toLowerCase();
        const filtered = {};
        for (const [provider, models] of Object.entries(this.availableModels)) {
            const matching = models.filter(m =>
                m.name.toLowerCase().includes(query) ||
                (m.displayName && m.displayName.toLowerCase().includes(query)) ||
                provider.toLowerCase().includes(query)
            );
            if (matching.length > 0) {
                filtered[provider] = matching;
            }
        }
        return filtered;
    },

    // Get provider icon
    getProviderIcon(provider) {
        const icons = {
            ollama: "🦙",
            openai: "🤖",
            anthropic: "🧠",
            google: "🔮",
            groq: "⚡",
            mistral: "🌊",
            azure: "☁️",
            default: "💬"
        };
        return icons[provider?.toLowerCase()] || icons.default;
    },

    // Format cost display
    formatCost(model) {
        if (model.isLocal) return "Local";
        if (!model.costPer1kInput && !model.costPer1kOutput) return "Free";
        const input = model.costPer1kInput || 0;
        const output = model.costPer1kOutput || 0;
        return `$${input}/$${output}`;
    },

    // Format context length
    formatContext(length) {
        if (!length) return "";
        if (length >= 1000000) return `${(length / 1000000).toFixed(1)}M`;
        if (length >= 1000) return `${Math.round(length / 1000)}k`;
        return length.toString();
    },

    // Get display name for current model
    getCurrentModelDisplay() {
        if (!this.currentModel) return "Select Model";
        return this.currentModel.displayName || this.currentModel.name;
    },

    getCurrentBackendLabel() {
        const option = this.backendOptions.find((o) => o.value === this.currentBackend);
        return option?.label || this.currentBackend || "Native";
    }
};

export const store = createStore("modelSelector", model);
