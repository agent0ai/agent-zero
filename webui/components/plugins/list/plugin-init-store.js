import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";
import {
  store as notificationStore,
  defaultPriority,
} from "/components/notifications/notification-store.js";

const model = {
  pluginName: "",
  pluginDisplayName: "",
  output: "",
  running: false,
  exitCode: null,
  lastExec: null,

  async open(plugin) {
    if (!plugin?.name) return;
    this.pluginName = plugin.name;
    this.pluginDisplayName = plugin.display_name || plugin.name;
    this.output = "";
    this.exitCode = null;
    this.lastExec = null;
    window.openModal?.("components/plugins/list/plugin-init-modal.html");
    await this.fetchLastExec();
  },

  async fetchLastExec() {
    try {
      const response = await api.callJsonApi("plugins", {
        action: "get_init_exec",
        plugin_name: this.pluginName,
      });
      this.lastExec = response.data || null;
    } catch (e) {
      this.lastExec = null;
    }
  },

  async run() {
    if (!this.pluginName) return;
    this.output = "";
    this.exitCode = null;
    this.running = true;
    try {
      const response = await api.callJsonApi("plugins", {
        action: "run_init_script",
        plugin_name: this.pluginName,
      });
      this.output = response.output || "";
      this.exitCode = response.exit_code ?? null;
      if (response.executed_at) {
        this.lastExec = { executed_at: response.executed_at, exit_code: response.exit_code ?? null };
      }
    } catch (e) {
      this.output = e.message || String(e);
      this.exitCode = -1;
      notificationStore.frontendError(
        e.message || String(e),
        "Failed to run init script",
        3,
        "pluginInit",
        defaultPriority,
        true,
      );
    } finally {
      this.running = false;
    }
  },

  cleanup() {
    this.pluginName = "";
    this.pluginDisplayName = "";
    this.output = "";
    this.running = false;
    this.exitCode = null;
    this.lastExec = null;
  },
};

export const store = createStore("pluginInitStore", model);
