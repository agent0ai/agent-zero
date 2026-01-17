import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";

const model = {
  loading: false,
  error: "",
  data: null,

  async load() {
    this.loading = true;
    this.error = "";
    try {
      const resp = await API.callJsonApi("prompt_enhance_get", {});
      this.data = resp.data || null;
    } catch (err) {
      this.error = err?.message || "Failed to load prompt enhancement details.";
      this.data = null;
    } finally {
      this.loading = false;
    }
  },
};

const store = createStore("promptEnhanceStore", model);

export { store };
