import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

export const store = createStore("teamAdmin", {
  accounts: [],
  projects: [],
  busy: false,
  error: "",

  async refresh() {
    return this._run();
  },

  async create(form) {
    const values = new FormData(form);
    const ok = await this._run({
      action: "create",
      username: values.get("username"),
      password: values.get("password"),
    });
    if (ok) form.reset();
    else form.elements.password.value = "";
  },

  async resetPassword(account, form) {
    const password = new FormData(form).get("password");
    await this._run({ action: "reset_password", account_id: account.id, password });
    form.reset();
  },

  setEnabled(account, enabled) {
    return this._run({ action: "set_enabled", account_id: account.id, enabled });
  },

  async setMembership(account, project, checkbox) {
    const granted = checkbox.checked;
    const ok = await this._run({ action: "set_membership", account_id: account.id, project, granted });
    if (!ok) checkbox.checked = account.projects.includes(project);
  },

  async _run(change = null) {
    if (this.busy) return false;
    this.busy = true;
    this.error = "";
    try {
      if (change) await callJsonApi("team_admin", change);
      const response = await callJsonApi("team_admin", { action: "list" });
      this.accounts = response.accounts;
      this.projects = response.projects;
      return true;
    } catch (error) {
      this.error = error.message || "Could not update team accounts.";
      return false;
    } finally {
      this.busy = false;
    }
  },
});
