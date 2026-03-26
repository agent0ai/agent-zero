import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";
import { toastFrontendError } from "/components/notifications/notification-store.js";
import { store as pluginSettingsStore } from "/components/plugins/plugin-settings-store.js";

const model = {
  tab: "",
  plugins: [],
  loading: false,

  resolveTab(element) {
    const host =
      element?.closest("x-component")
      || element?.parentElement?.closest("x-component");
    return host?.getAttribute("data-tab") || "";
  },

  async init(element) {
    this.tab = this.resolveTab(element);
    await this.load();
  },

  cleanup() {
    this.tab = "";
    this.plugins = [];
    this.loading = false;
  },

  async load() {
    if (!this.tab) {
      this.plugins = [];
      return;
    }

    this.loading = true;
    try {
      const response = await api.callJsonApi("plugins_list", {
        filter: { custom: true, builtin: true },
      });
      const plugins = Array.isArray(response?.plugins) ? response.plugins : [];
      this.plugins = plugins.filter((plugin) => {
        const sections = Array.isArray(plugin?.settings_sections)
          ? plugin.settings_sections
          : [];
        return plugin?.has_config_screen && sections.includes(this.tab);
      });
    } catch {
      this.plugins = [];
    } finally {
      this.loading = false;
    }
  },

  async openPluginConfig(plugin) {
    if (!plugin?.name) return;
    try {
      await pluginSettingsStore.openConfig(plugin.name);
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      void toastFrontendError(message, "Plugin Settings");
    }
  },
};

export const store = createStore("pluginsSubsectionPrototype", model);
