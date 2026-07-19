import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

function buildBannersContext() {
  return {
    url: window.location.href,
    protocol: window.location.protocol,
    hostname: window.location.hostname,
    port: window.location.port,
    browser: navigator.userAgent,
    timestamp: new Date().toISOString(),
  };
}

export const store = createStore("composerBanner", {
  missingApiKeys: [],
  hasMissingApiKeyBanner: false,
  loading: false,
  lastRefresh: 0,
  _modalCloseBound: false,

  get hasMissingApiKeys() {
    return this.hasMissingApiKeyBanner;
  },

  get missingApiKeysSummaryText() {
    if (!this.hasMissingApiKeys) return "";
    if (!Array.isArray(this.missingApiKeys) || this.missingApiKeys.length === 0) {
      return "Configure your model provider API keys to continue.";
    }
    return this.missingApiKeys
      .map((p) => `${p.model_type} (${p.provider})`)
      .join(", ");
  },

  init() {
    if (this._modalCloseBound) return;
    this._modalCloseBound = true;
    document.addEventListener("modal-closed", () => {
      this.refresh(true);
    });
  },

  async refresh(force = false) {
    const now = Date.now();
    if (!force && now - this.lastRefresh < 1000) return;
    this.lastRefresh = now;
    this.loading = true;
    try {
      const response = await callJsonApi("/banners", {
        banners: [],
        context: buildBannersContext(),
      });
      const banners = Array.isArray(response?.banners) ? response.banners : [];
      const missingApiKeyBanner = banners.find((banner) => banner?.id === "missing-api-key");
      this.hasMissingApiKeyBanner = !!missingApiKeyBanner;
      this.missingApiKeys = Array.isArray(missingApiKeyBanner?.missing_providers)
        ? missingApiKeyBanner.missing_providers
        : [];
    } catch (e) {
      console.error("composerBanner refresh failed", e);
      this.hasMissingApiKeyBanner = false;
      this.missingApiKeys = [];
    } finally {
      this.loading = false;
    }
  },
});
