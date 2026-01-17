import { createStore } from "/js/AlpineStore.js";

const model = {
    loading: false,
    error: null,
    accounts: [],
    calendars: [],
    events: [],
    rules: {},
    authUrl: null,
    selectedAccountId: null,
    selectedCalendarId: null,

    async init() {
        await this.refresh();
    },

    async refresh() {
        this.loading = true;
        this.error = null;
        try {
            const token = Alpine.store("csrfStore")?.token || "";
            const response = await fetch("/calendar_dashboard", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
                body: JSON.stringify({
                    account_id: this.selectedAccountId,
                    calendar_id: this.selectedCalendarId,
                }),
            });
            const data = await response.json();
            if (data.success) {
                this.accounts = data.accounts || [];
                this.calendars = data.calendars || [];
                this.events = data.events || [];
                this.rules = data.rules || {};
                this.authUrl = data.auth_url || null;
                if (!this.selectedAccountId && this.accounts.length) {
                    this.selectedAccountId = this.accounts[0].id;
                }
                if (!this.selectedCalendarId && this.calendars.length) {
                    this.selectedCalendarId = this.calendars[0].id;
                }
            } else {
                throw new Error(data.error || "Failed to load calendar dashboard");
            }
        } catch (err) {
            console.error("Calendar dashboard error:", err);
            this.error = err?.message || "Failed to load calendar dashboard";
        } finally {
            this.loading = false;
        }
    },

    async setAccount(accountId) {
        this.selectedAccountId = accountId ? Number(accountId) : null;
        this.selectedCalendarId = null;
        await this.refresh();
    },

    async setCalendar(calendarId) {
        this.selectedCalendarId = calendarId ? Number(calendarId) : null;
        await this.refresh();
    },

    openAuth() {
        if (this.authUrl) {
            window.open(this.authUrl, "_blank");
        }
    },

    async completeAuth(accountId) {
        const token = Alpine.store("csrfStore")?.token || "";
        const response = await fetch("/calendar_oauth_callback", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
            body: JSON.stringify({ account_id: accountId, token_ref: "mock-token", scopes: [] }),
        });
        await response.json();
        await this.refresh();
    },
};

createStore("calendarDashboard", model);
