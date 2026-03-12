import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";

const model = {
  loading: false,
  error: "",
  source: "",
  result: null,

  async install() {
    const source = this.source.trim();
    if (!source) return;

    this.loading = true;
    this.error = "";
    this.result = null;

    try {
      const ctxid = globalThis.getContext ? globalThis.getContext() : "";
      const result = await api.callJsonApi("/skill_install", {
        source,
        ctxid,
      });

      if (result.ok) {
        this.result = result;
        this.source = "";
      } else {
        this.error = result.error || "Install failed";
      }
    } catch (e) {
      this.error = `Install error: ${e.message}`;
    } finally {
      this.loading = false;
    }
  },
};

const store = createStore("skillsInstallStore", model);
export { store };
