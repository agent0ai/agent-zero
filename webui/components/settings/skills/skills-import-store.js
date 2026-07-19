import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";

function sanitizeNamespace(text) {
  if (!text) return "";
  return String(text)
    .trim()
    .replace(/[^a-zA-Z0-9._-]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

const model = {
  loading: false,
  loadingMessage: "",
  error: "",

  skillsFile: null,
  namespace: "",
  conflict: "skip", // skip|overwrite|rename
  projectKey: "", // selected project key, empty means All
  agentProfileKey: "", // selected agent profile key, empty means All
  projects: [], // available projects options [{key,label}]
  agentProfiles: [], // available agent profile options [{key,label}]

  preview: null,
  result: null,

  init() {
    this.resetState();
    this.loadProjects();
    this.loadAgentProfiles();
  },

  resetState() {
    this.loading = false;
    this.loadingMessage = "";
    this.error = "";
    this.preview = null;
    this.result = null;
  },

  onClose() {
    this.resetState();
    this.skillsFile = null;
    this.namespace = "";
    this.conflict = "skip";
    this.projectKey = "";
    this.agentProfileKey = "";
  },

  async loadProjects() {
    try {
      const data = await api.callJsonApi("/projects", { action: "list_options" });
      this.projects = data.ok ? (data.data || []) : [];
    } catch (e) {
      console.error("Failed to load projects:", e);
      this.projects = [];
    }
  },

  async loadAgentProfiles() {
    try {
      const data = await api.callJsonApi("/agents", { action: "list" });
      this.agentProfiles = data.ok ? (data.data || []) : [];
    } catch (e) {
      console.error("Failed to load agent profiles:", e);
      this.agentProfiles = [];
    }
  },

  async handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    this.skillsFile = file;
    this.error = "";
    this.result = null;
    this.preview = null;

    // default namespace from file name (minus .zip)
    const base = file.name.replace(/\.zip$/i, "");
    if (!this.namespace) {
      this.namespace = sanitizeNamespace(base);
    } else {
      this.namespace = sanitizeNamespace(this.namespace);
    }

    await this.previewImport();
  },

  buildFormData() {
    const formData = new FormData();
    formData.append("skills_file", this.skillsFile);
    formData.append("ctxid", globalThis.getContext ? globalThis.getContext() : "");
    formData.append("namespace", sanitizeNamespace(this.namespace));
    formData.append("conflict", this.conflict);

    if (this.projectKey) {
      formData.append("project_name", this.projectKey);
    }

    if (this.agentProfileKey) {
      formData.append("agent_profile", this.agentProfileKey);
    }
    return formData;
  },

  async previewImport() {
    if (!this.skillsFile) {
      this.error = "Please select a skills .zip file first";
      return;
    }

    try {
      this.loading = true;
      this.loadingMessage = "Previewing skills import...";
      this.error = "";
      this.preview = null;

      const response = await api.fetchApi("/skills_import_preview", {
        method: "POST",
        body: this.buildFormData(),
      });

      const result = await response.json();
      if (!result.success) {
        this.error = result.error || "Preview failed";
        return;
      }

      this.preview = result;
      // normalize namespace (server may sanitize)
      if (result.namespace) this.namespace = result.namespace;
    } catch (e) {
      this.error = `Preview error: ${e.message}`;
    } finally {
      this.loading = false;
      this.loadingMessage = "";
    }
  },

  async performImport() {
    if (!this.skillsFile) {
      this.error = "Please select a skills .zip file first";
      return;
    }

    try {
      this.loading = true;
      this.loadingMessage = "Importing skills...";
      this.error = "";
      this.result = null;

      const response = await api.fetchApi("/skills_import", {
        method: "POST",
        body: this.buildFormData(),
      });

      const result = await response.json();
      if (!result.success) {
        this.error = result.error || "Import failed";
        return;
      }

      this.result = result;
      this.preview = result; // keep last info visible
      if (window.toastFrontendInfo) {
        window.toastFrontendInfo(
          `Imported ${result.imported_count} skill folder(s)`,
          "Skills Import"
        );
      }
    } catch (e) {
      this.error = `Import error: ${e.message}`;
    } finally {
      this.loading = false;
      this.loadingMessage = "";
    }
  },
};

const store = createStore("skillsImportStore", model);
export { store };

