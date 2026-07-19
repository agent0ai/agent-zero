import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import {
  toastFrontendError,
  toastFrontendInfo,
  toastFrontendSuccess,
} from "/components/notifications/notification-store.js";

const STATUS_API = "/plugins/_orchestrator/status";
const START_LOGIN_API = "/plugins/_orchestrator/start_device_login";
const POLL_LOGIN_API = "/plugins/_orchestrator/poll_device_login";
const DISCONNECT_API = "/plugins/_orchestrator/disconnect";
const TOAST_TITLE = "Orchestrator";
const MAX_POLL_MS = 15 * 60 * 1000;

export const store = createStore("orchestratorStore", {
  agents: [],
  loading: false,
  disconnectingAgent: "",
  login: null, // { agentId, userCode, verificationUrl }
  _pollTimer: null,
  _pollStartedAt: 0,

  async onOpen() {
    await this.refresh();
  },

  cleanup() {
    this._stopPolling();
    this.login = null;
  },

  async refresh() {
    this.loading = true;
    try {
      const data = await callJsonApi(STATUS_API, {});
      this.agents = Array.isArray(data?.agents) ? data.agents : [];
    } catch (error) {
      toastFrontendError(`Failed to load status: ${error}`, TOAST_TITLE);
    } finally {
      this.loading = false;
    }
  },

  ensureConfig(config, agent) {
    if (!config || !agent?.id) return;
    if (!config[agent.id]) config[agent.id] = {};
    const cfg = config[agent.id];
    if (!cfg.binary) cfg.binary = agent.id === "a0" ? "a0" : (agent.id === "cursor" ? "agent" : agent.id);
    if (agent.id === "codex" && cfg.bypass_sandbox === undefined) {
      cfg.bypass_sandbox = true;
    }
    if (agent.id === "claude") {
      if (!cfg.permission_mode) cfg.permission_mode = "bypassPermissions";
      if (!cfg.allowed_tools) cfg.allowed_tools = "Bash,Read,Edit";
      if (cfg.bare === undefined) cfg.bare = false;
    }
    if (agent.id === "cursor") {
      if (!cfg.binary) cfg.binary = "agent";
      if (!cfg.output_format) cfg.output_format = "text";
      if (cfg.force === undefined) cfg.force = true;
    }
    if (agent.id === "hermes" && cfg.yolo === undefined) {
      cfg.yolo = true;
    }
    if (agent.id === "grok") {
      if (!cfg.output_format) cfg.output_format = "json";
      if (cfg.always_approve === undefined) cfg.always_approve = true;
      if (cfg.no_auto_update === undefined) cfg.no_auto_update = true;
    }
    if (agent.id === "opencode" && cfg.auto === undefined) {
      cfg.auto = true;
    }
  },

  authText(agent) {
    if (!agent.installed) return "Install and sign in with the CLI, then refresh.";
    if (!agent.auth?.connected) return agent.auth?.error || "Not authenticated";
    if (agent.auth.mode === "plugin") return "Plugin-owned login";
    if (agent.auth.mode === "env") return "Environment API key";
    return "External CLI login";
  },

  async startLogin(agentId) {
    try {
      const data = await callJsonApi(START_LOGIN_API, { agent_id: agentId });
      if (!data?.ok) throw new Error(data?.error || "Unknown error");
      this.login = {
        agentId,
        userCode: data.user_code,
        verificationUrl: data.verification_url,
        deviceAuthId: data.device_auth_id,
      };
      toastFrontendInfo(
        "Enter the code on the verification page to connect.",
        TOAST_TITLE
      );
      this._startPolling(Math.max(3, Number(data.interval) || 5) * 1000);
    } catch (error) {
      toastFrontendError(`Could not start login: ${error}`, TOAST_TITLE);
    }
  },

  _startPolling(intervalMs) {
    this._stopPolling();
    this._pollStartedAt = Date.now();
    this._pollTimer = setInterval(() => this._poll(), intervalMs);
  },

  _stopPolling() {
    if (this._pollTimer) clearInterval(this._pollTimer);
    this._pollTimer = null;
  },

  async _poll() {
    if (!this.login) return this._stopPolling();
    if (Date.now() - this._pollStartedAt > MAX_POLL_MS) {
      this._stopPolling();
      this.login = null;
      toastFrontendError("Login timed out. Please try again.", TOAST_TITLE);
      return;
    }
    try {
      const data = await callJsonApi(POLL_LOGIN_API, {
        agent_id: this.login.agentId,
        device_auth_id: this.login.deviceAuthId,
        user_code: this.login.userCode,
      });
      if (!data?.ok) throw new Error(data?.error || "Unknown error");
      if (data.completed) {
        this._stopPolling();
        this.login = null;
        toastFrontendSuccess("Account connected successfully.", TOAST_TITLE);
        await this.refresh();
      }
    } catch (error) {
      this._stopPolling();
      this.login = null;
      toastFrontendError(`Login failed: ${error}`, TOAST_TITLE);
    }
  },

  cancelLogin() {
    this._stopPolling();
    this.login = null;
  },

  async disconnect(agentId) {
    if (this.disconnectingAgent) return;
    this.disconnectingAgent = agentId;
    try {
      const data = await callJsonApi(DISCONNECT_API, { agent_id: agentId });
      if (!data?.ok) throw new Error(data?.error || "Unknown error");
      if (data.removed) {
        toastFrontendSuccess("Disconnected.", TOAST_TITLE);
      } else {
        toastFrontendInfo(data.message || "No stored credentials removed.", TOAST_TITLE);
      }
      await this.refresh();
    } catch (error) {
      toastFrontendError(`Disconnect failed: ${error}`, TOAST_TITLE);
    } finally {
      this.disconnectingAgent = "";
    }
  },
});
