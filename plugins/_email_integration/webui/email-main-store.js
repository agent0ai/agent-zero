import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { toastFrontendError } from "/components/notifications/notification-store.js";

const PLUGIN_NAME = "_email_integration";

export const store = {
  loading: true,
  status: { inboxes: [], total: 0, enabled: 0, running: 0 },

  async init() {
    await this.refresh();
  },

  async refresh() {
    this.loading = true;
    try {
      this.status = await callJsonApi(`/plugins/${PLUGIN_NAME}/api/status`, {});
    } catch (error) {
      toastFrontendError(error, "Could not load email status");
    } finally {
      this.loading = false;
    }
  },

  openConfig() {
    window.Alpine.store("pluginSettings").openConfig(PLUGIN_NAME);
  },
};

createStore("emailMain", store);
