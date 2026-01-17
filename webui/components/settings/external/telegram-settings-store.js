import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";

const model = {
  loading: false,
  saving: false,
  webhookInfo: null,
  settings: {
    bot_token: "",
    chat_id: "",
    webhook_url: "",
    webhook_secret: "",
    agent_context: "",
  },
  inboxItems: [],

  async init() {
    await this.refresh();
    await this.loadInbox();
  },

  async refresh() {
    this.loading = true;
    try {
      const response = await fetchApi("/telegram_settings_get", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });
      const data = await response.json();
      this.settings = data.settings || this.settings;
      this.webhookInfo = data.webhook_info || null;
    } catch (error) {
      console.error("Failed to load Telegram settings:", error);
      window.toastFrontendError("Failed to load Telegram settings", "Telegram");
    } finally {
      this.loading = false;
    }
  },

  async save() {
    this.saving = true;
    try {
      const response = await fetchApi("/telegram_settings_set", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ settings: this.settings }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Save failed");
      }
      window.toastFrontendInfo("Telegram settings saved", "Telegram");
    } catch (error) {
      console.error("Failed to save Telegram settings:", error);
      window.toastFrontendError("Failed to save Telegram settings", "Telegram");
    } finally {
      this.saving = false;
    }
  },

  async setWebhook() {
    this.saving = true;
    try {
      const response = await fetchApi("/telegram_webhook_set", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: this.settings.webhook_url,
          secret: this.settings.webhook_secret,
        }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Webhook setup failed");
      }
      window.toastFrontendInfo("Webhook updated", "Telegram");
      await this.refresh();
    } catch (error) {
      console.error("Failed to set webhook:", error);
      window.toastFrontendError("Failed to set webhook", "Telegram");
    } finally {
      this.saving = false;
    }
  },

  async testWebhook() {
    this.saving = true;
    try {
      const response = await fetchApi("/telegram_webhook_test", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: this.settings.webhook_url,
          secret: this.settings.webhook_secret,
        }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Webhook test failed");
      }
      window.toastFrontendInfo("Webhook test sent", "Telegram");
    } catch (error) {
      console.error("Webhook test failed:", error);
      window.toastFrontendError("Webhook test failed", "Telegram");
    } finally {
      this.saving = false;
    }
  },

  copyWebhookUrl() {
    const url = this.settings.webhook_url;
    if (!url) {
      window.toastFrontendError("Webhook URL is empty", "Telegram");
      return;
    }
    navigator.clipboard
      .writeText(url)
      .then(() => {
        window.toastFrontendInfo("Webhook URL copied", "Telegram");
      })
      .catch((err) => {
        console.error("Failed to copy webhook URL:", err);
        window.toastFrontendError("Failed to copy webhook URL", "Telegram");
      });
  },

  async loadInbox() {
    this.loading = true;
    try {
      const response = await fetchApi("/telegram_inbox_list", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ limit: 50, since_hours: 72 }),
      });
      const data = await response.json();
      this.inboxItems = data.items || [];
    } catch (error) {
      console.error("Failed to load inbox:", error);
      window.toastFrontendError("Failed to load inbox", "Telegram");
    } finally {
      this.loading = false;
    }
  },

  async sendReply(item) {
    if (!item.replyText) {
      return;
    }
    this.saving = true;
    try {
      const response = await fetchApi("/telegram_send_message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ chat_id: item.chat_id, text: item.replyText }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Send failed");
      }
      item.replyText = "";
      window.toastFrontendInfo("Reply sent", "Telegram");
    } catch (error) {
      console.error("Failed to send reply:", error);
      window.toastFrontendError("Failed to send reply", "Telegram");
    } finally {
      this.saving = false;
    }
  },
};

const store = createStore("telegramSettingsStore", model);

export { store };
