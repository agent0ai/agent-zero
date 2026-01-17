import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getCurrentContextId } from "/js/shortcuts.js";
import "/components/modals/file-browser/file-browser-store.js";

const model = {
  isLoading: false,
  isSaving: false,
  error: null,
  allowedPaths: [],
  approvals: [],
  contextId: "",

  async onOpen() {
    this.contextId = getCurrentContextId() || "";
    await this.refresh();
  },

  async refresh() {
    this.error = null;
    this.isLoading = true;
    try {
      const folders = await callJsonApi("/cowork_folders_get", {});
      this.allowedPaths = Array.isArray(folders.paths) ? folders.paths : [];
      await this.refreshApprovals();
    } catch (err) {
      console.error(err);
      this.error = err?.message || "Failed to load Cowork settings.";
    } finally {
      this.isLoading = false;
    }
  },

  async refreshApprovals() {
    if (!this.contextId) {
      this.approvals = [];
      return;
    }
    const resp = await callJsonApi("/cowork_approvals_list", {
      context: this.contextId,
    });
    this.approvals = (resp.approvals || []).map((approval) => ({
      inherit: approval.inherit !== false,
      ...approval,
    }));
  },

  async addFolder() {
    try {
      const selected = await window.openFolderPicker("/a0");
      if (!selected) return;
      const normalized = selected.replace(/\/+$/, "");
      if (!this.allowedPaths.includes(normalized)) {
        this.allowedPaths.push(normalized);
        await this.saveFolders();
      }
    } catch (err) {
      window.toastFrontendError(err?.message || "Failed to add folder.");
    }
  },

  async removeFolder(path) {
    this.allowedPaths = this.allowedPaths.filter((p) => p !== path);
    await this.saveFolders();
  },

  async saveFolders() {
    this.isSaving = true;
    try {
      await callJsonApi("/cowork_folders_set", { paths: this.allowedPaths });
    } catch (err) {
      window.toastFrontendError(err?.message || "Failed to save folders.");
    } finally {
      this.isSaving = false;
    }
  },

  get pendingApprovals() {
    return this.approvals.filter((a) => a.status === "pending");
  },

  get resolvedApprovals() {
    return this.approvals.filter((a) => a.status !== "pending");
  },

  async actOnApproval(approvalId, action, inherit = true) {
    if (!approvalId) return;
    await callJsonApi("/cowork_approvals_update", {
      context: this.contextId,
      approval_id: approvalId,
      action,
      inherit,
    });
    if (this.contextId) {
      try {
        await callJsonApi("/nudge", { ctxid: this.contextId });
      } catch (err) {
        console.warn("Failed to nudge agent:", err);
      }
    }
    await this.refreshApprovals();
  },

  async clearResolved() {
    await callJsonApi("/cowork_approvals_update", {
      context: this.contextId,
      action: "clear_resolved",
    });
    await this.refreshApprovals();
  },
};

export const store = createStore("coworkManager", model);
