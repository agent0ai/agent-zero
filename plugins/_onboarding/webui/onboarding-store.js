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
const OAUTH_START_API = "/plugins/_oauth/start_login";
const OAUTH_POLL_API = "/plugins/_oauth/poll_device_login";
const OAUTH_MANUAL_CALLBACK_API = "/plugins/_oauth/manual_callback";
const OAUTH_MODELS_API = "/plugins/_oauth/models";
const MAX_OAUTH_POLL_MS = 120000;

const TOP_CLOUD_IDS = TOP_CLOUD_PROVIDER_IDS;
const MORE_CLOUD_IDS = MORE_CLOUD_PROVIDER_IDS;

const OAUTH_MARKS = {
  github: "terminal",
  google: "cloud",
  openai: "key",
  xai: "neurology",
};

const FALLBACKS = {
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
  step: "connect",
  providerMode: "cloud",
  presetMode: "",
  loading: true,
  saving: false,
  config: null,
  providerDetails: {},
  selectedProviderId: "",
  selectedProviderOrigin: "cloud",
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
  oauthConnectingProvider: "",
  oauthDevice: null,
  oauthPollTimer: null,
  oauthCallbackPollTimer: null,
  oauthPollStartedAt: 0,
  oauthModels: {},
  oauthProviderUi: {},

  steps: [
    { step: "connect", label: "Choose provider" },
    { step: "setup", label: "Connect" },
    { step: "utility", label: "Utility" },
    { step: "ready", label: "Ready" },
  ],

  async init() {
    this.resetState();
  },

  resetState() {
    this.step = "connect";
    this.providerMode = ["local", "account"].includes(this.presetMode) ? this.presetMode : "cloud";
    this.presetMode = "";
    this.loading = true;
    this.saving = false;
    this.config = null;
    this.providerDetails = {};
    this.selectedProviderId = "";
    this.selectedProviderOrigin = "cloud";
    this.userTouchedModel = { chat_model: false, utility_model: false };
    this.modelDropdown = {
      chat_model: { models: [], open: false, loading: false, error: "", source: "" },
      utility_model: { models: [], open: false, loading: false, error: "", source: "" },
    };
    this.oauthStatus = null;
    this.oauthLoading = false;
    this.oauthConnecting = false;
    this.oauthConnectingProvider = "";
    this.oauthDevice = null;
    this.oauthModels = {};
    this.oauthProviderUi = {};
    this.stopOauthPolling();
    this.stopOauthCallbackPolling();
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
    const oauth = this.oauthProviderStatus(providerId);
    if (oauth) {
      const defaultModels = Array.isArray(oauth.default_models) ? oauth.default_models : [];
      return {
        ...fallback,
        ...fromDetails,
        ...override,
        id: providerId,
        name: oauth.display_name || fromDetails.name || override.name || providerId,
        short_description: oauth.connected
          ? (oauth.account_label || "Connected")
          : (oauth.note || oauth.warning || "Connect this account-backed provider."),
        logo: override.logo || fromDetails.logo || "/public/darkSymbol.svg",
        api_key_mode: "oauth",
        default_chat_model: oauth.default_model || defaultModels[0] || fromDetails.default_chat_model || "",
        default_utility_model: defaultModels[1] || oauth.default_model || fromDetails.default_utility_model || "",
        model_list_autoload: Boolean(oauth.connected),
        auth_flow: oauth.auth_flow || "",
      };
    }
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

  cloudProviders() {
    return [...TOP_CLOUD_IDS, ...MORE_CLOUD_IDS].map((id) => this.providerMeta(id));
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

  oauthProviderStatus(providerId) {
    const key = String(providerId || "").trim();
    if (!key) return null;
    return this.oauthStatus?.provider_map?.[key] || null;
  },

  oauthProviderCards() {
    const providers = Array.isArray(this.oauthStatus?.providers) ? this.oauthStatus.providers : [];
    return providers.filter((provider) => provider?.provider_id);
  },

  oauthProviderUiFor(providerId) {
    const key = String(providerId || "").trim();
    if (!key) return {};
    if (!this.oauthProviderUi[key]) {
      this.oauthProviderUi = {
        ...this.oauthProviderUi,
        [key]: {
          enterprise_domain: "",
          client_id: "",
          client_secret: "",
          quota_project_id: "",
          manualCallback: "",
        },
      };
    }
    return this.oauthProviderUi[key];
  },

  oauthMark(provider) {
    return provider?.connected ? "check" : (provider?.mark || OAUTH_MARKS[provider?.icon] || "account_circle");
  },

  oauthCardTitle(provider) {
    return provider?.display_name || provider?.short_name || provider?.provider_id || "Account";
  },

  oauthCardSubtitle(provider) {
    if (this.oauthLoading) return "Checking";
    if (provider?.connected) return provider.account_label || provider.email || "Connected";
    if (!this.oauthSetupReady(provider?.provider_id)) return "Needs OAuth client details";
    if (provider?.warning) return "Available with restrictions";
    return "Not connected";
  },

  oauthAccountActionLabel(providerId) {
    const provider = this.oauthProviderStatus(providerId);
    if (provider?.connected) return "Use account";
    if (this.oauthConnectingProvider === providerId) return "Waiting for sign-in";
    return this.oauthSetupReady(providerId) ? "Connect account" : "Configure";
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
    return "Choose your AI provider";
  },

  stepNumber(stepName) {
    const index = this.steps.findIndex((item) => item.step === stepName);
    return index >= 0 ? index + 1 : 1;
  },

  currentStepNumber() {
    return this.stepNumber(this.step);
  },

  isStep(name) {
    return this.step === name;
  },

  setProviderMode(mode) {
    this.providerMode = ["local", "account"].includes(mode) ? mode : "cloud";
  },

  goBack() {
    if (this.step === "setup") {
      this.step = "connect";
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
    return !["connect", "ready"].includes(this.step);
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
      if (this.isOAuthProvider() && !this.oauthConnected(this.selectedProviderId)) return true;
      if (this.providerNeedsKey(this.selectedProviderId) && !this.hasProviderKey(this.selectedProviderId)) return true;
      return !this.config?.chat_model?.provider || !this.config?.chat_model?.name;
    }
    if (this.step === "utility") {
      const utilityProvider = this.config?.utility_model?.provider || "";
      if (this.isOAuthProvider(utilityProvider) && !this.oauthConnected(utilityProvider)) return true;
      return !utilityProvider || !this.config?.utility_model?.name;
    }
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
    this.providerMode = ["local", "account"].includes(origin) ? origin : "cloud";
    const meta = this.providerMeta(providerId);
    this.applyProviderToSlot("chat_model", providerId, meta, { forceApiBase: origin === "local" });
    if (this.isOAuthProvider(providerId)) {
      await this.loadOauthStatus({ silent: true });
    }
    this.step = "setup";
    if (this.isOAuthProvider(providerId)) {
      if (this.oauthConnected(providerId)) {
        await this.loadModels("chat_model", { openDropdown: false });
      }
    } else if (meta.model_list_autoload !== false) {
      await this.loadModels("chat_model", { openDropdown: false });
    }
  },

  async selectOAuthProvider(providerId) {
    await this.selectProvider(providerId, "account");
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
    if (this.isOAuthProvider()) return "Connect this account, then choose the account-backed model Agent Zero should use.";
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

  isOAuthProvider(providerId = "") {
    const key = String(providerId || this.selectedProviderId || this.config?.chat_model?.provider || "").trim();
    if (!key) return false;
    return Boolean(this.oauthProviderStatus(key) || this.providerMeta(key).api_key_mode === "oauth");
  },

  oauthConnected(providerId = "") {
    const key = String(providerId || this.selectedProviderId || this.config?.chat_model?.provider || "").trim();
    return Boolean(this.oauthProviderStatus(key)?.connected);
  },

  oauthEmail(providerId = "") {
    const status = this.oauthProviderStatus(providerId || this.selectedProviderId) || {};
    return status.account_label || status.email || status.account_email || status.account_id || "";
  },

  oauthStatusLabel(providerId = "") {
    if (this.oauthLoading) return "Checking";
    const status = this.oauthProviderStatus(providerId || this.selectedProviderId);
    if (!status) return "Not connected";
    if (status.connected) return this.oauthEmail(status.provider_id) || "Connected";
    if (!this.oauthSetupReady(status.provider_id)) return "Needs OAuth client details";
    return "Not connected";
  },

  oauthSetupReady(providerId = "") {
    const status = this.oauthProviderStatus(providerId || this.selectedProviderId);
    if (!status?.supports_oauth_client_config) return true;
    const ui = this.oauthProviderUiFor(status.provider_id);
    const clientId = ui.client_id || status.client_id || "";
    const hasSecret = Boolean(ui.client_secret || status.client_secret_configured);
    return Boolean(String(clientId).trim() && hasSecret);
  },

  async loadOauthStatus({ silent = false } = {}) {
    if (this.oauthLoading) return;
    this.oauthLoading = true;
    try {
      this.oauthStatus = await callJsonApi(OAUTH_STATUS_API, {});
      for (const provider of this.oauthProviderCards()) {
        const ui = this.oauthProviderUiFor(provider.provider_id);
        if (provider.enterprise_domain && !ui.enterprise_domain) ui.enterprise_domain = provider.enterprise_domain;
        if (provider.client_id && !ui.client_id) ui.client_id = provider.client_id;
        if (provider.quota_project_id && !ui.quota_project_id) ui.quota_project_id = provider.quota_project_id;
      }
    } catch (error) {
      if (!silent) globalThis.justToast?.("Could not check account connection", "error");
    } finally {
      this.oauthLoading = false;
    }
  },

  async connectOAuth(providerId = "") {
    const selectedProvider = String(providerId || this.selectedProviderId || "").trim();
    if (!selectedProvider || this.oauthConnecting) return;
    this.oauthConnecting = true;
    this.oauthConnectingProvider = selectedProvider;
    const popup = window.open("about:blank", "_blank");
    if (popup) popup.opener = null;
    try {
      const payload = this.oauthLoginPayload(selectedProvider);
      const response = await callJsonApi(OAUTH_START_API, payload);
      if (!response?.ok) {
        throw new Error(response?.error || "Could not start account connection.");
      }
      this.oauthDevice = response;
      if (response.flow === "device_code" && response.verification_url && response.attempt_id) {
        if (popup && !popup.closed) {
          popup.location.assign(response.verification_url);
        } else {
          window.open(response.verification_url, "_blank", "noopener,noreferrer");
        }
        this.startOauthPolling(selectedProvider);
        return;
      }
      if (response.flow === "browser_pkce" && response.auth_url) {
        if (popup && !popup.closed) {
          popup.location.assign(response.auth_url);
        } else {
          window.open(response.auth_url, "_blank", "noopener,noreferrer");
        }
        this.startOauthCallbackPolling(selectedProvider);
        return;
      }
      throw new Error(response?.error || "Could not start account connection.");
    } catch (error) {
      if (popup && !popup.closed) popup.close();
      this.oauthConnecting = false;
      this.oauthConnectingProvider = "";
      globalThis.justToast?.(error?.message || "Could not connect account", "error");
    }
  },

  oauthLoginPayload(providerId) {
    const status = this.oauthProviderStatus(providerId) || {};
    const ui = this.oauthProviderUiFor(providerId);
    const payload = { provider_id: providerId };
    if (status.supports_enterprise_domain) {
      payload.enterprise_domain = ui.enterprise_domain || "";
    }
    if (status.supports_oauth_client_config) {
      payload.client_id = ui.client_id || "";
      payload.client_secret = ui.client_secret || "";
    }
    if (status.supports_quota_project) {
      payload.quota_project_id = ui.quota_project_id || "";
    }
    return payload;
  },

  startOauthPolling(providerId = "") {
    this.stopOauthPolling();
    this.oauthPollStartedAt = Date.now();
    const tick = async () => {
      if (!this.oauthDevice?.attempt_id) return;
      try {
        const response = await callJsonApi(OAUTH_POLL_API, {
          provider_id: providerId,
          attempt_id: this.oauthDevice.attempt_id,
        });
        if (!response?.ok) {
          if (response?.expired) {
            this.oauthDevice = null;
          }
          throw new Error(response?.error || "Could not finish account connection.");
        }
        if (response.completed) {
          this.oauthConnecting = false;
          this.oauthConnectingProvider = "";
          this.oauthDevice = null;
          this.stopOauthPolling();
          await this.loadOauthStatus();
          this.applyProviderToSlot("chat_model", providerId, this.providerMeta(providerId));
          await this.loadOauthModels(providerId, "chat_model");
          return;
        }
      } catch (error) {
        this.oauthConnecting = false;
        this.oauthConnectingProvider = "";
        this.stopOauthPolling();
        globalThis.justToast?.(error?.message || "Could not connect account", "error");
        return;
      }
      if (Date.now() - this.oauthPollStartedAt > MAX_OAUTH_POLL_MS) {
        this.oauthConnecting = false;
        this.oauthConnectingProvider = "";
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

  startOauthCallbackPolling(providerId = "") {
    this.stopOauthCallbackPolling();
    this.oauthPollStartedAt = Date.now();
    const tick = async () => {
      await this.loadOauthStatus({ silent: true });
      if (this.oauthConnected(providerId)) {
        this.oauthConnecting = false;
        this.oauthConnectingProvider = "";
        this.oauthDevice = null;
        this.stopOauthCallbackPolling();
        this.applyProviderToSlot("chat_model", providerId, this.providerMeta(providerId));
        await this.loadOauthModels(providerId, "chat_model");
        return;
      }
      if (Date.now() - this.oauthPollStartedAt > MAX_OAUTH_POLL_MS) {
        this.oauthConnecting = false;
        this.oauthConnectingProvider = "";
        this.oauthDevice = null;
        this.stopOauthCallbackPolling();
      }
    };
    void tick();
    this.oauthCallbackPollTimer = window.setInterval(tick, 2500);
  },

  stopOauthCallbackPolling() {
    if (this.oauthCallbackPollTimer) window.clearInterval(this.oauthCallbackPollTimer);
    this.oauthCallbackPollTimer = null;
  },

  async submitOAuthManualCallback(providerId = "") {
    const selectedProvider = String(providerId || this.selectedProviderId || "").trim();
    const callback = String(this.oauthProviderUiFor(selectedProvider).manualCallback || "").trim();
    if (!selectedProvider || !callback) {
      globalThis.justToast?.("Paste callback URL, query string, or code.", "error");
      return;
    }
    this.oauthConnecting = true;
    this.oauthConnectingProvider = selectedProvider;
    try {
      const response = await callJsonApi(OAUTH_MANUAL_CALLBACK_API, {
        provider_id: selectedProvider,
        callback,
      });
      if (!response?.ok) {
        throw new Error(response?.error || "Could not finish account connection.");
      }
      this.oauthProviderUiFor(selectedProvider).manualCallback = "";
      this.oauthDevice = null;
      this.stopOauthCallbackPolling();
      await this.loadOauthStatus();
      this.applyProviderToSlot("chat_model", selectedProvider, this.providerMeta(selectedProvider));
      await this.loadOauthModels(selectedProvider, "chat_model");
    } catch (error) {
      globalThis.justToast?.(error?.message || "Could not connect account", "error");
    } finally {
      this.oauthConnecting = false;
      this.oauthConnectingProvider = "";
    }
  },

  async loadOauthModels(providerId = "", slotKey = "chat_model", { openDropdown = true } = {}) {
    const selectedProvider = String(providerId || this.config?.[slotKey]?.provider || this.selectedProviderId || "").trim();
    if (!selectedProvider) return;
    const dropdown = this.modelDropdown[slotKey];
    dropdown.loading = true;
    dropdown.error = "";
    dropdown.source = "";
    try {
      const response = await callJsonApi(OAUTH_MODELS_API, { provider_id: selectedProvider });
      if (!response?.ok) {
        throw new Error(response?.error || "Could not load account models.");
      }
      const models = Array.isArray(response?.models) ? response.models : [];
      this.oauthModels = { ...this.oauthModels, [selectedProvider]: models };
      dropdown.models = models;
      dropdown.source = "oauth";
      dropdown.open = openDropdown && models.length > 0;
      if (models.length && !this.userTouchedModel[slotKey]) {
        const meta = this.providerMeta(selectedProvider);
        const preferred = slotKey === "utility_model" ? meta.default_utility_model : meta.default_chat_model;
        this.config[slotKey].name = preferred && models.includes(preferred) ? preferred : models[0];
      }
    } catch (error) {
      this.oauthModels = { ...this.oauthModels, [selectedProvider]: [] };
      dropdown.models = [];
      dropdown.error = error?.message || "Could not load account models.";
      dropdown.open = false;
    } finally {
      dropdown.loading = false;
    }
  },

  cancelOauthConnect() {
    this.oauthConnecting = false;
    this.oauthConnectingProvider = "";
    this.oauthDevice = null;
    this.stopOauthPolling();
    this.stopOauthCallbackPolling();
  },

  async loadModels(slotKey, { openDropdown = true } = {}) {
    if (!this.config?.[slotKey]?.provider) return;
    if (this.isOAuthProvider(this.config[slotKey].provider)) {
      await this.loadOauthModels(this.config[slotKey].provider, slotKey, { openDropdown });
      return;
    }
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
  },

  markModelTouched(slotKey) {
    this.userTouchedModel[slotKey] = true;
  },

  prepareUtilityDefaults() {
    const mainProvider = this.config.chat_model.provider;
    this.applyProviderToSlot("utility_model", mainProvider, this.providerMeta(mainProvider));
    if (!this.config.utility_model.api_base) {
      this.config.utility_model.api_base = this.config.chat_model.api_base || "";
    }
  },

  async utilityProviderChanged() {
    const providerId = this.config.utility_model.provider;
    this.userTouchedModel.utility_model = false;
    this.config.utility_model.api_base = "";
    this.applyProviderToSlot("utility_model", providerId, this.providerMeta(providerId));
    if (!this.config.utility_model.api_base && providerId === this.config.chat_model.provider) {
      this.config.utility_model.api_base = this.config.chat_model.api_base || "";
    }
    await this.loadModels("utility_model");
  },

  async completeSetup() {
    this.saving = true;
    try {
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
    await modelConfigStore.openPresetEditor(
      this.config?.model_preset || "Default"
    );
  },
});
