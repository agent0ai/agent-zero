import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import {
  toastFrontendError,
  toastFrontendInfo,
  toastFrontendSuccess,
} from "/components/notifications/notification-store.js";

const STATUS_API = "/plugins/_oauth/status";
const START_DEVICE_LOGIN_API = "/plugins/_oauth/start_device_login";
const POLL_DEVICE_LOGIN_API = "/plugins/_oauth/poll_device_login";
const MODELS_API = "/plugins/_oauth/models";
const DISCONNECT_API = "/plugins/_oauth/disconnect";
const MAX_POLL_MS = 120000;

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
  return config;
}

function messageOf(error) {
  return error instanceof Error ? error.message : String(error);
}

export const store = createStore("oauthConfig", {
  config: null,
  status: null,
  loadingStatus: false,
  connecting: false,
  disconnecting: false,
  loadingModels: false,
  models: [],
  device: null,
  pollTimer: null,
  pollStartedAt: 0,

  async init(config) {
    this.bindConfig(config);
    await this.loadStatus();
  },

  cleanup() {
    this.stopPolling();
    this.config = null;
    this.status = null;
    this.models = [];
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

  connected() {
    return Boolean(this.status?.codex?.connected);
  },

  statusLabel() {
    if (this.loadingStatus) return "Checking";
    return this.connected() ? "Connected" : "Not connected";
  },

  usage() {
    return this.status?.codex?.usage || null;
  },

  usageWindows() {
    const usage = this.usage();
    if (!usage?.available) return [];
    return [
      { key: "primary", title: "Session", ...(usage.primary || {}) },
      { key: "secondary", title: "Week", ...(usage.secondary || {}) },
    ].filter((window) => Number.isFinite(this.remainingPercent(window)));
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

  endpointUrl() {
    const base = this.codex().proxy_base_path || "/oauth/codex";
    return `${window.location.origin}${base}/v1`;
  },

  callbackUrl() {
    const path = this.codex().callback_path || "/auth/callback";
    return `${window.location.origin}${path}`;
  },

  async loadStatus() {
    if (this.loadingStatus) return;
    this.loadingStatus = true;
    try {
      const response = await callJsonApi(STATUS_API, {});
      this.status = response;
    } catch (error) {
      void toastFrontendError(messageOf(error), "OAuth Connections");
    } finally {
      this.loadingStatus = false;
    }
  },

  async connectCodex() {
    if (this.connecting) return;
    this.connecting = true;
    try {
      const response = await callJsonApi(START_DEVICE_LOGIN_API, {});
      if (!response?.ok || !response.verification_url || !response.attempt_id) {
        throw new Error(response?.error || "Could not start Codex sign-in.");
      }
      this.device = response;
      window.open(response.verification_url, "_blank", "noopener,noreferrer");
      void toastFrontendInfo("Enter the code shown here in the opened browser tab.", "OAuth Connections");
      this.startPolling();
    } catch (error) {
      this.connecting = false;
      void toastFrontendError(messageOf(error), "OAuth Connections");
    }
  },

  startPolling() {
    this.stopPolling();
    this.pollStartedAt = Date.now();
    const tick = async () => {
      if (!this.device?.attempt_id) return;
      try {
        const response = await callJsonApi(POLL_DEVICE_LOGIN_API, {
          attempt_id: this.device.attempt_id,
        });
        if (!response?.ok) {
          if (response?.expired) {
            this.connecting = false;
            this.device = null;
            this.stopPolling();
          }
          throw new Error(response?.error || "Could not finish Codex sign-in.");
        }
        if (response.completed) {
          await this.loadStatus();
          this.device = null;
          this.connecting = false;
          this.stopPolling();
          void toastFrontendSuccess("Codex account connected.", "OAuth Connections");
          return;
        }
      } catch (error) {
        this.connecting = false;
        this.stopPolling();
        void toastFrontendError(messageOf(error), "OAuth Connections");
        return;
      }
      if (Date.now() - this.pollStartedAt > MAX_POLL_MS) {
        this.connecting = false;
        this.device = null;
        this.stopPolling();
        return;
      }
    };
    void tick();
    const delay = Math.max(1500, Number(this.device.interval || 5) * 1000);
    this.pollTimer = window.setInterval(tick, delay);
  },

  stopPolling() {
    if (this.pollTimer) window.clearInterval(this.pollTimer);
    this.pollTimer = null;
  },

  async loadModels() {
    if (this.loadingModels) return;
    this.loadingModels = true;
    try {
      const response = await callJsonApi(MODELS_API, {});
      if (!response?.ok) throw new Error(response?.error || "Could not load Codex models.");
      this.models = Array.isArray(response.models) ? response.models : [];
      void toastFrontendSuccess("Codex models loaded.", "OAuth Connections");
    } catch (error) {
      this.models = [];
      void toastFrontendError(messageOf(error), "OAuth Connections");
    } finally {
      this.loadingModels = false;
    }
  },

  async disconnectCodex() {
    if (this.disconnecting || !this.connected()) return;
    const confirmed = window.confirm("Disconnect this OpenAI account and remove stored OAuth tokens?");
    if (!confirmed) return;

    this.disconnecting = true;
    try {
      const response = await callJsonApi(DISCONNECT_API, {});
      if (!response?.ok) throw new Error(response?.error || "Could not disconnect the account.");
      this.status = response.codex ? { ok: true, codex: response.codex } : this.status;
      this.models = [];
      this.device = null;
      this.connecting = false;
      this.stopPolling();
      void toastFrontendSuccess("OpenAI account disconnected.", "OAuth Connections");
      await this.loadStatus();
    } catch (error) {
      void toastFrontendError(messageOf(error), "OAuth Connections");
    } finally {
      this.disconnecting = false;
    }
  },

  cancelConnect() {
    this.connecting = false;
    this.device = null;
    this.stopPolling();
  },
});
