import { marked } from "/vendor/marked/marked.esm.js";
import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";
import { openModal as openAppModal } from "/js/modals.js";
import { toastFrontendError } from "/components/notifications/notification-store.js";

const BASE = "/plugins/_plugin_validator/webui";

let _config = null;
let _templateCache = null;
let _guidanceCache = null;
let _pollGen = 0;
let _queue = [];
let _running = null;
const POLL_INTERVAL = 2000;
const MAX_POLL_MS = 10 * 60 * 1000;

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

async function loadConfig() {
  if (_config) return _config;
  try {
    _config = await fetchJson(`${BASE}/plugin-validator-checks.json`, "validator checks");
    return _config;
  } catch (error) {
    _config = null;
    throw error;
  }
}

async function loadTemplate() {
  if (_templateCache) return _templateCache;
  try {
    _templateCache = await fetchText(`${BASE}/plugin-validator-prompt.md`, "validator prompt template");
    return _templateCache;
  } catch (error) {
    _templateCache = null;
    throw error;
  }
}

async function loadGuidance() {
  if (_guidanceCache) return _guidanceCache;
  try {
    _guidanceCache = await fetchText(`${BASE}/plugin-validator-guidance.md`, "validator guidance");
    return _guidanceCache;
  } catch (error) {
    _guidanceCache = null;
    throw error;
  }
}

function formatCriteria(ratings, criteria) {
  return Object.entries(criteria)
    .map(([level, desc]) => `- ${ratings[level].icon} ${desc}`)
    .join("\n");
}

function formatStatusLegend(ratings) {
  return Object.entries(ratings)
    .map(([, rating]) => `- ${rating.icon} **${rating.label}**`)
    .join("\n");
}

function formatRatingIcons(ratings) {
  return Object.values(ratings).map((rating) => rating.icon).join("/");
}

function sourceLabel(source) {
  return {
    local: "Local Plugin",
    git: "Git Repository",
    zip: "Uploaded ZIP",
  }[source] || "Plugin Source";
}

function sanitizeTarget(value) {
  return String(value || "").trim().replaceAll("{", "(").replaceAll("}", ")");
}

function targetReference(source, state, overrideTarget = "") {
  if (overrideTarget) return sanitizeTarget(overrideTarget);

  if (source === "git") {
    return sanitizeTarget(state.gitUrl) || "<paste git URL here>";
  }

  if (source === "zip") {
    return state.zipFileName
      ? `<uploaded ZIP: ${sanitizeTarget(state.zipFileName)}>`
      : "<uploaded ZIP will be extracted for validation>";
  }

  return state.localPluginName
    ? `usr/plugins/${sanitizeTarget(state.localPluginName)}/`
    : "<select a local plugin>";
}

function sourceInstructions(source, state, overrideTarget = "", cleanupTarget = "") {
  const target = targetReference(source, state, overrideTarget);
  const cleanupPath = sanitizeTarget(cleanupTarget) || target;

  if (source === "git") {
    return `Clone \`${target}\` to a temporary directory outside the workspace, such as \`/tmp/plugin-validate-$(date +%s)\`. Validate the cloned files there. After the review, run \`rm -rf /tmp/plugin-validate-*\` and verify cleanup with \`ls /tmp/plugin-validate-* 2>&1\`.`;
  }

  if (source === "zip") {
    if (overrideTarget) {
      return `The ZIP has already been extracted to \`${target}\`. Validate the plugin from that extracted directory only. Do not install or move it. After the review, delete that extracted directory with \`rm -rf "${cleanupPath}"\` and verify cleanup with \`ls "${cleanupPath}" 2>&1\`.`;
    }
    return "On run, the selected ZIP will be extracted to a temporary directory for validation. Review the extracted plugin only, do not install it, and delete the extracted directory after the review.";
  }

  return `Read the plugin directly from \`${target}\`. Do not clone, move, or modify the plugin. No temporary cleanup is required for this source.`;
}

async function parseJsonResponse(response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { error: text };
  }
}

export const store = createStore("pluginValidator", {
  source: "local",
  localPlugins: [],
  localPluginName: "",
  gitUrl: "",
  zipFile: null,
  zipFileName: "",
  checks: {},
  checksMeta: {},
  prompt: "",
  output: "",
  validating: false,
  queued: false,
  validationCtxId: "",

  get renderedOutput() {
    return this.output ? marked.parse(this.output, { breaks: true }) : "";
  },

  async init() {
    const cfg = await loadConfig();
    if (!cfg) return;
    this.checksMeta = cfg.checks;
    const initial = {};
    for (const key of Object.keys(cfg.checks)) initial[key] = true;
    this.checks = initial;
    await this.loadLocalPlugins();
  },

  async loadLocalPlugins() {
    try {
      const response = await api.callJsonApi("plugins_list", {
        filter: { custom: true, builtin: false, search: "" },
      });
      const plugins = Array.isArray(response.plugins) ? response.plugins : [];
      this.localPlugins = plugins
        .filter((plugin) => plugin?.name)
        .sort((a, b) => (a.display_name || a.name || "").localeCompare(b.display_name || b.name || ""));

      if (!this.localPluginName && this.localPlugins.length) {
        const firstPlugin = this.localPlugins[0];
        this.localPluginName = firstPlugin && typeof firstPlugin === "object" ? firstPlugin["name"] || "" : "";
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      void toastFrontendError(`Failed to load local plugins: ${message}`, "Plugin Validator");
      this.localPlugins = [];
      this.localPluginName = "";
    }
  },

  applyOptions(options = {}) {
    if (options.source) this.source = options.source;
    if (typeof options.localPluginName === "string") this.localPluginName = options.localPluginName;
    if (typeof options.gitUrl === "string") this.gitUrl = options.gitUrl;
    if (options.zipFile) {
      this.zipFile = options.zipFile;
      this.zipFileName = options.zipFileName || options.zipFile.name || "";
      this.source = "zip";
    }
  },

  async onOpen() {
    this.output = "";
    this.validating = false;
    this.queued = false;
    this.validationCtxId = "";
    await this.loadLocalPlugins();

    const cfg = await loadConfig();
    if (cfg && Object.keys(this.checks).length === 0) {
      this.checksMeta = cfg.checks;
      const initial = {};
      for (const key of Object.keys(cfg.checks)) initial[key] = true;
      this.checks = initial;
    }

    await this.buildPrompt();
  },

  cleanup() {
    _pollGen++;
  },

  async openModal(options = {}) {
    this.applyOptions(options);
    await openAppModal("/plugins/_plugin_validator/webui/plugin-validator.html");
  },

  async setSource(source) {
    this.source = source || "local";
    await this.buildPrompt();
  },

  async selectLocalPlugin(name) {
    this.localPluginName = name || "";
    await this.buildPrompt();
  },

  async handleZipUpload(event) {
    const file = event?.target?.files?.[0];
    if (!file) return;
    this.zipFile = file;
    this.zipFileName = file.name || "";
    await this.buildPrompt();
  },

  async buildPrompt(targetOverride = "", cleanupTargetOverride = "") {
    try {
      const [cfg, template, guidance] = await Promise.all([loadConfig(), loadTemplate(), loadGuidance()]);
      if (!cfg) return;
      const { ratings, checks } = cfg;

      const selected = Object.entries(this.checks)
        .filter(([, enabled]) => enabled)
        .map(([key]) => checks[key])
        .filter(Boolean);

      let text = template;
      text = text.replace(/\{\{SOURCE_LABEL\}\}/g, sourceLabel(this.source));
      text = text.replace(/\{\{TARGET_REFERENCE\}\}/g, targetReference(this.source, this, targetOverride));
      text = text.replace(/\{\{SOURCE_INSTRUCTIONS\}\}/g, sourceInstructions(this.source, this, targetOverride, cleanupTargetOverride));
      text = text.replace(
        /\{\{SELECTED_CHECKS\}\}/g,
        selected.length ? selected.map((check) => `- ${check.label}`).join("\n") : "- (no validation phases selected)",
      );
      text = text.replace(
        /\{\{CHECK_DETAILS\}\}/g,
        selected.length
          ? selected
              .map((check) => `**${check.label}**: ${check.detail}\n${formatCriteria(ratings, check.criteria)}`)
              .join("\n\n")
          : "(no validation phases selected)",
      );
      text = text.replace(/\{\{CHECKLIST_GUIDANCE\}\}/g, guidance);
      text = text.replace(/\{\{STATUS_LEGEND\}\}/g, formatStatusLegend(ratings));
      text = text.replace(/\{\{RATING_ICONS\}\}/g, formatRatingIcons(ratings));
      text = text.replace(/\{\{RATING_PASS\}\}/g, ratings.pass.icon);
      text = text.replace(/\{\{RATING_WARNING\}\}/g, ratings.warning.icon);
      text = text.replace(/\{\{RATING_FAIL\}\}/g, ratings.fail.icon);

      this.prompt = text;
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      void toastFrontendError(`Failed to build prompt: ${message}`, "Plugin Validator");
    }
  },

  async copyPrompt() {
    try {
      await navigator.clipboard.writeText(this.prompt);
    } catch {
      void toastFrontendError("Failed to copy the validation prompt", "Plugin Validator");
    }
  },

  async _prepareZipForValidation() {
    if (!this.zipFile) {
      throw new Error("Please select a ZIP file first.");
    }

    const formData = new FormData();
    formData.append("plugin_file", this.zipFile);

    const response = await api.fetchApi("/plugins/_plugin_validator/plugin_validator_prepare_zip", {
      method: "POST",
      body: formData,
    });
    const data = await parseJsonResponse(response);
    if (!response.ok || !data.ok) {
      throw new Error(data.error || "ZIP preparation failed.");
    }

    return data;
  },

  async runValidation() {
    const selectedChecks = Object.entries(this.checks).filter(([, enabled]) => enabled);
    if (!selectedChecks.length) {
      void toastFrontendError("Select at least one validation phase", "Plugin Validator");
      return;
    }

    let targetOverride = "";
    let cleanupTargetOverride = "";
    if (this.source === "local") {
      if (!this.localPluginName) {
        void toastFrontendError("Select a local plugin to validate", "Plugin Validator");
        return;
      }
    } else if (this.source === "git") {
      if (!this.gitUrl.trim()) {
        void toastFrontendError("Please enter a Git URL", "Plugin Validator");
        return;
      }
    } else if (this.source === "zip") {
      try {
        const prepared = await this._prepareZipForValidation();
        targetOverride = prepared.path || "";
        cleanupTargetOverride = prepared.cleanup_path || prepared.path || "";
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        void toastFrontendError(message, "Plugin Validator");
        return;
      }
    }

    await this.buildPrompt(targetOverride, cleanupTargetOverride);
    const capturedPrompt = this.prompt;
    const gen = ++_pollGen;
    this.output = "";

    let ctxId;
    try {
      const response = await api.callJsonApi("/chat_create", {});
      if (!response.ok) throw new Error("Failed to create chat context");
      ctxId = response.ctxid;
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      void toastFrontendError(`Validation failed: ${message}`, "Plugin Validator");
      return;
    }
    this.validationCtxId = ctxId;

    if (_running) {
      try {
        await api.callJsonApi("/plugins/_plugin_validator/plugin_validator_queue", {
          context: ctxId,
          text: capturedPrompt,
          queued: true,
        });
      } catch {
        // Best effort only.
      }
      _queue.push({ gen, ctxId, prompt: capturedPrompt });
      this.queued = true;
      this.validating = false;
    } else {
      try {
        await api.callJsonApi("/plugins/_plugin_validator/plugin_validator_queue", {
          context: ctxId,
          text: capturedPrompt,
        });
      } catch {
        // Best effort only.
      }
      this.queued = false;
      this.validating = true;
      this._runNext(gen, ctxId, capturedPrompt);
    }
  },

  async _runNext(gen, ctxId, prompt) {
    _running = { gen, ctxId };
    try {
      await api.callJsonApi("/plugins/_plugin_validator/plugin_validator_start", {
        text: prompt,
        context: ctxId,
      });
      await this._pollLoop(gen, ctxId);
    } catch (e) {
      if (gen === _pollGen) {
        const message = e instanceof Error ? e.message : String(e);
        void toastFrontendError(`Validation failed: ${message}`, "Plugin Validator");
        this.validating = false;
        this.queued = false;
      }
    } finally {
      _running = null;
      while (_queue.length) {
        const next = _queue.shift();
        if (!next || next.gen !== _pollGen) {
          continue;
        }
        this.queued = false;
        this.validating = true;
        this._runNext(next.gen, next.ctxId, next.prompt);
        break;
      }
    }
  },

  async _pollLoop(gen, ctxId) {
    let started = false;
    const deadline = Date.now() + MAX_POLL_MS;
    while (true) {
      if (Date.now() >= deadline) {
        if (gen === _pollGen) {
          this.validating = false;
          void toastFrontendError("Validation timed out while waiting for the agent response", "Plugin Validator");
          console.error(`Validation poll timed out for context ${ctxId}`);
        }
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL));
      try {
        const snapshot = await api.callJsonApi("/poll", {
          context: ctxId,
          log_from: 0,
          notifications_from: 0,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        });

        if (gen === _pollGen && snapshot.logs?.length) {
          const last = snapshot.logs
            .filter((log) => log.type === "response" && log.no > 0)
            .pop();
          if (last) this.output = last.content || "";
        }

        if (snapshot.log_progress_active) started = true;
        if (started && !snapshot.log_progress_active) {
          if (gen === _pollGen) this.validating = false;
          return;
        }
        if (snapshot.deselect_chat) return;
      } catch (e) {
        if (gen === _pollGen) {
          console.error("Validation poll error:", e);
        }
      }
    }
  },

  openChatInNewWindow() {
    if (!this.validationCtxId) return;
    const url = new URL(window.location.href);
    url.searchParams.set("ctxid", this.validationCtxId);
    window.open(url.toString(), "_blank");
  },
});
