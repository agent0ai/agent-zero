import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, fetchApi } from "/js/api.js";

const model = {
    settings: {
        browser_mode: "chromium",
        headless: false,
        default_max_steps: 25,
        vision_mode: "auto",
        flash_mode: false,
        screencast_quality: 80,
        window_size: "1024x768",
        browser_use_api_key: "",
    },
    loading: false,
    _initialized: false,

    init() {
        if (this._initialized) return;
        this._initialized = true;
    },

    async load() {
        this.loading = true;
        try {
            const response = await fetchApi("/api/plugins/browser_use/browser_use_settings", {
                method: "GET",
            });
            const data = await response.json();
            if (data.settings) {
                Object.assign(this.settings, data.settings);
            }
        } catch (e) {
            console.error("Failed to load browser settings:", e);
        }
        this.loading = false;
    },

    async save() {
        try {
            await callJsonApi("/api/plugins/browser_use/browser_use_settings", {
                settings: this.settings,
            });
        } catch (e) {
            console.error("Failed to save browser settings:", e);
        }
    },
};

export const store = createStore("browserSettings", model);
