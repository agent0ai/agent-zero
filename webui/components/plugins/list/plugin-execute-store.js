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
  lastExecution: null,

  async open(plugin) {
    if (!plugin?.name) return;
    this.pluginName = plugin.name;
    this.pluginDisplayName = plugin.display_name || plugin.name;
    this.output = "";
    this.exitCode = null;
    this.lastExecution = null;
    window.openModal?.("components/plugins/list/plugin-execute-modal.html");
    await this.fetchLastExecution();
  },

  async fetchLastExecution() {
    try {
      const response = await api.callJsonApi("plugins", {
        action: "get_execute_record",
        plugin_name: this.pluginName,
      });
      this.lastExecution = response.data || null;
    } catch (e) {
      this.lastExecution = null;
    }
  },

  async run() {
    if (!this.pluginName) return;
    this.output = "";
    this.exitCode = null;
    this.running = true;
    try {
      const response = await api.callJsonApi("plugins", {
        action: "run_execute_script",
        plugin_name: this.pluginName,
      });
      this.output = response.output || "";
      this.exitCode = response.exit_code ?? null;
      if (response.executed_at) {
        this.lastExecution = {
          executed_at: response.executed_at,
          exit_code: response.exit_code ?? null,
        };
      }
    } catch (e) {
      this.output = e.message || String(e);
      this.exitCode = -1;
      notificationStore.frontendError(
        e.message || String(e),
        "Failed to run execute script",
        3,
        "pluginExecute",
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
    this.lastExecution = null;
  },
};

export const store = createStore("pluginExecuteStore", model);
