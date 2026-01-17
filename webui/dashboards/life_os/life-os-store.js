import { createStore } from "/js/AlpineStore.js";

const model = {
    loading: false,
    error: null,
    dashboard: {
        event_count: 0,
        latest_event: null,
        widgets: [],
        sources: {},
    },

    async init() {
        await this.refresh();
    },

    async refresh() {
        this.loading = true;
        this.error = null;
        try {
            const token = Alpine.store("csrfStore")?.token || "";
            const response = await fetch("/life_os_dashboard", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
                body: JSON.stringify({}),
            });
            const data = await response.json();
            if (data.success) {
                this.dashboard = data.dashboard || this.dashboard;
            } else {
                throw new Error(data.error || "Failed to load Life OS dashboard");
            }
        } catch (err) {
            console.error("Life OS dashboard error:", err);
            this.error = err?.message || "Failed to load Life OS dashboard";
        } finally {
            this.loading = false;
        }
    },

    sourceCount(source) {
        return this.dashboard.sources?.[source] || 0;
    },

    formatPayload(payload) {
        if (!payload) return "";
        try {
            return JSON.stringify(payload);
        } catch (e) {
            return String(payload);
        }
    },
};

createStore("lifeOsDashboard", model);
