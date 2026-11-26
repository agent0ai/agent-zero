import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { projectLocation, projectRoot } from "/js/team-project-files.js";

export const store = createStore("projectSurfaces", {
  sessions: {},
  errors: {},
  loading: {},
  requests: {},

  async open(mode, path = "") {
    const request = (this.requests[mode] || 0) + 1;
    this.requests[mode] = request;
    this.errors[mode] = "";
    if (!path && !projectRoot()) {
      this.sessions[mode] = null;
      this.loading[mode] = false;
      this.errors[mode] = "Select a project first.";
      return;
    }
    this.loading[mode] = true;
    try {
      const location = projectLocation(path);
      if (this.sessions[mode]?.project !== location.project) this.sessions[mode] = null;
      const response = await callJsonApi("team_surface", { action: "open", mode, ...location });
      if (this.requests[mode] !== request) return;
      this.sessions[mode] = { ...location, url: response.url };
    } catch (error) {
      if (this.requests[mode] !== request) return;
      this.sessions[mode] = null;
      this.errors[mode] = error.message;
    } finally {
      if (this.requests[mode] === request) this.loading[mode] = false;
    }
  },

  async save(mode) {
    const session = this.sessions[mode];
    if (!session?.path || this.loading[mode]) return;
    try {
      await callJsonApi("team_surface", { action: "save", mode, project: session.project, path: session.path });
      this.errors[mode] = "";
      globalThis.toastFrontendSuccess?.("Saved to the project", "Desktop");
    } catch (error) {
      this.errors[mode] = error.message;
    }
  },
});
