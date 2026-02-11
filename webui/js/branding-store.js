import { createStore } from "/js/AlpineStore.js";

const model = {
  name: "Apollos AI",
  slug: "apollos-ai",
  url: "https://matherly.net",
  github_url: "https://github.com/jrmatherly/apollos-ai",
  _initialized: false,

  async init() {
    if (this._initialized) return;
    this._initialized = true;
    try {
      const response = await fetch("/branding_get");
      if (response.ok) {
        const data = await response.json();
        this.name = data.name || this.name;
        this.slug = data.slug || this.slug;
        this.url = data.url || this.url;
        this.github_url = data.github_url || this.github_url;
        document.title = data.name || "Apollos AI";
      }
    } catch (e) {
      console.warn("Failed to load branding config, using defaults:", e);
    }
  },
};

export const store = createStore("branding", model);
