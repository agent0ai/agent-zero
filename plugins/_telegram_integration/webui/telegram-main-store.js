import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { toastFrontendError } from "/components/notifications/notification-store.js";
import { store as pluginSettings } from "/components/plugins/plugin-settings-store.js";

export const store = createStore("telegramMain", {
  bots: [],
  configured: 0,
  running: 0,
  loading: false,

  async refresh() {
    if (this.loading) return;
    this.loading = true;
    try {
      const data = await callJsonApi("/plugins/_telegram_integration/status", {});
      this.bots = data.bots || [];
      this.configured = Number(data.configured || 0);
      this.running = Number(data.running || 0);
    } catch (error) {
      void toastFrontendError(error, "Telegram status");
    } finally {
      this.loading = false;
    }
  },

  async openConfig() {
    try {
      await pluginSettings.openConfig("_telegram_integration");
    } catch (error) {
      void toastFrontendError(error, "Telegram configuration");
    }
  },
});
