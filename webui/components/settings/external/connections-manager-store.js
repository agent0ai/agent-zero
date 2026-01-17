import { createStore } from "/js/AlpineStore.js";

const PASSWORD_PLACEHOLDER = "****PSWD****";

const model = {
  loading: false,
  saving: false,
  calendarAccounts: [],
  financeAccounts: [],
  calendarAuthUrl: "",
  financeAuthUrl: "",
  calendar: {
    clientId: "",
    clientSecret: "",
    redirectUri: "",
    secretConfigured: false,
    secretCleared: false,
  },
  finance: {
    clientId: "",
    secret: "",
    redirectUri: "",
    environment: "sandbox",
    secretConfigured: false,
    secretCleared: false,
  },

  async init() {
    this.hydrateFromSettings();
    await this.refreshAccounts();
  },

  hydrateFromSettings() {
    const fields = this._getSettingsFields();
    if (!fields.length) {
      return;
    }
    const getValue = (id) => {
      const field = fields.find((entry) => entry.id === id);
      return field ? field.value : "";
    };
    const calendarSecret = getValue("calendar_google_client_secret");
    const financeSecret = getValue("finance_plaid_secret");

    this.calendar.clientId = getValue("calendar_google_client_id") || "";
    this.calendar.redirectUri = getValue("calendar_google_redirect_uri") || "";
    this.calendar.secretConfigured = calendarSecret === PASSWORD_PLACEHOLDER;

    this.finance.clientId = getValue("finance_plaid_client_id") || "";
    this.finance.redirectUri = getValue("finance_plaid_redirect_uri") || "";
    this.finance.environment = getValue("finance_plaid_env") || "sandbox";
    this.finance.secretConfigured = financeSecret === PASSWORD_PLACEHOLDER;
  },

  updateField(id, value) {
    const field = this._getSettingsFields().find((entry) => entry.id === id);
    if (field) {
      field.value = value;
    }
  },

  clearCalendarSecret() {
    this.calendar.clientSecret = "";
    this.calendar.secretConfigured = false;
    this.calendar.secretCleared = true;
    this.updateField("calendar_google_client_secret", "");
  },

  clearFinanceSecret() {
    this.finance.secret = "";
    this.finance.secretConfigured = false;
    this.finance.secretCleared = true;
    this.updateField("finance_plaid_secret", "");
  },

  async saveSettings() {
    this.saving = true;
    try {
      const fields = [];
      fields.push({ id: "calendar_google_client_id", value: this.calendar.clientId });
      fields.push({ id: "calendar_google_redirect_uri", value: this.calendar.redirectUri });
      if (this.calendar.clientSecret) {
        fields.push({ id: "calendar_google_client_secret", value: this.calendar.clientSecret });
      } else if (this.calendar.secretCleared) {
        fields.push({ id: "calendar_google_client_secret", value: "" });
      }

      fields.push({ id: "finance_plaid_client_id", value: this.finance.clientId });
      fields.push({ id: "finance_plaid_redirect_uri", value: this.finance.redirectUri });
      fields.push({ id: "finance_plaid_env", value: this.finance.environment });
      if (this.finance.secret) {
        fields.push({ id: "finance_plaid_secret", value: this.finance.secret });
      } else if (this.finance.secretCleared) {
        fields.push({ id: "finance_plaid_secret", value: "" });
      }

      for (const entry of fields) {
        this.updateField(entry.id, entry.value);
      }

      const token = Alpine.store("csrfStore")?.token || "";
      const response = await fetch("/settings_set", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": token,
        },
        body: JSON.stringify({ sections: [{ fields }] }),
      });
      const data = await response.json();
      if (!data.settings) {
        throw new Error(data.error || "Failed to save settings");
      }
      this.calendar.secretCleared = false;
      this.finance.secretCleared = false;
      window.toastFrontendInfo?.("Connection settings saved", "Connections");
    } catch (error) {
      console.error("Failed to save connection settings:", error);
      window.toastFrontendError?.("Failed to save connection settings", "Connections");
    } finally {
      this.saving = false;
    }
  },

  async refreshAccounts() {
    this.loading = true;
    try {
      await Promise.all([this.refreshCalendarAccounts(), this.refreshFinanceAccounts()]);
    } finally {
      this.loading = false;
    }
  },

  async refreshCalendarAccounts() {
    const token = Alpine.store("csrfStore")?.token || "";
    const response = await fetch("/calendar_dashboard", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
      body: JSON.stringify({}),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || "Failed to load calendar accounts");
    }
    this.calendarAccounts = data.accounts || [];
    this.calendarAuthUrl = data.auth_url || "";
  },

  async refreshFinanceAccounts() {
    const token = Alpine.store("csrfStore")?.token || "";
    const response = await fetch("/finance_accounts_list", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
      body: JSON.stringify({}),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || "Failed to load finance accounts");
    }
    this.financeAccounts = data.accounts || [];
  },

  async startCalendarOAuth() {
    await this.saveSettings();
    const token = Alpine.store("csrfStore")?.token || "";
    const response = await fetch("/calendar_connect", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
      body: JSON.stringify({ provider: "google", mock: false }),
    });
    const data = await response.json();
    if (!data.success) {
      window.toastFrontendError?.(data.error || "Calendar OAuth failed", "Connections");
      return;
    }
    if (data.auth_url) {
      window.open(data.auth_url, "_blank");
    }
    await this.refreshCalendarAccounts();
  },

  async connectCalendarMock() {
    const token = Alpine.store("csrfStore")?.token || "";
    const response = await fetch("/calendar_connect", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
      body: JSON.stringify({ provider: "google", mock: true }),
    });
    const data = await response.json();
    if (!data.success) {
      window.toastFrontendError?.(data.error || "Calendar mock connect failed", "Connections");
      return;
    }
    await this.refreshCalendarAccounts();
  },

  async completeCalendarAuth(accountId) {
    const token = Alpine.store("csrfStore")?.token || "";
    const response = await fetch("/calendar_oauth_callback", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
      body: JSON.stringify({ account_id: accountId, token_ref: "mock-token", scopes: [] }),
    });
    await response.json();
    await this.refreshCalendarAccounts();
  },

  async startFinanceOAuth() {
    await this.saveSettings();
    const token = Alpine.store("csrfStore")?.token || "";
    const response = await fetch("/finance_connect", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
      body: JSON.stringify({ provider: "plaid", mock: false }),
    });
    const data = await response.json();
    if (!data.success) {
      window.toastFrontendError?.(data.error || "Finance OAuth failed", "Connections");
      return;
    }
    if (data.auth_url) {
      window.open(data.auth_url, "_blank");
    }
    await this.refreshFinanceAccounts();
  },

  async connectFinanceMock() {
    const token = Alpine.store("csrfStore")?.token || "";
    const response = await fetch("/finance_connect", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
      body: JSON.stringify({ provider: "plaid", mock: true }),
    });
    const data = await response.json();
    if (!data.success) {
      window.toastFrontendError?.(data.error || "Finance mock connect failed", "Connections");
      return;
    }
    await this.refreshFinanceAccounts();
  },

  async completeFinanceAuth(accountId) {
    const token = Alpine.store("csrfStore")?.token || "";
    const response = await fetch("/finance_oauth_callback", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
      body: JSON.stringify({ account_id: accountId }),
    });
    await response.json();
    await this.refreshFinanceAccounts();
  },

  _getSettingsFields() {
    try {
      return settingsModalProxy.settings.sections.flatMap((section) => section.fields);
    } catch (error) {
      return [];
    }
  },
};

const store = createStore("connectionsManager", model);

export { store };
