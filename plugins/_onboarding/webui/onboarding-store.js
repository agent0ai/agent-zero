import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, fetchApi } from "/js/api.js";
import { store as modelConfigStore } from "/plugins/_model_config/webui/model-config-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import {
  LOCAL_PROVIDER_IDS,
  MORE_CLOUD_PROVIDER_IDS,
  ONBOARDING_PROVIDER_OVERRIDES,
  TOP_CLOUD_PROVIDER_IDS,
} from "/plugins/_onboarding/webui/onboarding-providers.js";

const MODEL_CONFIG_API = "/plugins/_model_config";
const OAUTH_STATUS_API = "/plugins/_oauth/status";
const OAUTH_START_API = "/plugins/_oauth/start_device_login";
const OAUTH_POLL_API = "/plugins/_oauth/poll_device_login";
const OAUTH_MODELS_API = "/plugins/_oauth/models";
const MAX_OAUTH_POLL_MS = 120000;

const TOP_CLOUD_IDS = TOP_CLOUD_PROVIDER_IDS;
const MORE_CLOUD_IDS = MORE_CLOUD_PROVIDER_IDS;

const FALLBACKS = {
  codex_oauth: {
    id: "codex_oauth",
    name: "ChatGPT/Codex Account",
    logo: "https://openai.com/favicon.ico",
    onboarding_category: "account",
    api_key_mode: "oauth",
    short_description: "Use your connected ChatGPT or Codex account.",
    setup_url: "https://chatgpt.com/",
    docs_url: "https://platform.openai.com/docs/codex",
  },
  other: {
    id: "other",
    name: "Other OpenAI-compatible",
    logo: "/public/darkSymbol.svg",
    api_key_mode: "optional",
    short_description: "Use a compatible endpoint you control.",
  },
};

function clone(value) {
  return JSON.parse(JSON.stringify(value || {}));
}

function detailsById(details = []) {
  const result = {};
  for (const item of details || []) {
    const id = String(item?.id || item?.value || "").trim();
    if (id) result[id] = item;
  }
  return result;
}

function ensureSlot(config, key) {
  if (!config[key] || typeof config[key] !== "object") config[key] = {};
  config[key] = {
    provider: "",
    name: "",
    api_base: "",
    api_key: "",
    ctx_length: key === "utility_model" ? 128000 : 200000,
    ctx_history: key === "chat_model" ? 0.7 : undefined,
    ctx_input: key === "utility_model" ? 0.7 : undefined,
    vision: key === "chat_model" ? true : undefined,
    rl_requests: 0,
    rl_input: 0,
    rl_output: 0,
    kwargs: {},
    ...config[key],
  };
}

function normalizeUrl(value) {
  return String(value || "").trim();
}

function safeProviderName(provider) {
  return provider?.name || provider?.label || provider?.id || "Provider";
}

export const store = createStore("onboarding", {
  step: "path",
  pathChoice: "",
  loading: true,
  saving: false,
  config: null,
  providerDetails: {},
  selectedProviderId: "",
  selectedProviderOrigin: "cloud",
  moreProviderQuery: "",
  moreCloudOpen: false,
  sameAsMain: true,
  userTouchedModel: {
    chat_model: false,
    utility_model: false,
  },
  modelDropdown: {
    chat_model: { models: [], open: false, loading: false, error: "", source: "" },
    utility_model: { models: [], open: false, loading: false, error: "", source: "" },
  },
  oauthStatus: null,
  oauthLoading: false,
  oauthConnecting: false,
  oauthDevice: null,
  oauthPollTimer: null,
  oauthPollStartedAt: 0,
  oauthModels: [],

  steps: [
    { step: "path", label: "Choose path" },
    { step: "setup", label: "Connect" },
    { step: "utility", label: "Utility" },
    { step: "ready", label: "Ready" },
  ],

  async init() {
    this.resetState();
  },

  resetState() {
    this.step = "path";
    this.pathChoice = "";
    this.loading = true;
    this.saving = false;
    this.config = null;
    this.providerDetails = {};
    this.selectedProviderId = "";
    this.selectedProviderOrigin = "cloud";
    this.moreProviderQuery = "";
    this.moreCloudOpen = false;
    this.sameAsMain = true;
    this.userTouchedModel = { chat_model: false, utility_model: false };
    this.modelDropdown = {
      chat_model: { models: [], open: false, loading: false, error: "", source: "" },
      utility_model: { models: [], open: false, loading: false, error: "", source: "" },
    };
    this.oauthStatus = null;
    this.oauthLoading = false;
    this.oauthConnecting = false;
    this.oauthDevice = null;
    this.oauthModels = [];
    this.stopOauthPolling();
  },

  async onOpen() {
    await this.init();
    await modelConfigStore.ensureLoaded();
    modelConfigStore.resetApiKeyDrafts();
    await modelConfigStore.refreshApiKeyStatus();
    await this.loadConfig();
    await this.loadOauthStatus({ silent: true });
    this.loading = false;
  },

  cleanup() {
    this.stopOauthPolling();
    this.resetState();
  },

  async loadConfig() {
    const response = await fetchApi(`${MODEL_CONFIG_API}/model_config_get`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const data = await response.json().catch(() => ({}));
    this.config = clone(data.config || {});
    ensureSlot(this.config, "chat_model");
    ensureSlot(this.config, "utility_model");
    ensureSlot(this.config, "embedding_model");
    modelConfigStore.initConfigFields(this.config);
    this.providerDetails = detailsById(data.chat_provider_details || modelConfigStore.chatProviderDetails || []);
    if (this.config.chat_model.provider) {
      this.selectedProviderId = this.config.chat_model.provider;
    }
  },

  providerMeta(id) {
    const providerId = String(id || "").trim();
    const fromDetails = this.providerDetails[providerId] || {};
    const fallback = FALLBACKS[providerId] || {};
    const override = ONBOARDING_PROVIDER_OVERRIDES[providerId] || {};
    return {
      ...fallback,
      ...fromDetails,
      ...override,
      id: providerId,
      name: override.name || fromDetails.name || fallback.name || providerId,
      short_description: override.short_description || fromDetails.short_description || fallback.short_description || "Connect this provider to Agent Zero.",
      logo: override.logo || fromDetails.logo || fallback.logo || "/public/darkSymbol.svg",
      api_key_mode: override.api_key_mode || fromDetails.api_key_mode || fallback.api_key_mode || "required",
    };
  },

  topCloudProviders() {
    return TOP_CLOUD_IDS.map((id) => this.providerMeta(id));
  },

  moreCloudProviders() {
    return MORE_CLOUD_IDS.map((id) => this.providerMeta(id));
  },

  filteredMoreCloudProviders() {
    const query = this.moreProviderQuery.trim().toLowerCase();
    const providers = this.moreCloudProviders();
    if (!query) return providers;
    return providers.filter((provider) => {
      const haystack = `${provider.name} ${provider.short_description} ${provider.id}`.toLowerCase();
      return haystack.includes(query);
    });
  },

  localProviderCards() {
    return LOCAL_PROVIDER_IDS.map((id) => {
      const meta = this.providerMeta(id);
      if (id === "other") {
        return {
          ...meta,
          name: "Other local endpoint",
          short_description: "Point Agent Zero at a local compatible server.",
          default_api_base: "",
          api_key_mode: "optional",
        };
      }
      return meta;
    });
  },

  accountMeta() {
    return this.providerMeta("codex_oauth");
  },

  accountActionLabel() {
    return this.oauthConnected() ? "Use connected account" : "Connect via device code";
  },

  selectedProvider() {
    return this.providerMeta(this.selectedProviderId || this.config?.chat_model?.provider || "");
  },

  selectedProviderName() {
    return safeProviderName(this.selectedProvider());
  },

  titleText() {
    if (this.step === "setup") return "Choose your main model";
    if (this.step === "utility") return "Choose your utility model";
    if (this.step === "ready") return "Agent Zero is ready";
    if (this.step === "path") return "Choose how to use AI models in Agent Zero";
    if (this.step === "cloud") return "Choose your cloud AI provider";
    if (this.step === "local") {
      return "Choose your local LLM provider";
    }
    return "Choose how to use AI models in Agent Zero";
  },

  stepNumber(stepName) {
    const index = this.steps.findIndex((item) => item.step === stepName);
    return index >= 0 ? index + 1 : 1;
  },

  currentStepNumber() {
    if (this.step === "cloud" || this.step === "local") return 1;
    return this.stepNumber(this.step);
  },

  isStep(name) {
    return this.step === name;
  },

  choosePath(path) {
    this.pathChoice = path;
    this.step = path === "local" ? "local" : "cloud";
  },

  goBack() {
    if (this.step === "cloud" || this.step === "local") {
      this.step = "path";
      return;
    }
    if (this.step === "setup") {
      this.step = this.pathChoice === "local" ? "local" : "cloud";
      return;
    }
    if (this.step === "utility") {
      this.step = "setup";
      return;
    }
    if (this.step === "ready") {
      this.step = "utility";
    }
  },

  showBackButton() {
    return !["path", "ready"].includes(this.step);
  },

  showPrimaryButton() {
    return ["setup", "utility", "ready"].includes(this.step);
  },

  primaryButtonLabel() {
    if (this.step === "setup") return "Choose utility model";
    if (this.step === "utility") return this.saving ? "Saving" : "Finish setup";
    if (this.step === "ready") return "Start Chatting";
    return "Continue";
  },

  primaryDisabled() {
    if (this.loading || this.saving) return true;
    if (this.step === "setup") {
      if (this.isOAuthProvider() && !this.oauthConnected()) return true;
      if (this.providerNeedsKey(this.selectedProviderId) && !this.hasProviderKey(this.selectedProviderId)) return true;
      return !this.config?.chat_model?.provider || !this.config?.chat_model?.name;
    }
    if (this.step === "utility") return !this.config?.utility_model?.provider || !this.config?.utility_model?.name;
    return false;
  },

  async primaryAction() {
    if (this.primaryDisabled()) return;
    if (this.step === "setup") {
      this.prepareUtilityDefaults();
      this.step = "utility";
      await this.loadModels("utility_model");
      return;
    }
    if (this.step === "utility") {
      await this.completeSetup();
      return;
    }
    if (this.step === "ready") {
      await this.startChatting();
    }
  },

  async selectProvider(providerId, origin = "cloud") {
    this.selectedProviderId = providerId;
    this.selectedProviderOrigin = origin;
    this.pathChoice = origin;
    const meta = this.providerMeta(providerId);
    this.applyProviderToSlot("chat_model", providerId, meta, { forceApiBase: origin === "local" });
    if (providerId === "codex_oauth") {
      await this.loadOauthStatus({ silent: true });
    }
    this.step = "setup";
    if (meta.model_list_autoload !== false) {
      await this.loadModels("chat_model", { openDropdown: false });
    }
  },

  async selectCodexAccount() {
    this.pathChoice = "cloud";
    await this.selectProvider("codex_oauth", "cloud");
  },

  applyProviderToSlot(slotKey, providerId, meta, options = {}) {
    ensureSlot(this.config, slotKey);
    const slot = this.config[slotKey];
    const previousProvider = slot.provider;
    slot.provider = providerId;
    const defaultApiBase = meta.default_api_base || meta.kwargs?.api_base || "";
    if (defaultApiBase && (options.forceApiBase || !slot.api_base)) {
      slot.api_base = defaultApiBase;
    }

    const defaultModel = slotKey === "utility_model"
      ? meta.default_utility_model || meta.default_chat_model || ""
      : meta.default_chat_model || "";
    if (defaultModel && (!slot.name || !this.userTouchedModel[slotKey])) {
      slot.name = defaultModel;
    } else if (previousProvider && previousProvider !== providerId && !this.userTouchedModel[slotKey]) {
      slot.name = "";
    }

    if (!slot.kwargs || typeof slot.kwargs !== "object") slot.kwargs = {};
  },

  localGuidance() {
    return "";
  },

  showApiBaseField() {
    return this.selectedProviderOrigin === "local" || this.selectedProviderId === "other";
  },

  setupPurpose() {
    if (this.isOAuthProvider()) return "Connect once, then Agent Zero can use the local Codex/ChatGPT account bridge without an API key.";
    if (this.selectedProviderOrigin === "local") return "Choose a local model and confirm where Agent Zero can reach it.";
    return "Choose a model and add the key Agent Zero will use for this provider.";
  },

  selectedProviderDocsUrl() {
    const provider = this.selectedProvider();
    return provider.docs_url || provider.api_key_url || provider.setup_url || "";
  },

  openSelectedProviderDocs() {
    const url = this.selectedProviderDocsUrl();
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  },

  providerNeedsKey(providerId) {
    return this.providerMeta(providerId).api_key_mode === "required";
  },

  providerKeyOptional(providerId) {
    return this.providerMeta(providerId).api_key_mode === "optional";
  },

  providerHasNoKey(providerId) {
    const mode = this.providerMeta(providerId).api_key_mode;
    return mode === "none" || mode === "oauth";
  },

  hasProviderKey(providerId) {
    if (!providerId) return false;
    if (this.providerHasNoKey(providerId)) return true;
    const draft = modelConfigStore.apiKeyValues?.[providerId] || "";
    return Boolean(draft.trim() || modelConfigStore.apiKeyStatus?.[providerId]);
  },

  isOAuthProvider() {
    return this.selectedProviderId === "codex_oauth" || this.config?.chat_model?.provider === "codex_oauth";
  },

  oauthConnected() {
    return Boolean(this.oauthStatus?.codex?.connected);
  },

  oauthEmail() {
    return this.oauthStatus?.codex?.email || this.oauthStatus?.codex?.account_email || this.oauthStatus?.codex?.account_id || "";
  },

  oauthStatusLabel() {
    if (this.oauthLoading) return "Checking";
    return this.oauthConnected() ? "Connected" : "Not connected";
  },

  async loadOauthStatus({ silent = false } = {}) {
    if (this.oauthLoading) return;
    this.oauthLoading = true;
    try {
      this.oauthStatus = await callJsonApi(OAUTH_STATUS_API, {});
    } catch (error) {
      if (!silent) globalThis.justToast?.("Could not check account connection", "error");
    } finally {
      this.oauthLoading = false;
    }
  },

  async connectCodex() {
    if (this.oauthConnecting) return;
    this.oauthConnecting = true;
    const popup = window.open("about:blank", "_blank");
    if (popup) popup.opener = null;
    try {
      const response = await callJsonApi(OAUTH_START_API, {});
      if (!response?.ok || !response.verification_url || !response.attempt_id) {
        throw new Error(response?.error || "Could not start account connection.");
      }
      this.oauthDevice = response;
      if (popup && !popup.closed) {
        popup.location.assign(response.verification_url);
      } else {
        window.open(response.verification_url, "_blank", "noopener,noreferrer");
      }
      this.startOauthPolling();
    } catch (error) {
      if (popup && !popup.closed) popup.close();
      this.oauthConnecting = false;
      globalThis.justToast?.(error?.message || "Could not connect account", "error");
    }
  },

  startOauthPolling() {
    this.stopOauthPolling();
    this.oauthPollStartedAt = Date.now();
    const tick = async () => {
      if (!this.oauthDevice?.attempt_id) return;
      try {
        const response = await callJsonApi(OAUTH_POLL_API, { attempt_id: this.oauthDevice.attempt_id });
        if (!response?.ok) {
          if (response?.expired) {
            this.oauthDevice = null;
          }
          throw new Error(response?.error || "Could not finish account connection.");
        }
        if (response.completed) {
          this.oauthConnecting = false;
          this.oauthDevice = null;
          this.stopOauthPolling();
          await this.loadOauthStatus();
          this.applyProviderToSlot("chat_model", "codex_oauth", this.providerMeta("codex_oauth"));
          await this.loadOauthModels();
          return;
        }
      } catch (error) {
        this.oauthConnecting = false;
        this.stopOauthPolling();
        globalThis.justToast?.(error?.message || "Could not connect account", "error");
        return;
      }
      if (Date.now() - this.oauthPollStartedAt > MAX_OAUTH_POLL_MS) {
        this.oauthConnecting = false;
        this.oauthDevice = null;
        this.stopOauthPolling();
      }
    };
    void tick();
    const parsedInterval = Number(this.oauthDevice.interval);
    const intervalSeconds = Number.isFinite(parsedInterval) ? parsedInterval : 5;
    const delay = Math.max(1500, intervalSeconds * 1000);
    this.oauthPollTimer = window.setInterval(tick, delay);
  },

  stopOauthPolling() {
    if (this.oauthPollTimer) window.clearInterval(this.oauthPollTimer);
    this.oauthPollTimer = null;
  },

  async loadOauthModels() {
    try {
      const response = await callJsonApi(OAUTH_MODELS_API, {});
      this.oauthModels = Array.isArray(response?.models) ? response.models : [];
      if (this.oauthModels.length && !this.userTouchedModel.chat_model) {
        this.config.chat_model.name = this.oauthModels[0];
      }
      this.modelDropdown.chat_model.models = this.oauthModels;
      this.modelDropdown.chat_model.source = "oauth";
    } catch {
      this.oauthModels = [];
    }
  },

  cancelOauthConnect() {
    this.oauthConnecting = false;
    this.oauthDevice = null;
    this.stopOauthPolling();
  },

  async loadModels(slotKey, { openDropdown = true } = {}) {
    if (!this.config?.[slotKey]?.provider) return;
    const dropdown = this.modelDropdown[slotKey];
    dropdown.loading = true;
    dropdown.error = "";
    dropdown.source = "";
    try {
      const slot = this.config[slotKey];
      const response = await fetchApi(`${MODEL_CONFIG_API}/model_search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: slot.provider,
          model_type: slotKey === "embedding_model" ? "embedding" : "chat",
          query: "",
          api_base: slot.api_base || "",
        }),
      });
      const data = await response.json().catch(() => ({}));
      dropdown.models = Array.isArray(data.models) ? data.models : [];
      dropdown.source = data.source || "";
      dropdown.error = data.error || "";
      dropdown.open = openDropdown && dropdown.models.length > 0;
      this.selectDefaultModelIfSafe(slotKey);
    } catch (error) {
      dropdown.models = [];
      dropdown.error = error?.message || "Could not load models.";
      dropdown.open = false;
    } finally {
      dropdown.loading = false;
    }
  },

  selectDefaultModelIfSafe(slotKey) {
    const slot = this.config?.[slotKey];
    if (!slot || this.userTouchedModel[slotKey]) return;
    const models = this.modelDropdown[slotKey]?.models || [];
    if (!models.length) return;
    if (slot.name && models.includes(slot.name)) return;
    const meta = this.providerMeta(slot.provider);
    const preferred = slotKey === "utility_model" ? meta.default_utility_model : meta.default_chat_model;
    if (preferred && models.includes(preferred)) {
      slot.name = preferred;
    }
  },

  filteredModels(slotKey) {
    const slot = this.config?.[slotKey] || {};
    const query = String(slot.name || "").trim().toLowerCase();
    const models = this.modelDropdown[slotKey]?.models || [];
    if (!query) return models.slice(0, 80);
    return models.filter((name) => String(name).toLowerCase().includes(query)).slice(0, 80);
  },

  openModelDropdown(slotKey) {
    this.modelDropdown[slotKey].open = true;
    if (!this.modelDropdown[slotKey].models.length && !this.modelDropdown[slotKey].loading) {
      void this.loadModels(slotKey);
    }
  },

  closeModelDropdown(slotKey) {
    this.modelDropdown[slotKey].open = false;
  },

  selectModel(slotKey, modelName) {
    this.config[slotKey].name = modelName;
    this.userTouchedModel[slotKey] = true;
    this.modelDropdown[slotKey].open = false;
    if (slotKey === "chat_model" && this.sameAsMain) {
      this.syncUtilityWithMain();
    }
  },

  markModelTouched(slotKey) {
    this.userTouchedModel[slotKey] = true;
    if (slotKey === "chat_model" && this.sameAsMain) {
      this.syncUtilityWithMain();
    }
  },

  prepareUtilityDefaults() {
    ensureSlot(this.config, "utility_model");
    if (this.sameAsMain) {
      this.syncUtilityWithMain();
      return;
    }
    const mainProvider = this.config.chat_model.provider;
    const meta = this.providerMeta(mainProvider);
    this.applyProviderToSlot("utility_model", mainProvider, meta);
  },

  syncUtilityWithMain() {
    ensureSlot(this.config, "utility_model");
    if (!this.sameAsMain || !this.config?.chat_model) return;
    this.config.utility_model.provider = this.config.chat_model.provider;
    this.config.utility_model.name = this.config.chat_model.name;
    this.config.utility_model.api_base = this.config.chat_model.api_base || "";
    this.config.utility_model.kwargs = clone(this.config.chat_model.kwargs || {});
  },

  async utilityProviderChanged() {
    const providerId = this.config.utility_model.provider;
    this.sameAsMain = providerId === this.config.chat_model.provider;
    this.userTouchedModel.utility_model = false;
    this.applyProviderToSlot("utility_model", providerId, this.providerMeta(providerId));
    await this.loadModels("utility_model");
  },

  async completeSetup() {
    this.saving = true;
    try {
      if (this.sameAsMain) this.syncUtilityWithMain();
      await modelConfigStore.persistApiKeysForConfig(this.config);
      const response = await fetchApi(`${MODEL_CONFIG_API}/model_config_set`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_name: "",
          agent_profile: "",
          config: this.config,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!data?.ok) throw new Error(data?.error || "Could not save model setup.");
      await modelConfigStore.refreshApiKeyStatus();
      this.step = "ready";
      document.dispatchEvent(new CustomEvent("onboarding-configured"));
    } catch (error) {
      globalThis.justToast?.(error?.message || "Could not save setup", "error");
    } finally {
      this.saving = false;
    }
  },

  async startChatting() {
    window.closeModal?.();
    await chatsStore.newChat();
  },

  async openAdvancedSettings() {
    window.closeModal?.();
    const { store: pluginSettingsStore } = await import("/components/plugins/plugin-settings-store.js");
    await pluginSettingsStore.openConfig("_model_config");
  },
});
