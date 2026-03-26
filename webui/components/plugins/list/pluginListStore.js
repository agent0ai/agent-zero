import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";
import { marked } from "/vendor/marked/marked.esm.js";
import { addBlankTargetsToLinks } from "/js/messages.js";
import { store as pluginSettingsStore } from "/components/plugins/plugin-settings-store.js";
import { store as pluginToggleStore } from "/components/plugins/toggle/plugin-toggle-store.js";
import { store as pluginExecuteStore } from "/components/plugins/list/plugin-execute-store.js";
import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";
import { store as markdownModalStore } from "/components/modals/markdown/markdown-store.js";
import { callJsExtensions } from "/js/extensions.js";
import {
  store as notificationStore,
  defaultPriority,
} from "/components/notifications/notification-store.js";

// define the model object holding data and functions
const model = {
  loading: false,
  plugins: [],
  selectedPlugin: null,
  activeTab: "custom",
  readmeContent: "",
  readmeLoading: false,
  readmeError: "",

  async init() {
    this.loading = false;
    await this.setTab('custom');
    if (this.plugins.length === 0) {
        await this.setTab('builtin');
    }
  },

  async loadPluginList(filter) {
    this.loading = true;
    this.selectedPlugin = null;
    try {
      const response = await api.callJsonApi("plugins_list", { filter });
      this.plugins = Array.isArray(response.plugins) ? response.plugins : [];
      void callJsExtensions("plugins_list_after_load", {
        filter: filter ? { ...filter } : null,
        plugins: this.plugins,
        store: this,
      });
    } catch (e) {
      this.plugins = [];
      showErrorNotification(e, "Failed to load plugins list");
    } finally {
      this.loading = false;
    }
  },

  async setTab(tab) {
    if (tab === "pluginHub") {
      this.activeTab = "pluginHub";
      this.loading = false;
      return;
    }

    this.activeTab = tab === "builtin" ? "builtin" : "custom";
    const filter =
      this.activeTab === "builtin"
        ? { builtin: true, custom: false, search: "" }
        : { builtin: false, custom: true, search: "" };
    await this.loadPluginList(filter);
  },

  async refresh() {
    if (this.activeTab === "pluginHub") {
      return;
    }
    await this.setTab(this.activeTab);
  },

  openPlugin(plugin) {
    if (!plugin?.name || !plugin?.has_main_screen) return;
    window.openModal?.(`/plugins/${plugin.name}/webui/main.html`);
  },

  openPluginExecute(plugin) {
    if (!plugin?.name || !plugin?.has_execute_script) return;
    pluginExecuteStore.open(plugin);
  },

  async openPluginConfig(plugin) {
    if (!plugin?.name || !plugin?.has_config_screen) return;
    try {
      if (!pluginSettingsStore?.openConfig) {
        throw new Error("Plugin settings store is unavailable.");
      }
      await pluginSettingsStore.openConfig(plugin.name);
    } catch (e) {
      showErrorNotification(e, "Failed to open plugin config");
    }
  },

  async openPluginAdvancedToggle(plugin) {
    if (!plugin?.name) return;
    this.selectedPlugin = plugin;
    try {
        if (!pluginToggleStore?.open) {
            throw new Error("Plugin toggle store is unavailable.");
        }
        await pluginToggleStore.open(plugin);
        window.openModal?.("components/plugins/toggle/plugin-toggle-advanced.html");
    } catch (e) {
        showErrorNotification(e, "Failed to open plugin switch");
    }
  },

  async updateToggle(plugin, value) {
    if (!plugin?.name) return;
    
    if (value === 'advanced') {
        await this.openPluginAdvancedToggle(plugin);
        return; 
    }

    const enabled = value === 'enabled';
    const clearOverrides = plugin.toggle_state === 'advanced';
    if (clearOverrides && !window.confirm(
        `"${plugin.display_name || plugin.name}" has per-scope activation rules that will be removed. Set globally to ${enabled ? 'ON' : 'OFF'}?`
    )) return;

    this.loading = true;
    try {
        const response = await api.callJsonApi("plugins", {
            action: "toggle_plugin",
            plugin_name: plugin.name,
            enabled: enabled,
            project_name: "",
            agent_profile: "",
            clear_overrides: clearOverrides,
        });
        if (response?.error) throw new Error(response.error);
        await this.refresh();
    } catch (e) {
        showErrorNotification(e, "Failed to toggle plugin");
        this.loading = false;
    }
  },

  async openPluginDoc(plugin, doc) {
    try {
      const response = await api.callJsonApi("plugins", {
        action: "get_doc",
        plugin_name: plugin.name,
        doc,
      });
      if (response?.error) throw new Error(response.error);
      if (!markdownModalStore?.open) throw new Error("Markdown modal store unavailable.");
      markdownModalStore.open(response.filename, response.content);
      window.openModal?.("components/modals/markdown/markdown-modal.html");
    } catch (e) {
      showErrorNotification(e, "Failed to open document");
    }
  },

  async loadPluginReadme(plugin) {
    this.readmeLoading = true;
    this.readmeContent = "";
    this.readmeError = "";
    try {
      const response = await api.callJsonApi("plugins", {
        action: "get_doc",
        plugin_name: plugin.name,
        doc: "readme",
      });
      if (response?.error) throw new Error(response.error);
      const html = marked.parse(response.content || "", { breaks: true });
      this.readmeContent = addBlankTargetsToLinks(html);
    } catch (e) {
      const error = e instanceof Error ? e : new Error(String(e));
      this.readmeError = error.message || "Failed to load README";
    } finally {
      this.readmeLoading = false;
    }
  },

  openPluginInfo(plugin) {
    if (!plugin) return;
    this.selectedPlugin = plugin;
    this.readmeContent = "";
    this.readmeLoading = false;
    this.readmeError = "";
    if (plugin.has_readme) {
      void this.loadPluginReadme(plugin);
    }
    window.openModal?.("components/plugins/plugin-info.html");
  },

  async openPluginFolder(plugin) {
    if (!plugin?.path) return;
    await fileBrowserStore.open(plugin.path);
  },

  async openPluginHub(plugin) {
    const pluginKey = (plugin?.pluginHub?.key || "").trim();
    if (!pluginKey) return;
    const { store: pluginInstallStore } = await import(
      "/plugins/_plugin_installer/webui/pluginInstallStore.js"
    );
    await pluginInstallStore.openPluginHubDetailByKey(pluginKey);
  },

  async deletePlugin(plugin) {
    if (!plugin?.name) return;

    if (!plugin.is_custom) {
      showErrorNotification(
        new Error("Only custom plugins can be deleted from this modal."),
        "Delete blocked",
      );
      return;
    }

    try {
      const response = await api.callJsonApi("plugins", {
        action: "delete_plugin",
        plugin_name: plugin.name,
      });
      if (response?.error) {
        throw new Error(response.error);
      }
      if (window.toastFrontendSuccess) {
        window.toastFrontendSuccess("Plugin deleted", "Plugins");
      }
      await this.refresh();
    } catch (e) {
      showErrorNotification(e, "Failed to delete plugin");
    }
  },
};

function showErrorNotification(error, heading) {
    const text = error.message || error.text || JSON.stringify(error);
  notificationStore.frontendError(
    text,
    heading,
    3,
    "pluginsList",
    defaultPriority,
    true,
  );
}

// convert it to alpine store
const store = createStore("pluginListStore", model);

// export for use in other files
export { store };
