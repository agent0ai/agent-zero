import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, fetchApi } from "/js/api.js";
import { store as modelConfigStore } from "/plugins/_model_config/webui/model-config-store.js";
import {
  toastFrontendError,
  toastFrontendInfo,
  toastFrontendSuccess,
} from "/components/notifications/notification-store.js";

const MODEL_CONFIG_API = "/plugins/_model_config";
const STATUS_API = "/plugins/_oauth/status";
const START_LOGIN_API = "/plugins/_oauth/start_login";
const POLL_LOGIN_API = "/plugins/_oauth/poll_device_login";
const MANUAL_CALLBACK_API = "/plugins/_oauth/manual_callback";
const MODELS_API = "/plugins/_oauth/models";
const DISCONNECT_API = "/plugins/_oauth/disconnect";
const MAX_POLL_MS = 120000;
const CODEX_PROVIDER = "codex_oauth";
const PROVIDER_MARKS = {
  github: "terminal",
  google: "cloud",
  openai: "key",
  xai: "neurology",
};
const MODEL_SLOTS = [
  {
    key: "chat_model",
    title: "Main model",
    icon: "forum",
  },
  {
    key: "utility_model",
    title: "Utility model",
    icon: "manufacturing",
  },
];

function ensureConfig(config) {
  if (!config || typeof config !== "object") return null;
  config.codex = config.codex && typeof config.codex === "object" ? config.codex : {};
  const codex = config.codex;
  codex.enabled = codex.enabled !== false;
  codex.auth_file_path = String(codex.auth_file_path || "");
  codex.issuer = String(codex.issuer || "https://auth.openai.com");
  codex.token_url = String(codex.token_url || "https://auth.openai.com/oauth/token");
  codex.client_id = String(codex.client_id || "app_EMoamEEZ73f0CkXaXp7hrann");
  codex.upstream_base_url = String(codex.upstream_base_url || "https://chatgpt.com/backend-api/codex");
  codex.proxy_base_path = String(codex.proxy_base_path || "/oauth/codex");
  codex.callback_path = String(codex.callback_path || "/auth/callback");
  codex.require_proxy_token = Boolean(codex.require_proxy_token);
  codex.proxy_token = String(codex.proxy_token || "");
  codex.codex_version = String(codex.codex_version || "");
  codex.models = Array.isArray(codex.models) ? codex.models : [];

  config.gemini_api = config.gemini_api && typeof config.gemini_api === "object" ? config.gemini_api : {};
  const geminiApi = config.gemini_api;
  geminiApi.enabled = geminiApi.enabled !== false;
  geminiApi.client_id = String(geminiApi.client_id || "");
  geminiApi.client_secret = String(geminiApi.client_secret || "");
  geminiApi.quota_project_id = String(geminiApi.quota_project_id || "");
  geminiApi.scopes = Array.isArray(geminiApi.scopes) ? geminiApi.scopes : [];
  geminiApi.api_base_url = String(geminiApi.api_base_url || "https://generativelanguage.googleapis.com/v1beta/openai");
  geminiApi.proxy_base_path = String(geminiApi.proxy_base_path || "/oauth/gemini-api");
  geminiApi.callback_path = String(geminiApi.callback_path || "/oauth/gemini-api/callback");
  return config;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value || {}));
}

function ensureModelSlot(config, key) {
  if (!config[key] || typeof config[key] !== "object") config[key] = {};
  config[key] = {
    provider: "",
    name: "",
    api_base: "",
    ctx_length: key === "utility_model" ? 128000 : 200000,
    ctx_history: key === "chat_model" ? 0.7 : undefined,
    ctx_input: key === "utility_model" ? 0.7 : undefined,
    vision: key === "chat_model" ? true : undefined,
    max_embeds: key === "chat_model" ? 10 : undefined,
    rl_requests: 0,
    rl_input: 0,
    rl_output: 0,
    kwargs: {},
    ...config[key],
  };
  if (!config[key].kwargs || typeof config[key].kwargs !== "object") config[key].kwargs = {};
}

function messageOf(error) {
  return error instanceof Error ? error.message : String(error);
}

function providerUiDefaults() {
  return {};
}

export const store = createStore("oauthConfig", {
  config: null,
  status: null,
  loadingStatus: false,
  connecting: false,
  disconnecting: false,
  loadingModels: false,
  providerModels: {},
  providerModelMetadata: {},
  providerUi: providerUiDefaults(),
  connectingProvider: "",
  disconnectingProvider: "",
  loadingModelsProvider: "",
  selectedProviderId: "",
  activeModelProvider: CODEX_PROVIDER,
  models: [],
  modelSlots: MODEL_SLOTS,
  modelConfig: null,
  modelConfigLoading: false,
  modelConfigSaving: false,
  modelConfigDirty: false,
  modelSlotCurrentProviders: {},
  modelSlotDirty: {
    chat_model: false,
    utility_model: false,
  },
  modelDropdown: {
    chat_model: { open: false },
    utility_model: { open: false },
  },
  devices: {},
  pollTimers: {},
  pollStartedAt: {},
  callbackPollTimers: {},
  callbackPollStartedAt: {},
  device: null,
  pollTimer: null,

  async init(config, context = null) {
    this.bindConfig(config);
    this.installSettingsHooks(context);
    await Promise.all([this.loadStatus(), this.loadModelConfig()]);
    this.applySoleConnectedProviderDefaults();
  },

  cleanup() {
    this.stopPolling();
    this.stopCallbackPolling();
    this.config = null;
    this.status = null;
    this.connecting = false;
    this.disconnecting = false;
    this.loadingModels = false;
    this.providerModels = {};
    this.providerModelMetadata = {};
    this.providerUi = providerUiDefaults();
    this.connectingProvider = "";
    this.disconnectingProvider = "";
    this.loadingModelsProvider = "";
    this.selectedProviderId = "";
    this.activeModelProvider = CODEX_PROVIDER;
    this.models = [];
    this.modelConfig = null;
    this.modelConfigLoading = false;
    this.modelConfigSaving = false;
    this.modelConfigDirty = false;
    this.modelSlotCurrentProviders = {};
    this.modelSlotDirty = { chat_model: false, utility_model: false };
    this.modelDropdown = {
      chat_model: { open: false },
      utility_model: { open: false },
    };
    this.devices = {};
    this.pollStartedAt = {};
    this.callbackPollTimers = {};
    this.callbackPollStartedAt = {};
    this.device = null;
  },

  bindConfig(config) {
    const safeConfig = ensureConfig(config);
    if (!safeConfig) return;
    if (this.config === safeConfig) return;
    this.config = safeConfig;
  },

  codex() {
    return this.config?.codex || {};
  },

  geminiApi() {
    return this.config?.gemini_api || {};
  },

  providerMap() {
    const mapped = this.status?.provider_map;
    if (mapped && typeof mapped === "object") return mapped;
    const providers = Array.isArray(this.status?.providers) ? this.status.providers : [];
    return providers.reduce((result, provider) => {
      if (provider?.provider_id) result[provider.provider_id] = provider;
      return result;
    }, {});
  },

  providerStatus(providerId) {
    return this.providerMap()[providerId] || {};
  },

  providerUiFor(providerId) {
    const key = String(providerId || "");
    if (!key) return {};
    if (!this.providerUi[key]) {
      this.providerUi = {
        ...this.providerUi,
        [key]: {
          enterprise_domain: "",
          manualCallback: "",
          client_id: "",
          client_secret: "",
          quota_project_id: "",
        },
      };
    }
    return this.providerUi[key];
  },

  providerCards() {
    const map = this.providerMap();
    const providers = Array.isArray(this.status?.providers)
      ? this.status.providers
      : Object.values(map);
    return providers
      .filter((provider) => provider?.provider_id)
      .map((status) => {
        const providerId = status.provider_id;
        return {
          ...status,
          provider_id: providerId,
          connected: Boolean(status.connected),
          mark: status.mark || PROVIDER_MARKS[status.icon] || "key",
          use_label: status.use_label || `Use ${status.short_name || status.display_name || providerId}`,
          device: this.devices[providerId] || null,
          connecting: this.connectingProvider === providerId,
          disconnecting: this.disconnectingProvider === providerId,
          loadingModels: this.loadingModelsProvider === providerId,
        };
      });
  },

  connectedProviderCards() {
    return this.providerCards().filter((card) => card.connected);
  },

  availableProviderCards() {
    return this.providerCards().filter((card) => !card.connected);
  },

  selectedProvider() {
    const selected = this.providerCards().find((card) => card.provider_id === this.selectedProviderId);
    return selected || this.providerCards()[0] || null;
  },

  selectProvider(providerId) {
    if (!this.isOauthProvider(providerId)) return;
    this.selectedProviderId = providerId;
  },

  connectedSummaryLabel() {
    const connected = this.connectedProviderCards().length;
    const total = this.providerCards().length;
    if (!connected) return "Connect account-backed providers here. More than one can be connected at the same time.";
    if (connected === 1) return `1 of ${total} account providers connected.`;
    return `${connected} of ${total} account providers connected.`;
  },

  providerIds() {
    return this.providerCards().map((card) => card.provider_id);
  },

  isOauthProvider(providerId) {
    const key = String(providerId || "");
    return Boolean(key && this.providerMap()[key]);
  },

  providerConnected(providerId) {
    return Boolean(this.providerStatus(providerId)?.connected);
  },

  providerLabel(providerId) {
    const status = this.providerStatus(providerId);
    return status.display_name || providerId;
  },

  providerUseLabel(providerId) {
    const status = this.providerStatus(providerId);
    return status.use_label || `Use ${status.short_name || status.display_name || providerId}`;
  },

  providerStatusLabel(providerId) {
    if (this.loadingStatus) return "Checking";
    const status = this.providerStatus(providerId);
    if (!status.connected) return "Not connected";
    return status.account_label || status.email || "Connected";
  },

  providerDevice(providerId) {
    return this.devices[String(providerId || "")] || null;
  },

  providerShowSetupFields(providerId) {
    if (this.providerConnected(providerId)) return false;
    if (this.providerDevice(providerId)) return false;
    return this.selectedProviderId === providerId;
  },

  providerShowNote(providerId) {
    if (this.providerConnected(providerId)) return false;
    const status = this.providerStatus(providerId);
    return this.selectedProviderId === providerId && Boolean(status.warning || status.note);
  },

  providerDetailOpen(providerId) {
    if (!this.isOauthProvider(providerId) || this.providerConnected(providerId)) return false;
    if (this.providerDevice(providerId)) return true;
    const status = this.providerStatus(providerId);
    return this.selectedProviderId === providerId && Boolean(
      status.supports_enterprise_domain
      || status.supports_oauth_client_config
      || status.warning
      || status.note
    );
  },

  providerReadinessLabel(providerId) {
    const status = this.providerStatus(providerId);
    if (this.loadingStatus) return "Checking";
    if (status.connected) return this.providerStatusLabel(providerId);
    if (!this.providerSetupReady(providerId)) return "Needs OAuth client details";
    if (status.warning) return "Available with restrictions";
    return "Ready to connect";
  },

  providerSetupReady(providerId) {
    const status = this.providerStatus(providerId);
    if (!status.supports_oauth_client_config) return true;
    const ui = this.providerUiFor(providerId);
    const clientId = ui.client_id || status.client_id || this.geminiApi().client_id || "";
    const hasSecret = Boolean(
      ui.client_secret
      || this.geminiApi().client_secret
      || status.client_secret_configured
    );
    return Boolean(String(clientId).trim() && hasSecret);
  },

  providerPrimaryLabel(providerId) {
    if (this.connectingProvider === providerId) return "Waiting";
    return this.providerSetupReady(providerId) ? "Connect" : "Configure";
  },

  providerPrimaryDisabled(providerId) {
    if (!this.isOauthProvider(providerId)) return true;
    if (this.connectingProvider || this.disconnectingProvider) return true;
    return false;
  },

  handleProviderPrimary(providerId) {
    this.selectProvider(providerId);
    if (!this.providerSetupReady(providerId)) return;
    void this.connectProvider(providerId);
  },

  providerEndpointUrl(providerId) {
    const status = this.providerStatus(providerId);
    const proxyBase = String(status.proxy_base_path || "").replace(/\/$/, "");
    const base = status.v1_base_path || (proxyBase ? `${proxyBase}/v1` : "");
    return base ? `${window.location.origin}${base}` : "";
  },

  providerCallbackUrl(providerId) {
    const status = this.providerStatus(providerId);
    const path = status.callback_path || "";
    return path ? `${window.location.origin}${path}` : "";
  },

  usage(providerId = CODEX_PROVIDER) {
    return this.providerStatus(providerId)?.usage || null;
  },

  usageWindows(providerId = CODEX_PROVIDER) {
    const status = this.providerStatus(providerId);
    if (Array.isArray(status.usage_windows) && status.usage_windows.length) {
      return status.usage_windows.filter((window) => Number.isFinite(this.remainingPercent(window)));
    }
    const usage = this.usage(providerId);
    if (!usage?.available) return [];
    return [
      { key: "primary", title: "Session", ...(usage.primary || {}) },
      { key: "secondary", title: "Week", ...(usage.secondary || {}) },
    ].filter((window) => Number.isFinite(this.remainingPercent(window)));
  },

  connectedUsageWindows() {
    const windows = [];
    for (const card of this.connectedProviderCards()) {
      for (const window of this.usageWindows(card.provider_id)) {
        windows.push({
          ...window,
          key: `${card.provider_id}-${window.key}`,
          title: `${card.short_name || card.display_name || "Account"} ${window.title}`,
        });
      }
    }
    return windows;
  },

  usagePlanCatalog() {
    const catalog = this.status?.usage_plan_catalog;
    return catalog && typeof catalog === "object" ? catalog : {};
  },

  usagePlanEntries() {
    const catalog = this.usagePlanCatalog();
    const providerIds = this.providerIds();
    const ids = [
      ...providerIds,
      ...Object.keys(catalog).filter((providerId) => !providerIds.includes(providerId)),
    ];
    return ids
      .map((providerId) => catalog[providerId])
      .filter((entry) => entry && Array.isArray(entry.plans) && entry.plans.length);
  },

  usagePlanStatus() {
    return "Provider available";
  },

  usagePlanNotes(entry) {
    return Array.isArray(entry?.notes) ? entry.notes.slice(0, 2) : [];
  },

  usageWidth(window) {
    const value = Math.max(0, Math.min(100, this.remainingPercent(window)));
    return `${value}%`;
  },

  remainingPercent(window) {
    const remaining = Number(window?.remaining_percent);
    if (Number.isFinite(remaining)) return remaining;
    const used = Number(window?.used_percent);
    if (Number.isFinite(used)) return 100 - used;
    return Number.NaN;
  },

  formatRemainingPercent(window) {
    const number = this.remainingPercent(window);
    if (!Number.isFinite(number)) return "0%";
    return `${Math.round(number * 10) / 10}% left`;
  },

  formatWindowLabel(window) {
    return window?.label || "";
  },

  formatReset(window) {
    const seconds = Number(window?.reset_at || 0);
    if (!Number.isFinite(seconds) || seconds <= 0) return "";
    const remainingMs = Math.max(0, seconds * 1000 - Date.now());
    const minutes = Math.round(remainingMs / 60000);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.round(minutes / 60);
    if (hours < 48) return `${hours}h`;
    return `${Math.round(hours / 24)}d`;
  },

  installSettingsHooks(context) {
    if (!context || context.__oauthConfigHooksInstalled) return;

    const originalSave = context.save.bind(context);
    context.save = async () => {
      context.error = null;
      try {
        await this.saveModelConfigIfDirty();
      } catch (error) {
        context.error = messageOf(error) || "Failed to save model selection.";
        return;
      }
      await originalSave();
    };

    context.__oauthConfigHooksInstalled = true;
  },

  async loadModelConfig() {
    if (this.modelConfigLoading) return;
    this.modelConfigLoading = true;
    try {
      await modelConfigStore.ensureLoaded();
      const response = await fetchApi(`${MODEL_CONFIG_API}/model_config_get`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await response.json().catch(() => ({}));
      const modelConfig = data.config && typeof data.config === "object" ? data.config : {};
      ensureModelSlot(modelConfig, "chat_model");
      ensureModelSlot(modelConfig, "utility_model");
      this.modelConfig = modelConfig;
      this.modelSlotCurrentProviders = Object.fromEntries(
        MODEL_SLOTS.map((slot) => [slot.key, modelConfig[slot.key].provider || ""]),
      );
      this.modelConfigDirty = false;
      this.modelSlotDirty = { chat_model: false, utility_model: false };
    } catch (error) {
      this.modelConfig = null;
      void toastFrontendError(messageOf(error), "OAuth Connections");
    } finally {
      this.modelConfigLoading = false;
    }
  },

  modelSlot(key) {
    if (!this.modelConfig) return {};
    ensureModelSlot(this.modelConfig, key);
    return this.modelConfig[key];
  },

  slotUsesOauth(key) {
    return this.isOauthProvider(this.modelSlot(key).provider);
  },

  slotUsesProvider(key, providerId) {
    return this.modelSlot(key).provider === providerId;
  },

  providerName(provider) {
    if (!provider) return "Not configured";
    const found = (modelConfigStore.chatProviders || []).find((item) => item.value === provider);
    return found?.label || this.providerLabel(provider);
  },

  slotProviderChoices() {
    return this.connectedProviderCards();
  },

  modelProviderOptionLabel(provider) {
    return provider?.display_name || provider?.short_name || provider?.provider_id || "Connected account";
  },

  applySoleConnectedProviderDefaults() {
    const providers = this.connectedProviderCards();
    if (providers.length !== 1 || !this.modelConfig) return;
    const providerId = providers[0].provider_id;
    for (const slot of MODEL_SLOTS) {
      const model = this.modelSlot(slot.key);
      if (model.provider && model.provider !== providerId) continue;
      if (this.providerConnected(model.provider)) continue;
      model.provider = providerId;
      model.name = "";
      model.api_base = "";
      model.kwargs = {};
    }
    this.activeModelProvider = providerId;
    this.models = this.activeProviderModels();
  },

  slotStatusLabel(key) {
    const slot = this.modelSlot(key);
    const currentProvider = this.modelSlotCurrentProviders[key] ?? slot.provider;
    if (this.isOauthProvider(currentProvider)) return "";
    return `Currently ${this.providerName(currentProvider)}`;
  },

  slotCanUseModels(key) {
    const providerId = this.modelSlot(key).provider;
    return this.isOauthProvider(providerId) && this.providerConnected(providerId);
  },

  activeProviderModels() {
    if (!this.providerConnected(this.activeModelProvider)) return [];
    return this.providerModels[this.activeModelProvider] || [];
  },

  modelMetadata(providerId, model) {
    return this.providerModelMetadata[providerId]?.[model] || {};
  },

  modelDescription(providerId, model) {
    return this.modelMetadata(providerId, model).description || "";
  },

  activeModelsDescription() {
    if (!this.providerConnected(this.activeModelProvider)) return "";
    return `Available models from ${this.providerLabel(this.activeModelProvider)}`;
  },

  markModelDirty(key) {
    this.modelConfigDirty = true;
    this.modelSlotDirty = { ...this.modelSlotDirty, [key]: true };
  },

  useProviderForSlot(key, providerId) {
    if (!this.providerConnected(providerId)) return;
    const slot = this.modelSlot(key);
    const previousProvider = slot.provider;
    slot.provider = providerId;
    slot.api_base = "";
    if (previousProvider && previousProvider !== providerId) {
      slot.name = "";
    }
    if (!slot.kwargs || typeof slot.kwargs !== "object") slot.kwargs = {};
    this.activeModelProvider = providerId;
    this.models = this.activeProviderModels();
    this.markModelDirty(key);
    if (this.models.length) {
      this.openModelDropdown(key);
    } else if (this.providerConnected(providerId)) {
      void this.loadModels({ providerId, openDropdown: key, silent: true });
    }
  },

  copyMainToUtility() {
    if (!this.modelConfig) return;
    const main = this.modelSlot("chat_model");
    const utility = this.modelSlot("utility_model");
    utility.provider = main.provider || "";
    utility.name = main.name || "";
    utility.api_base = main.api_base || "";
    utility.kwargs = clone(main.kwargs || {});
    this.activeModelProvider = utility.provider || this.activeModelProvider;
    this.models = this.activeProviderModels();
    this.markModelDirty("utility_model");
  },

  openModelDropdown(key, trigger = null) {
    if (!this.slotCanUseModels(key)) return;
    trigger?.scrollIntoView({ block: "center" });
    const providerId = this.modelSlot(key).provider;
    this.activeModelProvider = providerId;
    this.models = this.activeProviderModels();
    this.modelDropdown[key] = { ...this.modelDropdown[key], open: true };
    if (!this.models.length && !this.loadingModelsProvider && this.providerConnected(providerId)) {
      void this.loadModels({ providerId, openDropdown: key, silent: true });
    }
  },

  closeModelDropdown(key) {
    this.modelDropdown[key] = { ...this.modelDropdown[key], open: false };
  },

  filteredModels(key) {
    const slot = this.modelSlot(key);
    const query = String(slot.name || "").trim().toLowerCase();
    const models = this.providerModels[slot.provider] || [];
    const filtered = query
      ? models.filter((model) => String(model).toLowerCase().includes(query))
      : models;
    return filtered.slice(0, 80);
  },

  selectModel(key, model) {
    const slot = this.modelSlot(key);
    const providerId = slot.provider;
    if (!this.providerConnected(providerId)) return;
    slot.name = model;
    this.activeModelProvider = providerId;
    this.models = this.activeProviderModels();
    this.markModelDirty(key);
    this.closeModelDropdown(key);
  },

  validateModelConfig() {
    if (!this.modelConfigDirty) return;
    for (const slot of MODEL_SLOTS) {
      if (!this.modelSlotDirty[slot.key]) continue;
      const model = this.modelSlot(slot.key);
      if (this.isOauthProvider(model.provider) && !String(model.name || "").trim()) {
        throw new Error(`Choose a ${slot.title} before saving.`);
      }
    }
  },

  async saveModelConfigIfDirty() {
    if (!this.modelConfigDirty || !this.modelConfig) return;
    this.validateModelConfig();
    this.modelConfigSaving = true;
    try {
      const response = await fetchApi(`${MODEL_CONFIG_API}/model_config_set`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_name: "",
          agent_profile: "",
          config: this.modelConfig,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!data?.ok) throw new Error(data?.error || "Could not save model selection.");
      this.modelConfigDirty = false;
      this.modelSlotDirty = { chat_model: false, utility_model: false };
      await modelConfigStore.refreshModelsSummary?.();
    } finally {
      this.modelConfigSaving = false;
    }
  },

  notifyModelSetupChanged(providerId) {
    if (typeof document === "undefined") return;
    document.dispatchEvent(new CustomEvent("model-setup-changed", {
      detail: { source: "_oauth", providerId },
    }));
  },

  async handleProviderConnected(providerId, { statusLoaded = false } = {}) {
    if (!statusLoaded) await this.loadStatus();
    this.notifyModelSetupChanged(providerId);
  },

  async loadStatus() {
    if (this.loadingStatus) return;
    this.loadingStatus = true;
    try {
      const response = await callJsonApi(STATUS_API, {});
      this.status = response;
      for (const card of this.providerCards()) {
        const ui = this.providerUiFor(card.provider_id);
        if (card.enterprise_domain && !ui.enterprise_domain) {
          ui.enterprise_domain = card.enterprise_domain;
        }
        if (card.client_id && !ui.client_id) {
          ui.client_id = card.client_id;
        }
        if (card.quota_project_id && !ui.quota_project_id) {
          ui.quota_project_id = card.quota_project_id;
        }
      }
      if (!this.providerConnected(this.activeModelProvider)) {
        this.activeModelProvider = this.connectedProviderCards()[0]?.provider_id
          || this.providerCards()[0]?.provider_id
          || CODEX_PROVIDER;
        this.models = this.activeProviderModels();
      }
      if (!this.isOauthProvider(this.selectedProviderId)) {
        this.selectedProviderId = this.connectedProviderCards()[0]?.provider_id
          || this.providerCards()[0]?.provider_id
          || "";
      }
      this.applySoleConnectedProviderDefaults();
    } catch (error) {
      void toastFrontendError(messageOf(error), "OAuth Connections");
    } finally {
      this.loadingStatus = false;
    }
  },

  async connectProvider(providerId) {
    if (!this.isOauthProvider(providerId) || this.connectingProvider) return;
    this.connectingProvider = providerId;
    this.connecting = true;
    try {
      const payload = { provider_id: providerId };
      const status = this.providerStatus(providerId);
      const ui = this.providerUiFor(providerId);
      if (status.supports_enterprise_domain) {
        payload.enterprise_domain = ui.enterprise_domain || "";
      }
      if (status.supports_oauth_client_config) {
        payload.client_id = ui.client_id || this.geminiApi().client_id || "";
        payload.client_secret = ui.client_secret || this.geminiApi().client_secret || "";
      }
      if (status.supports_quota_project) {
        payload.quota_project_id = ui.quota_project_id || this.geminiApi().quota_project_id || "";
      }
      const response = await callJsonApi(START_LOGIN_API, payload);
      if (!response?.ok) {
        throw new Error(response?.error || `Could not start ${this.providerLabel(providerId)} sign-in.`);
      }

      this.devices = { ...this.devices, [providerId]: response };
      if (providerId === CODEX_PROVIDER) this.device = response;

      if (response.flow === "device_code" && response.verification_url && response.attempt_id) {
        window.open(response.verification_url, "_blank", "noopener,noreferrer");
        void toastFrontendInfo("Enter the code shown here in the opened browser tab.", "OAuth Connections");
        this.startPolling(providerId);
        return;
      }

      if (response.flow === "browser_pkce" && response.auth_url) {
        window.open(response.auth_url, "_blank", "noopener,noreferrer");
        void toastFrontendInfo("Finish sign-in in the opened browser tab.", "OAuth Connections");
        this.startCallbackPolling(providerId);
        return;
      }

      throw new Error(response?.error || `Could not start ${this.providerLabel(providerId)} sign-in.`);
    } catch (error) {
      this.clearProviderDevice(providerId);
      this.connectingProvider = "";
      this.connecting = false;
      void toastFrontendError(messageOf(error), "OAuth Connections");
    }
  },

  startPolling(providerId = CODEX_PROVIDER) {
    this.stopPolling(providerId);
    this.pollStartedAt = { ...this.pollStartedAt, [providerId]: Date.now() };
    const clearTimer = () => {
      if (this.pollTimers[providerId]) window.clearTimeout(this.pollTimers[providerId]);
      const timers = { ...this.pollTimers };
      delete timers[providerId];
      this.pollTimers = timers;
      if (providerId === CODEX_PROVIDER) this.pollTimer = null;
    };
    const schedule = (delayMs) => {
      clearTimer();
      this.pollTimers = { ...this.pollTimers, [providerId]: window.setTimeout(tick, delayMs) };
      if (providerId === CODEX_PROVIDER) this.pollTimer = this.pollTimers[providerId];
    };
    const tick = async () => {
      clearTimer();
      const device = this.devices[providerId];
      if (!device?.attempt_id) return;
      let nextDelay = Math.max(1500, Number(device.interval || 5) * 1000);
      try {
        const response = await callJsonApi(POLL_LOGIN_API, {
          provider_id: providerId,
          attempt_id: device.attempt_id,
        });
        if (!response?.ok) {
          if (response?.expired) {
            this.clearProviderDevice(providerId);
            this.stopPolling(providerId);
          }
          throw new Error(response?.error || `Could not finish ${this.providerLabel(providerId)} sign-in.`);
        }
        if (response.completed) {
          await this.handleProviderConnected(providerId);
          this.clearProviderDevice(providerId);
          this.stopPolling(providerId);
          if (this.connectingProvider === providerId) this.connectingProvider = "";
          this.connecting = Boolean(this.connectingProvider);
          void toastFrontendSuccess(`${this.providerLabel(providerId)} connected.`, "OAuth Connections");
          return;
        }
        if (response.interval || response.expires_at) {
          const updatedDevice = {
            ...device,
            interval: response.interval || device.interval,
            expires_at: response.expires_at || device.expires_at,
          };
          this.devices = { ...this.devices, [providerId]: updatedDevice };
          if (providerId === CODEX_PROVIDER) this.device = updatedDevice;
          nextDelay = Math.max(1500, Number(updatedDevice.interval || 5) * 1000);
        }
      } catch (error) {
        if (this.connectingProvider === providerId) this.connectingProvider = "";
        this.connecting = Boolean(this.connectingProvider);
        this.stopPolling(providerId);
        void toastFrontendError(messageOf(error), "OAuth Connections");
        return;
      }
      const expiresAt = Number(this.devices[providerId]?.expires_at || 0);
      const timedOut = expiresAt > 0
        ? Date.now() / 1000 > expiresAt
        : Date.now() - Number(this.pollStartedAt[providerId] || 0) > MAX_POLL_MS;
      if (timedOut) {
        if (this.connectingProvider === providerId) this.connectingProvider = "";
        this.connecting = Boolean(this.connectingProvider);
        this.clearProviderDevice(providerId);
        this.stopPolling(providerId);
        return;
      }
      schedule(nextDelay);
    };
    const initialDelay = Math.max(1500, Number(this.devices[providerId]?.interval || 5) * 1000);
    schedule(initialDelay);
  },

  pollProvider(providerId = CODEX_PROVIDER) {
    this.startPolling(providerId);
  },

  startCallbackPolling(providerId) {
    this.stopCallbackPolling(providerId);
    this.callbackPollStartedAt = { ...this.callbackPollStartedAt, [providerId]: Date.now() };
    const tick = async () => {
      await this.loadStatus();
      if (this.providerConnected(providerId)) {
        await this.handleProviderConnected(providerId, { statusLoaded: true });
        this.clearProviderDevice(providerId);
        this.stopCallbackPolling(providerId);
        if (this.connectingProvider === providerId) this.connectingProvider = "";
        this.connecting = Boolean(this.connectingProvider);
        void toastFrontendSuccess(`${this.providerLabel(providerId)} connected.`, "OAuth Connections");
        return;
      }
      if (Date.now() - Number(this.callbackPollStartedAt[providerId] || 0) > MAX_POLL_MS) {
        this.stopCallbackPolling(providerId);
        if (this.connectingProvider === providerId) this.connectingProvider = "";
        this.connecting = Boolean(this.connectingProvider);
      }
    };
    this.callbackPollTimers = {
      ...this.callbackPollTimers,
      [providerId]: window.setInterval(tick, 2500),
    };
    void tick();
  },

  stopPolling(providerId = "") {
    if (providerId) {
      if (this.pollTimers[providerId]) window.clearTimeout(this.pollTimers[providerId]);
      const timers = { ...this.pollTimers };
      delete timers[providerId];
      this.pollTimers = timers;
      const startedAt = { ...this.pollStartedAt };
      delete startedAt[providerId];
      this.pollStartedAt = startedAt;
      if (providerId === CODEX_PROVIDER) this.pollTimer = null;
      return;
    }

    for (const timer of Object.values(this.pollTimers || {})) {
      if (timer) window.clearTimeout(timer);
    }
    this.pollTimers = {};
    this.pollStartedAt = {};
    this.pollTimer = null;
  },

  stopCallbackPolling(providerId = "") {
    if (providerId) {
      if (this.callbackPollTimers[providerId]) window.clearInterval(this.callbackPollTimers[providerId]);
      const timers = { ...this.callbackPollTimers };
      delete timers[providerId];
      this.callbackPollTimers = timers;
      const startedAt = { ...this.callbackPollStartedAt };
      delete startedAt[providerId];
      this.callbackPollStartedAt = startedAt;
      return;
    }

    for (const timer of Object.values(this.callbackPollTimers || {})) {
      if (timer) window.clearInterval(timer);
    }
    this.callbackPollTimers = {};
    this.callbackPollStartedAt = {};
  },

  clearProviderDevice(providerId = "") {
    if (!providerId) {
      this.devices = {};
      this.device = null;
      return;
    }
    const devices = { ...this.devices };
    delete devices[providerId];
    this.devices = devices;
    if (providerId === CODEX_PROVIDER) this.device = null;
  },

  async submitManualCallback(providerId) {
    if (!this.isOauthProvider(providerId)) return;
    const callback = String(this.providerUiFor(providerId).manualCallback || "").trim();
    if (!callback) {
      void toastFrontendError("Paste callback URL, query string, or code.", "OAuth Connections");
      return;
    }
    this.connectingProvider = providerId;
    this.connecting = true;
    try {
      const response = await callJsonApi(MANUAL_CALLBACK_API, {
        provider_id: providerId,
        callback,
      });
      if (!response?.ok) {
        throw new Error(response?.error || `Could not finish ${this.providerLabel(providerId)} sign-in.`);
      }
      this.providerUiFor(providerId).manualCallback = "";
      this.clearProviderDevice(providerId);
      this.stopCallbackPolling(providerId);
      await this.handleProviderConnected(providerId);
      void toastFrontendSuccess(`${this.providerLabel(providerId)} connected.`, "OAuth Connections");
    } catch (error) {
      void toastFrontendError(messageOf(error), "OAuth Connections");
    } finally {
      if (this.connectingProvider === providerId) this.connectingProvider = "";
      this.connecting = Boolean(this.connectingProvider);
    }
  },

  async loadModels({ providerId = "", openDropdown = "", silent = false } = {}) {
    const selectedProvider = providerId || this.activeModelProvider || CODEX_PROVIDER;
    if (!this.isOauthProvider(selectedProvider) || this.loadingModelsProvider) return;
    this.loadingModelsProvider = selectedProvider;
    this.loadingModels = true;
    this.activeModelProvider = selectedProvider;
    try {
      const response = await callJsonApi(MODELS_API, { provider_id: selectedProvider });
      if (!response?.ok) {
        throw new Error(response?.error || `Could not load ${this.providerLabel(selectedProvider)} models.`);
      }
      const models = Array.isArray(response.models) ? response.models : [];
      const metadata = Array.isArray(response.model_metadata) ? response.model_metadata : [];
      const metadataMap = metadata.reduce((result, item) => {
        const key = String(item?.slug || item?.id || "");
        if (key) result[key] = item;
        return result;
      }, {});
      this.providerModels = { ...this.providerModels, [selectedProvider]: models };
      this.providerModelMetadata = { ...this.providerModelMetadata, [selectedProvider]: metadataMap };
      this.models = models;
      if (openDropdown) this.openModelDropdown(openDropdown);
      if (!silent) void toastFrontendSuccess(`${this.providerLabel(selectedProvider)} models loaded.`, "OAuth Connections");
    } catch (error) {
      this.providerModels = { ...this.providerModels, [selectedProvider]: [] };
      this.providerModelMetadata = { ...this.providerModelMetadata, [selectedProvider]: {} };
      this.models = [];
      if (!silent) void toastFrontendError(messageOf(error), "OAuth Connections");
    } finally {
      this.loadingModelsProvider = "";
      this.loadingModels = false;
    }
  },

  async disconnectProvider(providerId) {
    if (!this.isOauthProvider(providerId) || this.disconnectingProvider || !this.providerConnected(providerId)) return;
    const confirmed = window.confirm(`Disconnect ${this.providerLabel(providerId)} and remove stored OAuth tokens?`);
    if (!confirmed) return;

    this.disconnectingProvider = providerId;
    this.disconnecting = true;
    try {
      const response = await callJsonApi(DISCONNECT_API, { provider_id: providerId });
      if (!response?.ok) throw new Error(response?.error || "Could not disconnect the account.");
      if (response.provider) {
        const providerMap = { ...this.providerMap(), [providerId]: response.provider };
        this.status = { ...(this.status || {}), provider_map: providerMap, providers: Object.values(providerMap) };
        if (providerId === CODEX_PROVIDER) this.status.codex = response.provider;
      }
      const providerModels = { ...this.providerModels };
      delete providerModels[providerId];
      this.providerModels = providerModels;
      const providerModelMetadata = { ...this.providerModelMetadata };
      delete providerModelMetadata[providerId];
      this.providerModelMetadata = providerModelMetadata;
      if (this.activeModelProvider === providerId) this.models = [];
      this.clearProviderDevice(providerId);
      if (this.connectingProvider === providerId) this.connectingProvider = "";
      this.connecting = Boolean(this.connectingProvider);
      this.stopPolling(providerId);
      this.stopCallbackPolling(providerId);
      void toastFrontendSuccess(`${this.providerLabel(providerId)} disconnected.`, "OAuth Connections");
      await this.loadStatus();
    } catch (error) {
      void toastFrontendError(messageOf(error), "OAuth Connections");
    } finally {
      if (this.disconnectingProvider === providerId) this.disconnectingProvider = "";
      this.disconnecting = Boolean(this.disconnectingProvider);
    }
  },

  cancelConnect(providerId = "") {
    if (providerId) {
      this.stopPolling(providerId);
      this.stopCallbackPolling(providerId);
      this.clearProviderDevice(providerId);
      if (this.connectingProvider === providerId) this.connectingProvider = "";
    } else {
      this.stopPolling();
      this.stopCallbackPolling();
      this.clearProviderDevice();
      this.connectingProvider = "";
    }
    this.connecting = Boolean(this.connectingProvider);
  },
});
