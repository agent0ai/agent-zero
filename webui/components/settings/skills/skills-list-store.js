import { createStore } from "/js/AlpineStore.js";
import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";

const fetchApi = globalThis.fetchApi;

const model = {
  loading: false,
  error: "",
  skills: [],
  projects: [],
  projectName: "",
  agentProfiles: [],
  agentProfileKey: "",

  async init() {
    this.resetState();
    await Promise.all([this.loadProjects(), this.loadAgentProfiles()]);
    await this.loadSkills();
  },

  resetState() {
    this.loading = false;
    this.error = "";
    this.skills = [];
    this.projects = [];
    this.projectName = "";
    this.agentProfiles = [];
    this.agentProfileKey = "";
  },

  onClose() {
    this.resetState();
  },

  async loadAgentProfiles() {
    try {
      const response = await fetchApi("/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "list" }),
      });
      const data = await response.json().catch(() => ({}));
      this.agentProfiles = data.ok ? (data.data || []) : [];
    } catch (e) {
      console.error("Failed to load agent profiles:", e);
      this.agentProfiles = [];
    }
  },

  async loadProjects() {
    try {
      const response = await fetchApi("/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "list_options" }),
      });
      const data = await response.json().catch(() => ({}));
      this.projects = data.ok ? (data.data || []) : [];
    } catch (e) {
      console.error("Failed to load projects:", e);
      this.projects = [];
    }
  },

  async loadSkills() {
    try {
      this.loading = true;
      this.error = "";
      const response = await fetchApi("/skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "list",
          project_name: this.projectName || null,
          agent_profile: this.agentProfileKey || null,
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!result.ok) {
        this.error = result.error || "Failed to load skills";
        this.skills = [];
        return;
      }
      this.skills = Array.isArray(result.data) ? result.data : [];
    } catch (e) {
      this.error = e?.message || "Failed to load skills";
      this.skills = [];
    } finally {
      this.loading = false;
    }
  },

  async deleteSkill(skill) {
    if (!skill) return;
    try {
      const response = await fetchApi("/skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "delete",
          skill_path: skill.path,
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!result.ok) {
        throw new Error(result.error || "Delete failed");
      }
      if (window.toastFrontendSuccess) {
        window.toastFrontendSuccess("Skill deleted", "Skills");
      }
      await this.loadSkills();
    } catch (e) {
      const msg = e?.message || "Delete failed";
      if (window.toastFrontendError) {
        window.toastFrontendError(msg, "Skills");
      }
    }
  },

  async openSkill(skill) {
    await fileBrowserStore.open(skill.path);
  },
};

const store = createStore("skillsListStore", model);
export { store };
