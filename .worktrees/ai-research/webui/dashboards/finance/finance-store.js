import { createStore } from "/js/AlpineStore.js";

const model = {
    loading: false,
    error: null,
    period: "",
    report: {},
    roi: {},
    authUrl: null,
    hasAuth: false,

    async init() {
        const now = new Date();
        this.period = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
        await this.refresh();
    },

    async refresh() {
        this.loading = true;
        this.error = null;
        try {
            const token = Alpine.store("csrfStore")?.token || "";
            const response = await fetch("/finance_dashboard", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
                body: JSON.stringify({ period: this.period }),
            });
            const data = await response.json();
            if (data.success) {
                this.report = data.report || {};
                this.roi = data.roi || {};
                this.authUrl = data.auth_url || null;
                this.hasAuth = Boolean(this.report?.total_count || this.roi?.income);
            } else {
                throw new Error(data.error || "Failed to load finance dashboard");
            }
        } catch (err) {
            console.error("Finance dashboard error:", err);
            this.error = err?.message || "Failed to load finance dashboard";
        } finally {
            this.loading = false;
        }
    },

    formatCurrency(value) {
        const amount = Number(value || 0);
        return `$${amount.toFixed(2)}`;
    },

    formatRoi(value) {
        if (value === null || value === undefined) return "N/A";
        return `${(value * 100).toFixed(2)}%`;
    },

    async setPeriod(period) {
        this.period = period || this.period;
        await this.refresh();
    },

    openAuth() {
        if (this.authUrl) {
            window.open(this.authUrl, "_blank");
        }
    },

    async completeAuth(accountId) {
        const token = Alpine.store("csrfStore")?.token || "";
        const response = await fetch("/finance_oauth_callback", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
            body: JSON.stringify({ account_id: accountId || 1 }),
        });
        await response.json();
        await this.refresh();
    },
};

createStore("financeDashboard", model);
