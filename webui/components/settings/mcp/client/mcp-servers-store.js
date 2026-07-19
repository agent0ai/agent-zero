import { createStore } from "/js/AlpineStore.js";
import { marked } from "/vendor/marked/marked.esm.js";
import sleep from "/js/sleep.js";
import * as API from "/js/api.js";
import { openModal } from "/js/modals.js";
import { store as settingsStore } from "/components/settings/settings-store.js";
import { getUserTimezone } from "/js/time-utils.js";
import {
  toastFrontendError,
  toastFrontendSuccess,
  toastFrontendWarning,
} from "/components/notifications/notification-store.js";

const EMPTY_CONFIG = '{\n  "mcpServers": {}\n}';
const STATUS_INTERVAL_MS = 3000;
const SCAN_ASSET_BASE = "/components/settings/mcp/client";
const SCAN_POLL_INTERVAL_MS = 2000;
const SCAN_MAX_POLL_MS = 10 * 60 * 1000;
const SCAN_TITLE = "MCP Scanner";

let scanChecksConfig = null;
let scanPromptTemplate = null;
let scanPollGeneration = 0;

async function fetchText(url, label) {
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`Failed to load ${label}: ${response.status} ${response.statusText}${body ? ` - ${body}` : ""}`);
  }
  return response.text();
}

async function fetchJson(url, label) {
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`Failed to load ${label}: ${response.status} ${response.statusText}${body ? ` - ${body}` : ""}`);
  }
  return response.json();
}

async function loadScanChecks() {
  if (scanChecksConfig) return scanChecksConfig;
  scanChecksConfig = await fetchJson(`${SCAN_ASSET_BASE}/mcp-scan-checks.json`, "MCP scan checks");
  return scanChecksConfig;
}

async function loadScanTemplate() {
  if (scanPromptTemplate) return scanPromptTemplate;
  scanPromptTemplate = await fetchText(`${SCAN_ASSET_BASE}/mcp-scan-prompt.md`, "MCP scan prompt");
  return scanPromptTemplate;
}

function normalizeName(value) {
  return String(value || "mcp_server")
    .trim()
    .toLowerCase()
    .replace(/[^\w]/gu, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "") || "mcp_server";
}

function parseJsonConfig(value) {
  const text = String(value || "").trim() || EMPTY_CONFIG;
  const parsed = JSON.parse(text);
  if (Array.isArray(parsed)) return { mcpServers: parsed };
  if (parsed && typeof parsed === "object") {
    if (!parsed.mcpServers) parsed.mcpServers = {};
    return parsed;
  }
  return { mcpServers: {} };
}

function stringifyConfig(config) {
  return JSON.stringify(config || { mcpServers: {} }, null, 2);
}

function matchesSearchQuery(query, values) {
  const normalized = String(query || "").trim().toLowerCase();
  if (!normalized) return true;
  return values.some((value) => String(value ?? "").toLowerCase().includes(normalized));
}

function parseKeyValueText(text) {
  const raw = String(text || "").trim();
  if (!raw) return {};
  if (raw.startsWith("{")) {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  }

  return raw.split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .reduce((acc, line) => {
      const idx = line.indexOf("=");
      if (idx <= 0) return acc;
      const key = line.slice(0, idx).trim();
      if (!key) return acc;
      acc[key] = line.slice(idx + 1).trim();
      return acc;
    }, {});
}

function formatKeyValueText(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return "";
  return Object.entries(value)
    .map(([key, val]) => `${key}=${val ?? ""}`)
    .join("\n");
}

function parseArgsText(text) {
  const raw = String(text || "").trim();
  if (!raw) return [];
  if (raw.startsWith("[")) {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map((item) => String(item)) : [];
  }
  return raw.split(/\r?\n/).flatMap((line) => splitCommandLine(line.trim())).filter(Boolean);
}

function formatArgsText(value) {
  return Array.isArray(value) ? value.join("\n") : "";
}

function splitCommandLine(text) {
  const raw = String(text || "").trim();
  if (!raw) return [];

  const tokens = [];
  let current = "";
  let quote = "";
  let escaping = false;

  for (const char of raw) {
    if (escaping) {
      current += char;
      escaping = false;
      continue;
    }
    if (char === "\\") {
      escaping = true;
      continue;
    }
    if (quote) {
      if (char === quote) quote = "";
      else current += char;
      continue;
    }
    if (char === "\"" || char === "'") {
      quote = char;
      continue;
    }
    if (/\s/u.test(char)) {
      if (current) {
        tokens.push(current);
        current = "";
      }
      continue;
    }
    current += char;
  }

  if (escaping) current += "\\";
  if (current) tokens.push(current);
  return tokens;
}

function getLocalCommandParts(form) {
  const commandLine = String(form.command || "").trim();
  const explicitArgs = parseArgsText(form.argsText);
  if (explicitArgs.length) return { command: commandLine, args: explicitArgs };

  const parts = splitCommandLine(commandLine);
  return {
    command: parts[0] || commandLine,
    args: parts.slice(1),
  };
}

function deriveNameFromUrl(url) {
  try {
    const parsed = new URL(url);
    const parts = parsed.pathname.split("/").filter(Boolean);
    return normalizeName(parts.at(-1) || parsed.hostname || "remote_mcp");
  } catch {
    return "remote_mcp";
  }
}

function deriveNameFromCommand(command, argsText) {
  let args = [];
  try {
    args = parseArgsText(argsText);
  } catch {}

  const parts = args.length
    ? [String(command || "").trim(), ...args]
    : splitCommandLine(command);
  const ignored = new Set(["npx", "uvx", "uv", "node", "python", "python3"]);
  const candidate = [...parts]
    .reverse()
    .find((part) => part && !part.startsWith("-") && !ignored.has(part.toLowerCase()));
  return normalizeName(candidate || parts[0] || "local_mcp");
}

function formatCriteria(ratings, criteria) {
  return Object.entries(criteria || {})
    .map(([level, desc]) => `- ${ratings[level]?.icon || level}: ${desc}`)
    .join("\n");
}

function formatStatusLegend(ratings) {
  return Object.values(ratings || {})
    .map((rating) => `- ${rating.icon} ${rating.label}`)
    .join("\n");
}

function formatRatingIcons(ratings) {
  return Object.values(ratings || {}).map((rating) => rating.icon).join("/");
}

function createDefaultScanOptions() {
  return {
    inspectRuntime: true,
    allowLocalExecution: false,
    allowRemoteNetwork: false,
  };
}

function createEmptyForm() {
  return {
    mode: "local",
    name: "",
    description: "",
    url: "",
    type: "streamable-http",
    command: "",
    argsText: "",
    headersText: "",
    envText: "",
    init_timeout: "",
    tool_timeout: "",
    verify: true,
    disabled: false,
  };
}

const model = {
  editor: null,
  servers: [],
  loading: true,
  applying: false,
  statusCheck: false,
  serverLog: "",
  serverDetail: null,
  serverSearch: "",
  toolSearch: "",
  activeView: "visual",
  advancedOpen: false,
  serverForm: createEmptyForm(),
  scanChecks: {},
  scanChecksMeta: {},
  scanOptions: createDefaultScanOptions(),
  scanPrompt: "",
  scanOutput: "",
  scanCtxId: "",
  scanTargetJson: "",
  scanServer: null,
  agentScanning: false,
  scanLoading: false,
  scanResult: null,
  scope: "global",
  projectName: "",
  projectModel: null,
  standaloneProject: false,

  async initialize() {
    this.loading = true;
    await this.ensureScopeLoaded();
    this.setupEditor();
    await this.loadStatus();
    this.loading = false;
    this.startStatusCheck();
  },

  setupEditor() {
    const container = document.getElementById("mcp-servers-config-json");
    if (!container) return;

    const editor = ace.edit("mcp-servers-config-json");
    const dark = localStorage.getItem("darkMode");
    editor.setTheme(dark !== "false" ? "ace/theme/github_dark" : "ace/theme/tomorrow");
    editor.session.setMode("ace/mode/json");
    editor.setValue(this.getScopeConfigJson());
    editor.clearSelection();
    this.editor = editor;
    requestAnimationFrame(() => this.editor?.resize());
  },

  async ensureScopeLoaded() {
    if (this.scope === "project") return;
    if (settingsStore.settings) return;

    try {
      const response = await API.callJsonApi("settings_get", null);
      if (response?.settings) {
        settingsStore.settings = response.settings;
        settingsStore.additional = response.additional || null;
      }
    } catch (error) {
      console.error("Failed to load settings for MCP manager:", error);
      void toastFrontendError("Failed to load settings for MCP manager", "MCP Servers");
    }
  },

  async openGlobalConfig() {
    this.configureGlobalScope();
    await openModal("settings/mcp/client/mcp-servers.html");
  },

  async openProjectConfig(projectModel) {
    if (!projectModel?.name) return;
    this.configureProjectScope(projectModel.name, projectModel, false);
    await openModal("settings/mcp/client/mcp-servers.html");
  },

  async openFromComposer(projectName = "") {
    const normalizedProject = String(projectName || "").trim();
    if (normalizedProject) {
      try {
        const response = await API.callJsonApi("projects", {
          action: "load",
          name: normalizedProject,
        });
        if (!response?.ok) throw new Error(response?.error || "Project load failed");
        this.configureProjectScope(normalizedProject, response.data, true);
      } catch (error) {
        console.error("Failed to load project MCP config:", error);
        void toastFrontendError("Failed to load project MCP config", "MCP Servers");
        return;
      }
    } else {
      this.configureGlobalScope();
      await this.ensureScopeLoaded();
    }
    await openModal("settings/mcp/client/mcp-servers.html");
  },

  configureGlobalScope() {
    this.scope = "global";
    this.projectName = "";
    this.projectModel = null;
    this.standaloneProject = false;
  },

  configureProjectScope(projectName, projectModel, standaloneProject = false) {
    this.scope = "project";
    this.projectName = projectName;
    this.projectModel = projectModel || null;
    this.standaloneProject = !!standaloneProject;
  },

  resetScope() {
    this.configureGlobalScope();
  },

  get scopeTitle() {
    if (this.scope === "project") return `Project MCP servers`;
    return "Global MCP servers";
  },

  get scopeSubtitle() {
    if (this.scope === "project") {
      return this.projectName ? `Project: ${this.projectName}` : "Project scope";
    }
    return "Available to every chat unless a project overrides a server.";
  },

  getStatusPayload() {
    return this.scope === "project" && this.projectName
      ? { project_name: this.projectName }
      : null;
  },

  getApplyPayload() {
    const payload = { mcp_servers: this.getEditorValue() };
    if (this.scope === "project" && this.projectName) payload.project_name = this.projectName;
    return payload;
  },

  getScopeConfigJson() {
    if (this.scope === "project") {
      return this.projectModel?.mcp_servers || EMPTY_CONFIG;
    }
    return settingsStore.settings?.mcp_servers
      ?? settingsStore.settings?.mcpServers
      ?? EMPTY_CONFIG;
  },

  setScopeConfigJson(value) {
    if (this.scope === "project") {
      if (this.projectModel) this.projectModel.mcp_servers = value;
      return;
    }
    if (settingsStore.settings) settingsStore.settings.mcp_servers = value;
  },

  getEditorValue() {
    return this.editor?.getValue() ?? this.getScopeConfigJson();
  },

  setEditorValue(value) {
    if (this.editor) {
      this.editor.setValue(value);
      this.editor.clearSelection();
      this.editor.navigateFileStart();
      requestAnimationFrame(() => this.editor?.resize());
    }
    this.setScopeConfigJson(value);
  },

  getConfigObject() {
    return parseJsonConfig(this.getEditorValue());
  },

  get configuredServers() {
    try {
      const config = this.getConfigObject();
      const servers = config.mcpServers;
      if (Array.isArray(servers)) {
        return servers.map((server, index) => ({
          name: server?.name || `server_${index + 1}`,
          config: server || {},
        }));
      }
      if (servers && typeof servers === "object") {
        return Object.entries(servers).map(([name, config]) => ({
          name,
          config: config || {},
        }));
      }
    } catch {
      return [];
    }
    return [];
  },

  get filteredConfiguredServers() {
    return this.configuredServers.filter((entry) => matchesSearchQuery(this.serverSearch, [
      entry.name,
      this.configModeLabel(entry.config),
      this.configSummary(entry.config),
      entry.config?.description,
    ]));
  },

  get filteredServers() {
    return this.servers.filter((server) => matchesSearchQuery(this.serverSearch, [
      server.name,
      server.scope,
      server.type,
      server.description,
      server.error,
      this.statusLabel(server),
    ]));
  },

  get serverSearchActive() {
    return !!String(this.serverSearch || "").trim();
  },

  get configuredServersCountLabel() {
    const total = this.configuredServers.length;
    if (!this.serverSearchActive) return `${total} total`;
    return `${this.filteredConfiguredServers.length} of ${total}`;
  },

  get visibleServersCountLabel() {
    if (this.loading) return "Loading";
    const total = this.servers.length;
    if (!this.serverSearchActive) return `${total} visible`;
    return `${this.filteredServers.length} of ${total}`;
  },

  clearServerSearch() {
    this.serverSearch = "";
  },

  get serverDetailTools() {
    return Array.isArray(this.serverDetail?.tools) ? this.serverDetail.tools : [];
  },

  get filteredServerDetailTools() {
    return this.serverDetailTools.filter((tool) => matchesSearchQuery(this.toolSearch, [
      tool.name,
      tool.description,
      JSON.stringify(tool.input_schema || {}),
    ]));
  },

  get serverDetailToolsCountLabel() {
    const total = this.serverDetailTools.length;
    const query = String(this.toolSearch || "").trim();
    if (!query) return `${total} tools`;
    return `${this.filteredServerDetailTools.length} of ${total}`;
  },

  clearToolSearch() {
    this.toolSearch = "";
  },

  countServersInConfig(configText) {
    try {
      const config = parseJsonConfig(configText || EMPTY_CONFIG);
      if (Array.isArray(config.mcpServers)) return config.mcpServers.length;
      return Object.keys(config.mcpServers || {}).length;
    } catch {
      return 0;
    }
  },

  formatJson() {
    try {
      this.setEditorValue(stringifyConfig(this.getConfigObject()));
      void toastFrontendSuccess("MCP JSON reformatted", "MCP Servers");
    } catch (error) {
      console.error("Failed to format JSON:", error);
      void toastFrontendError(`Invalid JSON: ${error.message}`, "MCP Servers");
    }
  },

  setActiveView(view) {
    this.activeView = view || "visual";
    if (this.activeView === "raw") {
      requestAnimationFrame(() => this.editor?.resize());
    }
  },

  setFormMode(mode) {
    this.serverForm.mode = mode === "local" ? "local" : "remote";
    this.scanResult = null;
  },

  resetForm() {
    this.serverForm = createEmptyForm();
    this.advancedOpen = false;
    this.scanResult = null;
  },

  buildServerFromForm() {
    const form = this.serverForm;
    const name = normalizeName(form.name || (form.mode === "remote" ? deriveNameFromUrl(form.url) : deriveNameFromCommand(form.command, form.argsText)));
    if (!name) throw new Error("Name is required");

    const server = {
      name,
      disabled: !!form.disabled,
    };

    if (form.description.trim()) server.description = form.description.trim();

    if (form.init_timeout !== "" && form.init_timeout !== null) {
      const timeout = Number(form.init_timeout);
      if (Number.isFinite(timeout) && timeout > 0) server.init_timeout = timeout;
    }
    if (form.tool_timeout !== "" && form.tool_timeout !== null) {
      const timeout = Number(form.tool_timeout);
      if (Number.isFinite(timeout) && timeout > 0) server.tool_timeout = timeout;
    }

    if (form.mode === "remote") {
      if (!form.url.trim()) throw new Error("Remote MCP server URL is required");
      server.url = form.url.trim();
      server.type = form.type || "streamable-http";
      server.verify = form.verify !== false;
      const headers = parseKeyValueText(form.headersText);
      if (Object.keys(headers).length) server.headers = headers;
    } else {
      if (!form.command.trim()) throw new Error("Local command is required");
      const parts = getLocalCommandParts(form);
      if (!parts.command) throw new Error("Local command is required");
      server.type = "stdio";
      server.command = parts.command;
      if (parts.args.length) server.args = parts.args;
      const env = parseKeyValueText(form.envText);
      if (Object.keys(env).length) server.env = env;
    }

    return server;
  },

  async ensureScanFramework() {
    try {
      const cfg = await loadScanChecks();
      this.scanChecksMeta = cfg.checks || {};
      if (Object.keys(this.scanChecks).length === 0) {
        const checks = {};
        for (const key of Object.keys(this.scanChecksMeta)) checks[key] = true;
        this.scanChecks = checks;
      }
      return cfg;
    } catch (error) {
      console.error("Failed to load MCP scanner framework:", error);
      void toastFrontendError(`Failed to load MCP scanner: ${error.message || error}`, SCAN_TITLE);
      return null;
    }
  },

  resetScanState() {
    scanPollGeneration++;
    this.scanOptions = createDefaultScanOptions();
    this.scanPrompt = "";
    this.scanOutput = "";
    this.scanCtxId = "";
    this.scanTargetJson = "";
    this.scanServer = null;
    this.agentScanning = false;
    this.scanLoading = false;
    this.scanResult = null;
  },

  prepareScanTarget() {
    let server;
    try {
      server = this.buildServerFromForm();
    } catch (error) {
      void toastFrontendError(error.message || String(error), SCAN_TITLE);
      return false;
    }

    this.scanServer = server;
    this.scanTargetJson = JSON.stringify(server, null, 2);
    this.scanResult = null;
    this.scanOutput = "";
    this.scanCtxId = "";
    return true;
  },

  async openScanModal() {
    if (!this.prepareScanTarget()) return;
    await this.ensureScanFramework();
    await this.buildScanPrompt();
    await openModal("settings/mcp/client/mcp-server-scan.html");
  },

  async onScanModalOpen() {
    await this.ensureScanFramework();
    if (!this.scanServer) this.prepareScanTarget();
    await this.buildScanPrompt();
  },

  async buildScanPrompt() {
    if (!this.scanServer) return;
    try {
      const [cfg, template] = await Promise.all([loadScanChecks(), loadScanTemplate()]);
      const ratings = cfg.ratings || {};
      const checks = cfg.checks || {};
      const selected = Object.entries(this.scanChecks)
        .filter(([, enabled]) => enabled)
        .map(([key]) => checks[key])
        .filter(Boolean);

      const inspectionSummary = this.scanResult
        ? JSON.stringify({
          risk_level: this.scanResult.risk_level,
          warnings: this.scanResult.warnings || [],
          inspected_tools: this.scanResult.inspected_tools || [],
        }, null, 2)
        : "No deterministic config inspection has been run in this modal yet.";

      let prompt = template;
      prompt = prompt.replace(/\{\{SERVER_JSON\}\}/g, this.scanTargetJson || JSON.stringify(this.scanServer, null, 2));
      prompt = prompt.replace(/\{\{CONFIG_SCOPE\}\}/g, this.scope === "project" && this.projectName ? `project: ${this.projectName}` : "global draft");
      prompt = prompt.replace(/\{\{RUNTIME_INSPECTION\}\}/g, this.scanOptions.inspectRuntime ? "requested" : "not requested");
      prompt = prompt.replace(/\{\{ALLOW_LOCAL_EXECUTION\}\}/g, this.scanOptions.allowLocalExecution ? "yes" : "no");
      prompt = prompt.replace(/\{\{ALLOW_REMOTE_NETWORK\}\}/g, this.scanOptions.allowRemoteNetwork ? "yes" : "no");
      prompt = prompt.replace(/\{\{INSPECTION_SUMMARY\}\}/g, inspectionSummary);
      prompt = prompt.replace(
        /\{\{SELECTED_CHECKS\}\}/g,
        selected.length ? selected.map((check) => `- ${check.label}`).join("\n") : "- (no checks selected)",
      );
      prompt = prompt.replace(
        /\{\{CHECK_DETAILS\}\}/g,
        selected.length
          ? selected.map((check) => `**${check.label}**: ${check.detail}\n${formatCriteria(ratings, check.criteria)}`).join("\n\n")
          : "(no checks selected)",
      );
      prompt = prompt.replace(/\{\{STATUS_LEGEND\}\}/g, formatStatusLegend(ratings));
      prompt = prompt.replace(/\{\{RATING_ICONS\}\}/g, formatRatingIcons(ratings));
      prompt = prompt.replace(/\{\{RATING_PASS\}\}/g, ratings.pass?.icon || "PASS");
      prompt = prompt.replace(/\{\{RATING_WARNING\}\}/g, ratings.warning?.icon || "WARN");
      prompt = prompt.replace(/\{\{RATING_FAIL\}\}/g, ratings.fail?.icon || "FAIL");
      this.scanPrompt = prompt;
    } catch (error) {
      console.error("Failed to build MCP scan prompt:", error);
      void toastFrontendError(`Failed to build scan prompt: ${error.message || error}`, SCAN_TITLE);
    }
  },

  async runConfigInspection() {
    if (!this.scanServer && !this.prepareScanTarget()) return;
    this.scanLoading = true;
    this.scanResult = null;
    try {
      const response = await API.callJsonApi("mcp_server_scan", {
        server: this.scanServer,
        inspect_runtime: !!this.scanOptions.inspectRuntime,
        allow_local_execution: !!this.scanOptions.allowLocalExecution,
        allow_remote_network: !!this.scanOptions.allowRemoteNetwork,
      });
      if (!response?.success) throw new Error(response?.error || "Scan failed");
      this.scanResult = response;
      await this.buildScanPrompt();
    } catch (error) {
      console.error("MCP scan failed:", error);
      void toastFrontendError(`MCP scan failed: ${error.message || error}`, SCAN_TITLE);
    } finally {
      this.scanLoading = false;
    }
  },

  async copyScanPrompt() {
    try {
      await navigator.clipboard.writeText(this.scanPrompt || "");
    } catch {
      void toastFrontendError("Failed to copy the scan prompt", SCAN_TITLE);
    }
  },

  async runAgentScan() {
    if (this.agentScanning) return;
    if (!this.scanServer && !this.prepareScanTarget()) return;
    await this.buildScanPrompt();

    const prompt = String(this.scanPrompt || "").trim();
    if (!prompt) {
      void toastFrontendError("Scan prompt is empty", SCAN_TITLE);
      return;
    }

    const gen = ++scanPollGeneration;
    this.scanOutput = "";

    let ctxId = "";
    try {
      const resp = await API.callJsonApi("/chat_create", {});
      if (!resp?.ok || !resp.ctxid) throw new Error(resp?.message || "Failed to create scan chat");
      ctxId = resp.ctxid;
      this.scanCtxId = ctxId;
      await API.callJsonApi("/message_queue_add", { context: ctxId, text: prompt });
      this.agentScanning = true;
      await API.callJsonApi("/message_queue_send", { context: ctxId });
      void this.pollAgentScan(gen, ctxId);
    } catch (error) {
      this.agentScanning = false;
      console.error("MCP agent scan failed:", error);
      void toastFrontendError(`Scan failed: ${error.message || error}`, SCAN_TITLE);
    }
  },

  async pollAgentScan(gen, ctxId) {
    let started = false;
    const deadline = Date.now() + SCAN_MAX_POLL_MS;
    while (gen === scanPollGeneration) {
      if (Date.now() >= deadline) {
        this.agentScanning = false;
        void toastFrontendError("Scan timed out while waiting for Agent Zero", SCAN_TITLE);
        return;
      }
      await sleep(SCAN_POLL_INTERVAL_MS);
      try {
        const snap = await API.callJsonApi("/poll", {
          context: ctxId,
          log_from: 0,
          notifications_from: 0,
          timezone: getUserTimezone(),
        });

        if (snap.logs?.length) {
          const last = snap.logs
            .filter((log) => log.type === "response" && log.no > 0)
            .pop();
          if (last) this.scanOutput = last.content || "";
        }

        if (snap.log_progress_active) started = true;
        if (started && !snap.log_progress_active) {
          this.agentScanning = false;
          return;
        }
        if (snap.deselect_chat) return;
      } catch (error) {
        if (gen === scanPollGeneration) console.error("MCP scan poll error:", error);
      }
    }
  },

  openScanChatInNewWindow() {
    if (!this.scanCtxId) return;
    const url = new URL(window.location.href);
    url.searchParams.set("ctxid", this.scanCtxId);
    window.open(url.toString(), "_blank");
  },

  scanCleanup() {
    scanPollGeneration++;
    this.agentScanning = false;
  },

  addServerFromForm() {
    let server;
    try {
      server = this.buildServerFromForm();
    } catch (error) {
      void toastFrontendError(error.message || String(error), "MCP Servers");
      return;
    }

    try {
      const config = this.getConfigObject();
      if (Array.isArray(config.mcpServers)) {
        const index = config.mcpServers.findIndex((item) => normalizeName(item?.name || "") === server.name);
        if (index >= 0) config.mcpServers.splice(index, 1, server);
        else config.mcpServers.push(server);
      } else {
        const stored = { ...server };
        delete stored.name;
        config.mcpServers[server.name] = stored;
      }
      this.setEditorValue(stringifyConfig(config));
      this.resetForm();
      void toastFrontendSuccess("MCP server added to draft config", "MCP Servers");
      requestAnimationFrame(() => globalThis.scrollModal?.("mcp-configured-servers"));
    } catch (error) {
      console.error("Failed to add MCP server:", error);
      void toastFrontendError(`Failed to add MCP server: ${error.message || error}`, "MCP Servers");
    }
  },

  editConfigServer(name) {
    const entry = this.configuredServers.find((item) => item.name === name);
    if (!entry) return;
    const cfg = entry.config || {};
    const isRemote = !!(cfg.url || cfg.serverUrl);
    this.serverForm = {
      ...createEmptyForm(),
      mode: isRemote ? "remote" : "local",
      name,
      description: cfg.description || "",
      url: cfg.url || cfg.serverUrl || "",
      type: cfg.type || "streamable-http",
      command: cfg.command || "",
      argsText: formatArgsText(cfg.args),
      headersText: formatKeyValueText(cfg.headers),
      envText: formatKeyValueText(cfg.env),
      init_timeout: cfg.init_timeout || "",
      tool_timeout: cfg.tool_timeout || "",
      verify: cfg.verify !== false,
      disabled: !!cfg.disabled,
    };
    this.activeView = "visual";
    this.scanResult = null;
    requestAnimationFrame(() => globalThis.scrollModal?.("mcp-add-server"));
  },

  async removeConfigServer(name) {
    try {
      const config = this.getConfigObject();
      const normalized = normalizeName(name);
      let removed = false;

      if (Array.isArray(config.mcpServers)) {
        const nextServers = config.mcpServers.filter((server) => normalizeName(server?.name || "") !== normalized);
        removed = nextServers.length !== config.mcpServers.length;
        config.mcpServers = nextServers;
      } else if (config.mcpServers && typeof config.mcpServers === "object") {
        const key = Object.keys(config.mcpServers).find((serverName) => normalizeName(serverName) === normalized);
        if (key) {
          delete config.mcpServers[key];
          removed = true;
        }
      }

      if (!removed) {
        void toastFrontendWarning("MCP server is no longer in this config.", "MCP Servers");
        await this.loadStatus({ silent: true });
        return;
      }

      this.setEditorValue(stringifyConfig(config));
      if (normalizeName(this.serverForm.name) === normalized) this.resetForm();
      await this.applyNow({ successMessage: "MCP server removed" });
    } catch (error) {
      void toastFrontendError(`Failed to remove MCP server: ${error.message || error}`, "MCP Servers");
    }
  },

  toggleConfigServer(name) {
    try {
      const config = this.getConfigObject();
      if (Array.isArray(config.mcpServers)) {
        const server = config.mcpServers.find((item) => normalizeName(item?.name || "") === normalizeName(name));
        if (server) server.disabled = !server.disabled;
      } else if (config.mcpServers[name]) {
        config.mcpServers[name].disabled = !config.mcpServers[name].disabled;
      }
      this.setEditorValue(stringifyConfig(config));
    } catch (error) {
      void toastFrontendError(`Failed to update MCP server: ${error.message || error}`, "MCP Servers");
    }
  },

  getServerConfigRef(config, name) {
    const normalized = normalizeName(name);
    if (Array.isArray(config.mcpServers)) {
      const server = config.mcpServers.find((item) => normalizeName(item?.name || "") === normalized);
      return server ? { server } : null;
    }
    if (config.mcpServers && typeof config.mcpServers === "object") {
      const key = Object.keys(config.mcpServers).find((serverName) => normalizeName(serverName) === normalized);
      if (key) return { server: config.mcpServers[key] };
    }
    return null;
  },

  getDisabledToolsForServer(name) {
    try {
      const ref = this.getServerConfigRef(this.getConfigObject(), name);
      const disabled = ref?.server?.disabled_tools;
      return Array.isArray(disabled) ? disabled.map((toolName) => String(toolName)) : [];
    } catch {
      return [];
    }
  },

  canConfigureServerTools(name) {
    try {
      return !!this.getServerConfigRef(this.getConfigObject(), name);
    } catch {
      return false;
    }
  },

  isServerToolEnabled(serverName, toolName) {
    const disabled = this.getDisabledToolsForServer(serverName);
    return !disabled.includes(String(toolName || ""));
  },

  toggleServerTool(serverName, toolName, enabled) {
    const normalizedTool = String(toolName || "").trim();
    if (!serverName || !normalizedTool) return;

    try {
      const config = this.getConfigObject();
      const ref = this.getServerConfigRef(config, serverName);
      if (!ref?.server) {
        void toastFrontendWarning("Add this inherited server to the current config before changing its tools.", "MCP Servers");
        return;
      }

      const disabled = Array.isArray(ref.server.disabled_tools)
        ? ref.server.disabled_tools.map((item) => String(item)).filter(Boolean)
        : [];
      const nextDisabled = new Set(disabled);
      if (enabled) nextDisabled.delete(normalizedTool);
      else nextDisabled.add(normalizedTool);

      const disabledTools = [...nextDisabled].sort((a, b) => a.localeCompare(b));
      if (disabledTools.length) ref.server.disabled_tools = disabledTools;
      else delete ref.server.disabled_tools;

      this.setEditorValue(stringifyConfig(config));
      if (this.serverDetail?.name === serverName && Array.isArray(this.serverDetail.tools)) {
        this.serverDetail.tools = this.serverDetail.tools.map((tool) => (
          tool.name === normalizedTool
            ? { ...tool, disabled: !enabled }
            : tool
        ));
      }
    } catch (error) {
      void toastFrontendError(`Failed to update MCP tool: ${error.message || error}`, "MCP Servers");
    }
  },

  async startStatusCheck() {
    this.statusCheck = true;
    while (this.statusCheck) {
      await sleep(STATUS_INTERVAL_MS);
      if (this.statusCheck) await this.loadStatus({ silent: true });
    }
  },

  async loadStatus(options = {}) {
    try {
      const resp = await API.callJsonApi("mcp_servers_status", this.getStatusPayload());
      if (resp?.success) {
        this.servers = resp.status || [];
        this.servers.sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
      } else if (!options.silent) {
        void toastFrontendWarning(resp?.error || "Unable to load MCP status", "MCP Servers");
      }
    } catch (error) {
      if (!options.silent) {
        console.error("Failed to load MCP status:", error);
        void toastFrontendError("Failed to load MCP status", "MCP Servers");
      }
    }
  },

  stopStatusCheck() {
    this.statusCheck = false;
  },

  async applyNow(options = {}) {
    if (this.applying) return;
    try {
      const formatted = stringifyConfig(this.getConfigObject());
      this.setEditorValue(formatted);
    } catch (error) {
      void toastFrontendError(`Invalid JSON: ${error.message || error}`, "MCP Servers");
      return;
    }

    this.applying = true;
    try {
      const resp = await API.callJsonApi("mcp_servers_apply", this.getApplyPayload());
      if (!resp?.success) throw new Error(resp?.error || "Apply failed");
      this.setScopeConfigJson(resp.mcp_servers || this.getEditorValue());
      this.servers = resp.status || [];
      this.servers.sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
      if (options.successMessage !== false) {
        void toastFrontendSuccess(options.successMessage || "MCP servers applied", "MCP Servers");
      }
      await sleep(100);
      if (options.scrollToStatus !== false && globalThis.scrollModal) {
        globalThis.scrollModal("mcp-servers-status");
      }
    } catch (error) {
      console.error("Failed to apply MCP servers:", error);
      void toastFrontendError(`Failed to apply MCP servers: ${error.message || error}`, "MCP Servers");
    } finally {
      this.applying = false;
    }
  },

  async getServerLog(serverName) {
    this.serverLog = "";
    const payload = { server_name: serverName, ...(this.getStatusPayload() || {}) };
    const resp = await API.callJsonApi("mcp_server_get_log", payload);
    if (resp?.success) {
      this.serverLog = resp.log;
      openModal("settings/mcp/client/mcp-servers-log.html");
    }
  },

  async onToolCountClick(serverName) {
    const payload = { server_name: serverName, ...(this.getStatusPayload() || {}) };
    const resp = await API.callJsonApi("mcp_server_get_detail", payload);
    if (resp?.success) {
      this.serverDetail = resp.detail;
      this.toolSearch = "";
      openModal("settings/mcp/client/mcp-server-tools.html");
    }
  },

  statusLabel(server) {
    if (!server.connected) return "Unavailable";
    if (server.error) return "Needs attention";
    if ((server.tool_count || 0) > 0) return "Ready";
    return "Connected";
  },

  statusClass(server) {
    if (!server.connected || server.error) return "danger";
    if ((server.tool_count || 0) > 0) return "ok";
    return "idle";
  },

  configModeLabel(config) {
    if (config?.disabled) return "Disabled";
    if (config?.url || config?.serverUrl) return "Remote";
    return "Local";
  },

  configSummary(config) {
    if (config?.url || config?.serverUrl) return config.url || config.serverUrl;
    const args = Array.isArray(config?.args) && config.args.length ? ` ${config.args.join(" ")}` : "";
    return `${config?.command || "command"}${args}`;
  },

  get scanWarnings() {
    return this.scanResult?.warnings || [];
  },

  get scanRiskLabel() {
    const risk = this.scanResult?.risk_level || "";
    if (risk === "ok") return "No major issues found";
    if (risk === "warning") return "Review warnings";
    if (risk === "error") return "Action needed";
    return "";
  },

  get renderedScanOutput() {
    return this.scanOutput ? marked.parse(this.scanOutput, { breaks: true }) : "";
  },

  onClose() {
    try {
      this.setScopeConfigJson(this.getEditorValue());
    } catch {}
    this.stopStatusCheck();
    if (this.editor) {
      try { this.editor.destroy(); } catch {}
      this.editor = null;
    }
    this.servers = [];
    this.loading = true;
    this.applying = false;
    this.activeView = "visual";
    this.serverSearch = "";
    this.toolSearch = "";
    this.serverDetail = null;
    this.resetForm();
    this.resetScanState();
    this.resetScope();
  },
};

const store = createStore("mcpServersStore", model);

export { store };
