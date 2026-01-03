import { createStore } from "/js/AlpineStore.js";
import { scrollModal } from "/js/modals.js";
import sleep from "/js/sleep.js";
import * as API from "/js/api.js";

// Normalize server name to match backend behavior (lowercase, replace non-alphanumeric with underscore)
function normalizeName(name) {
  if (!name) return "";
  return name.trim().toLowerCase().replace(/[^\w]/g, "_");
}

// Find server object in config by normalized name, returns { serverObj, configKey }
function findServerInConfig(config, normalizedServerName) {
  if (Array.isArray(config)) {
    const serverObj = config.find(s => normalizeName(s.name) === normalizedServerName);
    return serverObj ? { serverObj, configKey: null } : null;
  } else if (config.mcpServers) {
    if (Array.isArray(config.mcpServers)) {
      const serverObj = config.mcpServers.find(s => normalizeName(s.name) === normalizedServerName);
      return serverObj ? { serverObj, configKey: null } : null;
    } else {
      // mcpServers is an object/dict - iterate keys
      for (const key of Object.keys(config.mcpServers)) {
        if (normalizeName(key) === normalizedServerName) {
          return { serverObj: config.mcpServers[key], configKey: key };
        }
      }
    }
  }
  return null;
}

const model = {
  editor: null,
  servers: [],
  loading: true,
  statusCheck: false,
  serverLog: "",
  currentDetailServer: null, // Added to hold tool details

  async initialize() {
    // Initialize the JSON Viewer after the modal is rendered
    const container = document.getElementById("mcp-servers-config-json");
    if (container) {
      const editor = ace.edit("mcp-servers-config-json");

      const dark = localStorage.getItem("darkMode");
      if (dark != "false") {
        editor.setTheme("ace/theme/github_dark");
      } else {
        editor.setTheme("ace/theme/tomorrow");
      }

      editor.session.setMode("ace/mode/json");
      const json = this.getSettingsFieldConfigJson().value;
      editor.setValue(json);
      editor.clearSelection();
      this.editor = editor;
    }

    this.startStatusCheck();
  },

  formatJson() {
    try {
      // get current content
      const currentContent = this.editor.getValue();

      // parse and format with 2 spaces indentation
      const parsed = JSON.parse(currentContent);
      const formatted = JSON.stringify(parsed, null, 2);

      // update editor content
      this.editor.setValue(formatted);
      this.editor.clearSelection();

      // move cursor to start
      this.editor.navigateFileStart();
    } catch (error) {
      console.error("Failed to format JSON:", error);
      alert("Invalid JSON: " + error.message);
    }
  },

  getEditorValue() {
    return this.editor.getValue();
  },

  getSettingsFieldConfigJson() {
    return settingsModalProxy.settings.sections
      .filter((x) => x.id == "mcp_client")[0]
      .fields.filter((x) => x.id == "mcp_servers")[0];
  },

  onClose() {
    const val = this.getEditorValue();
    this.getSettingsFieldConfigJson().value = val;
    this.stopStatusCheck();
  },

  async startStatusCheck() {
    this.statusCheck = true;
    let firstLoad = true;

    while (this.statusCheck) {
      await this._statusCheck();
      if (firstLoad) {
        this.loading = false;
        firstLoad = false;
      }
      await sleep(3000);
    }
  },

  async _statusCheck() {
    const resp = await API.callJsonApi("mcp_servers_status", null);
    if (resp.success) {
      this.servers = resp.status;
      this.servers.sort((a, b) => a.name.localeCompare(b.name));
    }
  },

  async stopStatusCheck() {
    this.statusCheck = false;
  },

  async applyNow() {
    if (this.loading) return;
    this.loading = true;
    try {
      // Only scroll if we aren't in the tools modal (checked via currentDetailServer existence implies focus elsewhere, but keeping simpler)
      // scrollModal("mcp-servers-status"); 
      const resp = await API.callJsonApi("mcp_servers_apply", {
        mcp_servers: this.getEditorValue(),
      });
      if (resp.success) {
        this.servers = resp.status;
        this.servers.sort((a, b) => a.name.localeCompare(b.name));
      }
      this.loading = false;
      await sleep(100); 
      // scrollModal("mcp-servers-status");
    } catch (error) {
      console.error("Failed to apply MCP servers:", error);
    }
    this.loading = false;
  },

  async getServerLog(serverName) {
    this.serverLog = "";
    const resp = await API.callJsonApi("mcp_server_get_log", {
      server_name: serverName,
    });
    if (resp.success) {
      this.serverLog = resp.log;
      openModal("settings/mcp/client/mcp-servers-log.html");
    }
  },

  async onToolCountClick(serverName) {
    const resp = await API.callJsonApi("mcp_server_get_detail", {
      server_name: serverName,
    });
    if (resp.success) {
      this.currentDetailServer = resp.detail; // Store detail for the modal
      openModal("settings/mcp/client/mcp-server-tools.html");
    }
  },

  // --- New Logic for Tool Toggling ---

  isToolDisabled(toolName) {
    if (!this.currentDetailServer || !this.currentDetailServer.disabled_tools) return false;
    return this.currentDetailServer.disabled_tools.includes(toolName);
  },

  async toggleTool(toolName) {
    if (!this.currentDetailServer) return;
    
    try {
        const rawConfig = this.getEditorValue();
        const config = JSON.parse(rawConfig);
        const serverName = this.currentDetailServer.name;

        const found = findServerInConfig(config, serverName);
        if (!found) {
            alert(`Could not find configuration block for server: ${serverName}`);
            return;
        }

        const { serverObj } = found;

        if (!serverObj.disabled_tools) {
            serverObj.disabled_tools = [];
        }

        if (serverObj.disabled_tools.includes(toolName)) {
            serverObj.disabled_tools = serverObj.disabled_tools.filter(t => t !== toolName);
        } else {
            serverObj.disabled_tools.push(toolName);
        }

        const newJson = JSON.stringify(config, null, 2);
        this.editor.setValue(newJson);
        this.editor.clearSelection();

        this.currentDetailServer.disabled_tools = [...serverObj.disabled_tools];

        await this.applyNow();

    } catch (e) {
        console.error("Error toggling tool:", e);
        alert("Cannot toggle tool: Config JSON is invalid.");
    }
  }
};

const store = createStore("mcpServersStore", model);

export { store };