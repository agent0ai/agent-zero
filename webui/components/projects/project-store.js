import { createStore } from "/js/AlpineStore.js";
import {
  NotificationType,
  NotificationPriority,
} from "/components/notifications/notification-store.js";

/**
 * Project Store for Agent Zero Project Management System
 * Provides centralized state management for project operations
 * Interfaces with Flask API endpoints (/projects)
 */

const model = {
  // State properties
  projects: [],
  activeProject: null,
  loading: false,
  error: null,
  lastFetchTime: null,

  // Operation states
  creating: false,
  updating: false,
  deleting: false,
  activating: false,

  // Event listeners
  listeners: new Map(),

  // Detail form data
  detailForm: {
    name: "",
    description: "",
    instructions: "",
  },

  // Validation errors
  validationErrors: [],

  // Modal state management
  showDetailModal: false,
  detailMode: "view", // 'view', 'edit', 'create'
  selectedProject: null,
  isDetailLoading: false,
  detailLoadingText: "",
  detailError: null,

  init() {
    this.initialize();
  },

  // Initialize the project store
  initialize() {
    this.loading = false;
    this.error = null;
    this.projects = [];
    this.activeProject = null;
    this.lastFetchTime = null;

    // Reset operation states
    this.creating = false;
    this.updating = false;
    this.deleting = false;
    this.activating = false;

    // Reset form data
    this.detailForm = {
      name: "",
      description: "",
      instructions: "",
    };

    // Reset validation errors
    this.validationErrors = [];

    // Load projects on initialization
    this.loadProjects();
  },

  // Event system for component communication
  addEventListener(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  },

  removeEventListener(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  },

  emit(event, data = null) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(
            `Error in project store event listener for '${event}':`,
            error,
          );
        }
      });
    }
  },

  // Toast Notification Methods
  showToast(type, message, title = "", displayTime = 5, group = "project") {
    try {
      // Use the global notification system
      if (globalThis.$store?.notificationStore) {
        globalThis.$store.notificationStore.addFrontendToast(
          type,
          message,
          title,
          displayTime,
          group,
          NotificationPriority.NORMAL,
        );
      } else if (globalThis.toastFrontendInfo) {
        // Fallback to global toast functions
        switch (type) {
          case NotificationType.SUCCESS:
            globalThis.toastFrontendSuccess(message, title, displayTime, group);
            break;
          case NotificationType.ERROR:
            globalThis.toastFrontendError(message, title, displayTime, group);
            break;
          case NotificationType.WARNING:
            globalThis.toastFrontendWarning(message, title, displayTime, group);
            break;
          default:
            globalThis.toastFrontendInfo(message, title, displayTime, group);
        }
      }
    } catch (error) {
      console.error("Failed to show toast notification:", error);
    }
  },

  showSuccessToast(message, title = "Project Success") {
    this.showToast(NotificationType.SUCCESS, message, title, 3);
  },

  showErrorToast(message, title = "Project Error") {
    this.showToast(NotificationType.ERROR, message, title, 5);
  },

  showInfoToast(message, title = "Project Info") {
    this.showToast(NotificationType.INFO, message, title, 4);
  },

  // API Methods

  // Load all projects from the API
  async loadProjects() {
    if (this.loading) return;

    this.loading = true;
    this.error = null;

    try {
      const response = await globalThis.sendJsonData("/projects", null, "GET");

      if (response.success) {
        this.projects = response.projects || [];
        this.activeProject = this.projects.find((p) => p.active) || null;
        this.lastFetchTime = Date.now();
        this.emit("projectsLoaded", {
          projects: this.projects,
          activeProject: this.activeProject,
        });
      } else {
        this.error = response.error || "Failed to load projects";
        this.emit("error", this.error);
      }
    } catch (error) {
      this.error = `Network error: ${error.message}`;
      this.emit("error", this.error);
      console.error("Error loading projects:", error);
    } finally {
      this.loading = false;
    }
  },

  // Get a specific project by ID
  async getProject(projectId) {
    if (!projectId) {
      throw new Error("Project ID is required");
    }

    try {
      const response = await globalThis.sendJsonData(
        `/projects?id=${encodeURIComponent(projectId)}`,
        null,
        "GET",
      );

      if (response.success) {
        return response.project;
      } else {
        throw new Error(response.error || "Failed to get project");
      }
    } catch (error) {
      console.error("Error getting project:", error);
      throw error;
    }
  },

  // Create a new project
  async createProject(projectData) {
    if (this.creating) return null;

    this.creating = true;
    this.error = null;

    try {
      const { name, description, instructions } = projectData;

      if (!name) {
        throw new Error("Project name is required");
      }

      if (!description) {
        throw new Error("Project description is required");
      }

      const response = await globalThis.sendJsonData(
        "/projects",
        {
          name: name.trim(),
          description: description.trim(),
          instructions: instructions ? instructions.trim() : "",
        },
        "POST",
      );

      if (response.success && response.project) {
        const newProject = response.project;
        this.projects.unshift(newProject); // Add to beginning of list
        this.emit("projectCreated", newProject);

        // Show success notification
        this.showSuccessToast(
          `Project "${newProject.name}" created successfully`,
          "Project Created",
        );

        return newProject;
      } else {
        const errorMsg = response.error || "Failed to create project";
        this.error = errorMsg;
        this.emit("error", this.error);
        this.showErrorToast(errorMsg, "Create Failed");
        throw new Error(errorMsg);
      }
    } catch (error) {
      this.error = error.message;
      this.emit("error", this.error);
      this.showErrorToast(error.message, "Create Failed");
      console.error("Error creating project:", error);
      throw error;
    } finally {
      this.creating = false;
    }
  },

  // Update an existing project
  async updateProject(projectId, updateData) {
    if (this.updating) return null;

    this.updating = true;
    this.error = null;

    try {
      if (!projectId) {
        throw new Error("Project ID is required");
      }

      const response = await globalThis.sendJsonData(
        "/projects",
        {
          id: projectId,
          ...updateData,
        },
        "PUT",
      );

      if (response.success) {
        const updatedProject = response.project;

        // Update project in the list
        const index = this.projects.findIndex((p) => p.id === projectId);
        if (index >= 0) {
          this.projects[index] = updatedProject;
        }

        // Update active project if it's the one being updated
        if (this.activeProject && this.activeProject.id === projectId) {
          this.activeProject = updatedProject;
        }

        this.emit("projectUpdated", updatedProject);
        return updatedProject;
      } else {
        this.error = response.error || "Failed to update project";
        this.emit("error", this.error);
        throw new Error(this.error);
      }
    } catch (error) {
      this.error = error.message;
      this.emit("error", this.error);
      console.error("Error updating project:", error);
      throw error;
    } finally {
      this.updating = false;
    }
  },

  // Delete a project
  async deleteProject(projectId) {
    if (this.deleting) return false;

    this.deleting = true;
    this.error = null;

    try {
      if (!projectId) {
        throw new Error("Project ID is required");
      }

      const response = await globalThis.sendJsonData(
        "/projects",
        {
          id: projectId,
        },
        "DELETE",
      );

      if (response.success) {
        // Remove project from the list
        const index = this.projects.findIndex((p) => p.id === projectId);
        if (index >= 0) {
          const deletedProject = this.projects[index];
          this.projects.splice(index, 1);

          // Clear active project if it was deleted
          if (this.activeProject && this.activeProject.id === projectId) {
            this.activeProject = null;
          }

          this.emit("projectDeleted", deletedProject);
        }

        return true;
      } else {
        this.error = response.error || "Failed to delete project";
        this.emit("error", this.error);
        throw new Error(this.error);
      }
    } catch (error) {
      this.error = error.message;
      this.emit("error", this.error);
      console.error("Error deleting project:", error);
      throw error;
    } finally {
      this.deleting = false;
    }
  },

  // Activate a project (deactivates all others)
  async activateProject(projectId) {
    if (this.activating) return null;

    this.activating = true;
    this.error = null;

    try {
      if (!projectId) {
        throw new Error("Project ID is required");
      }

      const response = await globalThis.sendJsonData(
        "/projects",
        {
          id: projectId,
          action: "activate",
        },
        "POST",
      );

      if (response.success) {
        const activatedProject = response.project;

        // Update all projects: deactivate others, activate target
        this.projects.forEach((project) => {
          project.active = project.id === projectId;
        });

        // Update the specific project with latest data from server
        const index = this.projects.findIndex((p) => p.id === projectId);
        if (index >= 0) {
          this.projects[index] = activatedProject;
        }

        this.activeProject = activatedProject;
        this.emit("projectActivated", activatedProject);

        // Show success notification for project activation
        this.showSuccessToast(
          `Project "${activatedProject.name}" is now active`,
          "Project Activated",
        );

        // Trigger immediate chat update to show system message
        if (window.poll) {
          window.poll();
        }

        return activatedProject;
      } else {
        this.error = response.error || "Failed to activate project";
        this.emit("error", this.error);
        this.showErrorToast(this.error, "Activation Failed");
        throw new Error(this.error);
      }
    } catch (error) {
      this.error = error.message;
      this.emit("error", this.error);
      this.showErrorToast(error.message, "Activation Failed");
      console.error("Error activating project:", error);
      throw error;
    } finally {
      this.activating = false;
    }
  },

  async deactivateProject() {
    if (this.activating) return null;

    this.activating = true;
    this.error = null;

    try {
      const response = await globalThis.sendJsonData(
        "/projects",
        {
          action: "deactivate",
        },
        "POST",
      );

      if (response.success) {
        // Clear active project from all projects
        this.projects.forEach((project) => {
          project.active = false;
        });

        // Clear active project reference
        this.activeProject = null;
        this.emit("projectDeactivated", response.previous_active);

        // Show success notification
        this.showSuccessToast(
          "All projects have been deactivated",
          "Projects Deactivated",
        );

        // Trigger immediate chat update to show system message
        if (window.poll) {
          window.poll();
        }

        return true;
      } else {
        this.error = response.error || "Failed to deactivate projects";
        this.emit("error", this.error);
        this.showErrorToast(this.error, "Deactivation Failed");
        throw new Error(this.error);
      }
    } catch (error) {
      this.error = error.message;
      this.emit("error", this.error);
      this.showErrorToast(error.message, "Deactivation Failed");
      console.error("Error deactivating projects:", error);
      throw error;
    } finally {
      this.activating = false;
    }
  },

  // Utility Methods

  // Get project by ID from local state
  getProjectById(projectId) {
    return this.projects.find((p) => p.id === projectId) || null;
  },

  // Get all projects sorted by creation date (newest first)
  getAllProjects() {
    return [...this.projects].sort((a, b) => {
      const dateA = new Date(a.created_at || 0);
      const dateB = new Date(b.created_at || 0);
      return dateB - dateA;
    });
  },

  // Get active project
  getActiveProject() {
    return this.activeProject;
  },

  // Check if a project is active
  isProjectActive(projectId) {
    return this.activeProject && this.activeProject.id === projectId;
  },

  // Get projects count
  getProjectsCount() {
    return this.projects.length;
  },

  // Validate project data
  validateProjectData(projectData) {
    const errors = [];

    if (!projectData.name || projectData.name.trim() === "") {
      errors.push("Project name is required");
    }

    if (!projectData.description || projectData.description.trim() === "") {
      errors.push("Project description is required");
    }

    if (projectData.name && projectData.name.length > 100) {
      errors.push("Project name must be 100 characters or less");
    }

    if (projectData.description && projectData.description.length > 500) {
      errors.push("Project description must be 500 characters or less");
    }

    return errors;
  },

  // Format timestamp for display
  formatTimestamp(timestamp) {
    if (!timestamp) return "Unknown";

    try {
      const date = new Date(timestamp);

      // Check if the date is valid
      if (isNaN(date.getTime())) {
        return timestamp; // Return original if it's already formatted
      }

      const now = new Date();
      const diffMs = now - date;
      const diffMins = diffMs / 60000;
      const diffHours = diffMs / 3600000;
      const diffDays = diffMs / 86400000;

      if (diffMins < 1) return "Just now";
      else if (diffMins < 60) return `${Math.round(diffMins)}m ago`;
      else if (diffHours < 24) return `${Math.round(diffHours)}h ago`;
      else if (diffDays < 7) return `${Math.round(diffDays)}d ago`;
      else return date.toLocaleDateString();
    } catch (error) {
      console.warn("Error formatting timestamp:", timestamp, error);
      return String(timestamp);
    }
  },

  // Alias for formatTimestamp (for compatibility)
  formatDate(timestamp) {
    return this.formatTimestamp(timestamp);
  },

  // Clear error state
  clearError() {
    this.error = null;
  },

  // Refresh projects (force reload)
  async refreshProjects() {
    this.lastFetchTime = null;
    await this.loadProjects();
  },

  // Check if store is in any loading state
  isLoading() {
    return (
      this.loading ||
      this.creating ||
      this.updating ||
      this.deleting ||
      this.activating
    );
  },

  // Get loading state details
  getLoadingState() {
    return {
      loading: this.loading,
      creating: this.creating,
      updating: this.updating,
      deleting: this.deleting,
      activating: this.activating,
    };
  },

  // Modal control methods
  closeDetailModal() {
    this.showDetailModal = false;
    this.selectedProject = null;
    this.detailMode = "view";
    this.isDetailLoading = false;
    this.detailLoadingText = "";
    this.detailError = null;
    // Reset form data
    this.detailForm = {
      name: "",
      description: "",
      instructions: "",
    };
    this.validationErrors = [];
  },

  openDetailModal(mode = "view", project = null) {
    this.detailMode = mode;
    this.selectedProject = project;
    if (project) {
      this.detailForm = {
        name: project.name || "",
        description: project.description || "",
        instructions: project.instructions || "",
      };
    } else if (mode === "create") {
      // Reset form for create mode
      this.detailForm = {
        name: "",
        description: "",
        path: "",
        instructions: "",
      };
    }
    this.showDetailModal = true;
    this.validationErrors = [];
  },

  handleDetailEscapeKey(event) {
    if (event.key === "Escape") {
      this.closeDetailModal();
    }
  },

  // Additional modal methods that the template requires
  cancelDetailForm() {
    this.closeDetailModal();
  },

  switchToEditMode() {
    if (this.selectedProject) {
      this.detailMode = "edit";
    }
  },

  async activateProjectFromDetail() {
    if (this.selectedProject) {
      try {
        await this.activateProject(this.selectedProject.id);
        // Modal stays open to show updated status
      } catch (error) {
        this.showErrorToast(error.message, "Activation Failed");
      }
    }
  },

  async deactivateProjectFromDetail() {
    if (this.selectedProject && this.selectedProject.active) {
      try {
        await this.deactivateProject();
        this.closeDetailModal();
      } catch (error) {
        this.showErrorToast(error.message, "Deactivation Failed");
      }
    }
  },

  // Form submission for create/edit
  async submitDetailForm() {
    this.validationErrors = [];

    // Basic validation
    const errors = this.validateProjectData({
      name: this.detailForm.name,
      description: this.detailForm.description,
    });

    if (errors.length > 0) {
      this.validationErrors = errors;
      return;
    }

    try {
      if (this.detailMode === "create") {
        await this.createProject({
          name: this.detailForm.name,
          description: this.detailForm.description,
          instructions: this.detailForm.instructions,
        });
        this.closeDetailModal();
      } else if (this.detailMode === "edit" && this.selectedProject) {
        await this.updateProject(this.selectedProject.id, {
          name: this.detailForm.name,
          description: this.detailForm.description,
          instructions: this.detailForm.instructions,
        });
        this.closeDetailModal();
      }
    } catch (error) {
      this.validationErrors = [error.message];
    }
  },
};

// Create and export the store
const store = createStore("projectStore", model);
export { store };

// Export convenience methods for global access
globalThis.projectStore = store;
