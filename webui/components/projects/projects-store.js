import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";
import * as modals from "/js/modals.js";
import * as notifications from "/components/notifications/notification-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as browserStore } from "/components/modals/file-browser/file-browser-store.js";
import * as shortcuts from "/js/shortcuts.js";

const listModal = "projects/project-list.html";
const createModal = "projects/project-create.html";
const editModal = "projects/project-edit.html";

// define the model object holding data and functions
const model = {
  projectList: [],
  selectedProject: null,
  editData: null,
  colors: [
    "#7b2cbf", // Deep Purple
    "#8338ec", // Blue Violet
    "#9b5de5", // Amethyst
    "#d0bfff", // Lavender
    "#002975ff", // Prussian Blue
    "#3a86ff", // Azure
    "#0077b6", // Star Command Blue
    "#4cc9f0", // Bright Blue
    "#00bbf9", // Deep Sky Blue
    "#a5d8ff", // Baby Blue
    "#00f5d4", // Electric Blue
    "#06d6a0", // Teal
    "#1a7431", // Dartmouth Green
    "#2a9d8f", // Jungle Green
    "#b2f2bb", // Light Mint
    "#9ef01a", // Lime Green
    "#e9c46a", // Saffron
    "#fee440", // Lemon Yellow
    "#ffec99", // Pale Yellow
    "#ff9f43", // Bright Orange
    "#fb5607", // Orange Peel
    "#ffddb5", // Peach
    "#f95738", // Coral
    "#e76f51", // Burnt Sienna
    "#ff6b6b", // Vibrant Red
    "#ffc9c9", // Light Coral
    "#f15bb5", // Hot Pink
    "#ff006e", // Magenta
    "#ffafcc", // Carnation Pink
    "#adb5bd", // Cool Gray
    "#6c757d", // Slate Gray
  ],

  _toFolderName(str) {
    if (!str) return "";
    // a helper function to convert title to a folder safe name
    const s = str
      .normalize("NFD") // remove all diacritics and replace it with the latin character
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "_") // replace all special symbols with _
      .replace(/\s+/g, "_") // replace spaces with _
      .replace(/_{2,}/g, "_") // condense multiple underscores into 1
      .replace(/^-+|-+$/g, "") // remove any leading and trailing underscores
      .replace(/^_+|_+$/g, "");
    return s;
  },

  async openProjectsModal() {
    await this.loadProjectsList();
    await modals.openModal(listModal);
  },

  async openCreateModal() {
    this.selectedProject = this._createNewProjectData();
    await modals.openModal(createModal);
    this.selectedProject = null;
  },

  async openEditModal(name) {
    this.selectedProject = await this._createEditProjectData(name);
    await modals.openModal(editModal);
    this.selectedProject = null;
  },

  async cancelCreate() {
    await modals.closeModal(createModal);
  },

  async cancelEdit() {
    await modals.closeModal(editModal);
  },

  async confirmCreate() {
    // create folder name based on title
    this.selectedProject.name = this._toFolderName(this.selectedProject.title);
    const project = await this.saveSelectedProject(true);
    await this.loadProjectsList();
    await modals.closeModal(createModal);
    await this.openEditModal(project.name);
  },

  async confirmEdit() {
    const project = await this.saveSelectedProject(false);
    await this.loadProjectsList();
    await modals.closeModal(editModal);
  },

  async activateProject(name) {
    try {
      const response = await api.callJsonApi("projects", {
        action: "activate",
        context_id: chatsStore.getSelectedChatId(),
        name: name,
      });
      if (response?.ok) {
        notifications.toastFrontendSuccess(
          "Project activated successfully",
          "Project activated",
          3,
          "projects",
          notifications.NotificationPriority.NORMAL,
          true
        );
      } else {
        notifications.toastFrontendWarning(
          response?.error || "Project activation reported issues",
          "Project activation",
          5,
          "projects",
          notifications.NotificationPriority.NORMAL,
          true
        );
      }
    } catch (error) {
      console.error("Error activating project:", error);
      notifications.toastFrontendError(
        "Error activating project: " + error,
        "Error activating project",
        5,
        "projects",
        notifications.NotificationPriority.NORMAL,
        true
      );
    }
    await this.loadProjectsList();
  },

  async deactivateProject() {
    try {
      const response = await api.callJsonApi("projects", {
        action: "deactivate",
        context_id: chatsStore.getSelectedChatId(),
      });
      if (response?.ok) {
        notifications.toastFrontendSuccess(
          "Project deactivated successfully",
          "Project deactivated",
          3,
          "projects",
          notifications.NotificationPriority.NORMAL,
          true
        );
      } else {
        notifications.toastFrontendWarning(
          response?.error || "Project deactivation reported issues",
          "Project deactivated",
          5,
          "projects",
          notifications.NotificationPriority.NORMAL,
          true
        );
      }
    } catch (error) {
      console.error("Error deactivating project:", error);
      notifications.toastFrontendError(
        "Error deactivating project: " + error,
        "Error deactivating project",
        5,
        "projects",
        notifications.NotificationPriority.NORMAL,
        true
      );
    }
    await this.loadProjectsList();
  },

  async deleteProjectAndCloseModal() {
    await this.deleteProject(this.selectedProject.name);
    await modals.closeModal(editModal);
  },

  async deleteProject(name) {
    // show confirmation dialog before proceeding
    const confirmed = window.confirm(
      "Are you sure you want to permanently delete this project? This action is irreversible and ALL FILES will be deleted."
    );
    if (!confirmed) return;
    try {
      const response = await api.callJsonApi("projects", {
        action: "delete",
        name: name,
      });
      if (response.ok) {
        notifications.toastFrontendSuccess(
          "Project deleted successfully",
          "Project deleted",
          3,
          "projects",
          notifications.NotificationPriority.NORMAL,
          true
        );
        await this.loadProjectsList();
      } else {
        notifications.toastFrontendWarning(
          response.error || "Project deletion blocked",
          "Project delete",
          5,
          "projects",
          notifications.NotificationPriority.NORMAL,
          true
        );
      }
    } catch (error) {
      console.error("Error deleting project:", error);
      notifications.toastFrontendError(
        "Error deleting project: " + error,
        "Error deleting project",
        5,
        "projects",
        notifications.NotificationPriority.NORMAL,
        true
      );
    }
  },

  async loadProjectsList() {
    this.loading = true;
    try {
      const response = await api.callJsonApi("projects", {
        action: "list",
      });
      this.projectList = response.data || [];
    } catch (error) {
      console.error("Error loading projects list:", error);
    } finally {
      this.loading = false;
    }
  },

  async saveSelectedProject(creating) {
    try {
      // prepare data
      const data = {
        ...this.selectedProject,
        memory: this.selectedProject._ownMemory ? "own" : "global",
      };
      // remove internal fields
      for (const kvp of Object.entries(data))
        if (kvp[0].startsWith("_")) delete data[kvp[0]];

      const response = await api.callJsonApi("projects", {
        action: creating ? "create" : "update",
        project: data,
      });

      if (!creating && this.selectedProject._mcpServers) {
        await api.callJsonApi("project_mcp_servers", {
          action: "save",
          project_name: this.selectedProject.name,
          config: this.selectedProject._mcpServers,
        });
      }

      if (response.ok) {
        notifications.toastFrontendSuccess(
          "Project saved successfully",
          "Project saved",
          3,
          "projects",
          notifications.NotificationPriority.NORMAL,
          true
        );
        return response.data;
      } else {
        notifications.toastFrontendError(
          response.error || "Error saving project",
          "Error saving project",
          5,
          "projects",
          notifications.NotificationPriority.NORMAL,
          true
        );
        return null;
      }
    } catch (error) {
      console.error("Error saving project:", error);
      notifications.toastFrontendError(
        "Error saving project: " + error,
        "Error saving project",
        5,
        "projects",
        notifications.NotificationPriority.NORMAL,
        true
      );
      return null;
    }
  },

  _createNewProjectData() {
    return {
      _meta: {
        creating: true,
      },
      _ownMemory: true,
      name: ``,
      title: `Project #${this.projectList.length + 1}`,
      description: "",
      color: "",
    };
  },

  async _createEditProjectData(name) {
    const projectData = (
      await api.callJsonApi("projects", {
        action: "load",
        name: name,
      })
    ).data;
    return {
      _meta: {
        creating: false,
      },
      ...projectData,
      _ownMemory: projectData.memory == "own",
    };
  },

  async browseSelected(...relPath) {
    const path = this.getSelectedAbsPath(...relPath);
    return await browserStore.open(path);
  },

  async browseInstructionFiles() {
    await this.browseSelected(".a0proj", "instructions");
    try {
      const newData = await this._createEditProjectData(
        this.selectedProject.name
      );
      this.selectedProject.instruction_files_count =
        newData.instruction_files_count;
    } catch (error) {
      //pass
    }
  },

  async browseKnowledgeFiles() {
    await this.browseSelected(".a0proj", "knowledge");
    // refresh and reindex project
    try {
      // progress notification
      shortcuts.frontendNotification({
        type: shortcuts.NotificationType.PROGRESS,
        message: "Loading knowledge...",
        priority: shortcuts.NotificationPriority.NORMAL,
        displayTime: 999,
        group: "knowledge_load",
        frontendOnly: true,
      });

      // call reindex knowledge
      const reindexCall = api.callJsonApi("/knowledge_reindex", {
        ctxid: shortcuts.getCurrentContextId(),
      });

      const newData = await this._createEditProjectData(
        this.selectedProject.name
      );
      this.selectedProject.knowledge_files_count =
        newData.knowledge_files_count;

      // wait for reindex to finish
      await reindexCall;

      // finished notification
      shortcuts.frontendNotification({
        type: shortcuts.NotificationType.SUCCESS,
        message: "Knowledge loaded successfully",
        priority: shortcuts.NotificationPriority.NORMAL,
        displayTime: 2,
        group: "knowledge_load",
        frontendOnly: true,
      });
    } catch (error) {
      // error notification
      shortcuts.frontendNotification({
        type: shortcuts.NotificationType.ERROR,
        message: "Error loading knowledge",
        priority: shortcuts.NotificationPriority.NORMAL,
        displayTime: 5,
        group: "knowledge_load",
        frontendOnly: true,
      });
    }
  },

  getSelectedAbsPath(...relPath) {
    return ["/a0/usr/projects", this.selectedProject.name, ...relPath]
      .join("/")
      .replace(/\/+/g, "/");
  },

  async editActiveProject() {
    const ctx = shortcuts.getCurrentContext();
    if(!ctx) return;
    this.openEditModal(ctx.project.name);
  },

  async testFileStructure() {
    try {
      const response = await api.callJsonApi("projects", {
        action: "file_structure",
        name: this.selectedProject.name,
        settings: this.selectedProject.file_structure,
      });
      this.fileStructureTestOutput = response.data;
      shortcuts.openModal("projects/project-file-structure-test.html");
    } catch (error) {
      console.error("Error testing file structure:", error);
      shortcuts.frontendNotification({
        type: shortcuts.NotificationType.ERROR,
        message: "Error testing file structure",
        priority: shortcuts.NotificationPriority.NORMAL,
        displayTime: 3,
        frontendOnly: true,
      });
    }
  },

  mcpEditor: null,
  mcpGlobalServers: {},
  mcpLoading: true,
  mcpApplying: false,
  mcpServerToolsCache: {},
  mcpExpandedServers: {},
  mcpServerStatus: [],

  async initMcpEditor() {
    this.mcpLoading = true;
    this.mcpEditor = null;
    this.mcpApplying = false;
    this.mcpServerToolsCache = {};
    this.mcpExpandedServers = {};
    this.mcpServerStatus = [];
    
    await this._loadMcpConfig();
    await this._loadGlobalServers();

    const container = document.getElementById("project-mcp-editor");
    if (!container) {
      this.mcpLoading = false;
      return;
    }

    const editor = ace.edit("project-mcp-editor");
    const dark = localStorage.getItem("darkMode");
    editor.setTheme(dark !== "false" ? "ace/theme/github_dark" : "ace/theme/tomorrow");
    editor.session.setMode("ace/mode/json");
    editor.setValue(this.selectedProject._mcpServers || '{\n    "mcpServers": {}\n}');
    editor.clearSelection();
    this.mcpEditor = editor;

    editor.session.on("change", () => {
      this.selectedProject._mcpServers = editor.getValue();
    });
    this.mcpLoading = false;
  },

  async _loadMcpConfig() {
    try {
      const resp = await api.callJsonApi("project_mcp_servers", {
        action: "load",
        project_name: this.selectedProject.name,
      });
      if (resp.success) {
        this.selectedProject._mcpServers = resp.config;
      }
    } catch (e) {
      console.error("Failed to load project MCP config:", e);
      this.selectedProject._mcpServers = '{\n    "mcpServers": {}\n}';
    }
  },

  async _loadGlobalServers() {
    try {
      const resp = await api.callJsonApi("project_mcp_servers", {
        action: "list_global",
      });
      if (resp.success) {
        this.mcpGlobalServers = resp.servers || {};
      }
    } catch (e) {
      console.error("Failed to load global MCP servers:", e);
      this.mcpGlobalServers = {};
    }
  },

  formatMcpJson() {
    if (!this.mcpEditor) return;
    try {
      const parsed = JSON.parse(this.mcpEditor.getValue());
      const formatted = JSON.stringify(parsed, null, 2);
      this.mcpEditor.setValue(formatted);
      this.mcpEditor.clearSelection();
    } catch (e) {
      alert("Invalid JSON: " + e.message);
    }
  },

  getMcpGlobalServerNames() {
    return Object.keys(this.mcpGlobalServers);
  },

  isMcpServerImported(serverName) {
    if (!this.mcpEditor) return false;
    try {
      const current = JSON.parse(this.mcpEditor.getValue());
      return !!(current.mcpServers && current.mcpServers[serverName]);
    } catch (e) {
      return false;
    }
  },

  toggleMcpServerImport(serverName) {
    if (!this.mcpEditor) return;
    try {
      const current = JSON.parse(this.mcpEditor.getValue());
      if (!current.mcpServers) current.mcpServers = {};

      if (current.mcpServers[serverName]) {
        delete current.mcpServers[serverName];
        delete this.mcpExpandedServers[serverName];
      } else if (this.mcpGlobalServers[serverName]) {
        current.mcpServers[serverName] = JSON.parse(
          JSON.stringify(this.mcpGlobalServers[serverName])
        );
      }

      const formatted = JSON.stringify(current, null, 2);
      this.mcpEditor.setValue(formatted);
      this.mcpEditor.clearSelection();
    } catch (e) {
      alert("Failed to toggle server: " + e.message);
    }
  },

  getProjectImportedServers() {
    if (!this.mcpEditor) return [];
    try {
      const current = JSON.parse(this.mcpEditor.getValue());
      return Object.keys(current.mcpServers || {});
    } catch (e) {
      return [];
    }
  },

  async toggleServerExpanded(serverName) {
    if (this.mcpExpandedServers[serverName]) {
      delete this.mcpExpandedServers[serverName];
      this.mcpExpandedServers = { ...this.mcpExpandedServers };
    } else {
      if (!this.mcpServerToolsCache[serverName]) {
        await this.fetchServerTools(serverName);
      }
      this.mcpExpandedServers[serverName] = true;
      this.mcpExpandedServers = { ...this.mcpExpandedServers };
    }
  },

  isServerExpanded(serverName) {
    return !!this.mcpExpandedServers[serverName];
  },

  async fetchServerTools(serverName, retries = 3) {
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const resp = await api.callJsonApi("mcp_server_get_detail", {
          server_name: serverName,
          project_name: this.selectedProject?.name || "",
        });
        if (resp.success && resp.detail) {
          const tools = resp.detail.tools || [];
          this.mcpServerToolsCache[serverName] = {
            tools: tools,
            description: resp.detail.description || "",
          };
          this.mcpServerToolsCache = { ...this.mcpServerToolsCache };
          if (tools.length > 0) return;
          if (attempt < retries - 1) {
            await new Promise(resolve => setTimeout(resolve, 1500));
          }
        }
      } catch (e) {
        console.error("Failed to fetch server tools:", e);
        if (attempt < retries - 1) {
          await new Promise(resolve => setTimeout(resolve, 1500));
        }
      }
    }
  },

  async applyProjectMcp() {
    if (!this.mcpEditor || !this.selectedProject) return;
    this.mcpApplying = true;
    try {
      const config = this.mcpEditor.getValue();
      const resp = await api.callJsonApi("project_mcp_servers", {
        action: "apply",
        project_name: this.selectedProject.name,
        config: config,
      });
      if (resp.success) {
        this.mcpServerStatus = resp.status || [];
        this.mcpServerToolsCache = {};
        await new Promise(resolve => setTimeout(resolve, 3000));
        const allServers = this.getProjectImportedServers();
        for (const serverName of allServers) {
          this.mcpExpandedServers[serverName] = true;
        }
        this.mcpExpandedServers = { ...this.mcpExpandedServers };
        for (const serverName of allServers) {
          await this.fetchServerTools(serverName);
        }
        notifications.toastFrontendSuccess(
          "MCP servers applied successfully",
          "MCP Applied",
          3,
          "mcp",
          notifications.NotificationPriority.NORMAL,
          true
        );
      } else {
        notifications.toastFrontendError(
          resp.error || "Failed to apply MCP servers",
          "MCP Error",
          5,
          "mcp",
          notifications.NotificationPriority.NORMAL,
          true
        );
      }
    } catch (e) {
      console.error("Failed to apply project MCP:", e);
      notifications.toastFrontendError(
        "Failed to apply MCP servers: " + e.message,
        "MCP Error",
        5,
        "mcp",
        notifications.NotificationPriority.NORMAL,
        true
      );
    } finally {
      this.mcpApplying = false;
    }
  },

  getServerTools(serverName) {
    return this.mcpServerToolsCache[serverName]?.tools || [];
  },

  getServerDescription(serverName) {
    return this.mcpServerToolsCache[serverName]?.description || "";
  },

  isProjectToolDisabled(serverName, toolName) {
    if (!this.mcpEditor) return false;
    try {
      const current = JSON.parse(this.mcpEditor.getValue());
      const server = current.mcpServers?.[serverName];
      if (!server || !server.disabled_tools) return false;
      return server.disabled_tools.includes(toolName);
    } catch (e) {
      return false;
    }
  },

  toggleProjectTool(serverName, toolName) {
    if (!this.mcpEditor) return;
    try {
      const current = JSON.parse(this.mcpEditor.getValue());
      if (!current.mcpServers?.[serverName]) return;

      const server = current.mcpServers[serverName];
      if (!server.disabled_tools) {
        server.disabled_tools = [];
      }

      const idx = server.disabled_tools.indexOf(toolName);
      if (idx >= 0) {
        server.disabled_tools.splice(idx, 1);
      } else {
        server.disabled_tools.push(toolName);
      }

      const formatted = JSON.stringify(current, null, 2);
      this.mcpEditor.setValue(formatted);
      this.mcpEditor.clearSelection();
    } catch (e) {
      alert("Failed to toggle tool: " + e.message);
    }
  },
};

// convert it to alpine store
const store = createStore("projects", model);

// export for use in other files
export { store };
