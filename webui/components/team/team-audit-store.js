import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const endpoint = "team_audit";
const blankFilters = () => ({ project_id: "", context_id: "", account_id: "", action: "", from: "", until: "" });
const labels = { admin: "Administrator", system: "System" };

export const store = createStore("teamAudit", {
  admin: false,
  projects: [],
  accounts: [],
  grants: [],
  events: [],
  cursor: null,
  transcript: null,
  context: "",
  filters: blankFilters(),
  busy: false,
  error: "",
  active: false,

  initView() {
    this.active = true;
    this.filters = blankFilters();
    this.context = "";
    this.error = "";
    return this.run(async () => {
      await this.loadOptions();
      if (this.admin || this.projects.length) await this.loadEvents();
    });
  },

  close() {
    this.active = false;
    this.transcript = null;
    this.context = "";
    this.events = [];
    this.cursor = null;
    this.grants = [];
  },

  async loadOptions() {
    const result = await callJsonApi(endpoint, { action: "options" });
    if (!this.active) return;
    this.admin = result.admin;
    this.projects = result.projects;
    this.accounts = result.accounts;
    this.grants = result.grants;
  },

  async loadEvents(before) {
    const filters = {};
    for (const [key, value] of Object.entries(this.filters)) {
      if (!value.trim()) continue;
      filters[key] = key === "from" || key === "until" ? Math.floor(new Date(value).getTime() / 1000) : value.trim();
    }
    if (before) filters.before_id = before;
    const result = await callJsonApi(endpoint, { action: "events", filters });
    if (!this.active) return;
    this.events = before ? [...this.events, ...result.events] : result.events;
    this.cursor = result.before_id;
  },

  search() {
    return this.run(() => this.loadEvents());
  },

  more() {
    return this.run(() => this.loadEvents(this.cursor));
  },

  grant(form) {
    const payload = Object.fromEntries(new FormData(form));
    return this.run(async () => {
      await callJsonApi(endpoint, { action: "grant", ...payload });
      this.transcript = null;
      await this.loadOptions();
      await this.loadEvents();
    });
  },

  showTranscript(context = this.context, before = null) {
    return this.run(async () => {
      this.context = context;
      const previous = before ? this.transcript : null;
      this.transcript = null;
      const payload = { action: "transcript", context: context.trim() };
      if (before !== null) payload.before_no = before;
      const result = await callJsonApi(endpoint, payload);
      if (!this.active) return;
      this.transcript = previous ? { ...result, messages: [...result.messages, ...previous.messages] } : result;
    });
  },

  actor(id, name) {
    return name || labels[id] || id;
  },

  async run(action) {
    if (this.busy) return;
    this.busy = true;
    this.error = "";
    try {
      await action();
    } catch (error) {
      if (this.active) this.error = error.message || "The audit request failed.";
    } finally {
      this.busy = false;
    }
  },
});
