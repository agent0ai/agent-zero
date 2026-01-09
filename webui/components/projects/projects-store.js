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

      // call backend
      const response = await api.callJsonApi("projects", {
        action: creating ? "create" : "update",
        project: data,
      });
      // notifications
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
};

// convert it to alpine store
const store = createStore("projects", model);

// export for use in other files
export { store };
