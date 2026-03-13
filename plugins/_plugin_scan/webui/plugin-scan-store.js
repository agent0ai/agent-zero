import { marked } from "/vendor/marked/marked.esm.js";
import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";
import { openModal } from "/js/modals.js";

const BASE = "/plugins/_plugin_scan/webui";

/** @type {{ ratings: Record<string, {icon:string,label:string}>, checks: Record<string, {label:string,detail:string,criteria:Record<string,string>}> } | null} */
let _config = null;
/** @type {string|null} */
let _templateCache = null;

async function loadConfig() {
  if (!_config) {
    const resp = await fetch(`${BASE}/plugin-scan-checks.json`);
    _config = await resp.json();
  }
  return _config;
}

async function loadTemplate() {
  if (!_templateCache) {
    const resp = await fetch(`${BASE}/plugin-scan-prompt.md`);
    _templateCache = await resp.text();
  }
  return _templateCache;
}

function formatCriteria(ratings, criteria) {
  return Object.entries(criteria)
    .map(([level, desc]) => `- ${ratings[level].icon} ${desc}`)
    .join("\n");
}

function formatStatusLegend(ratings) {
  return Object.entries(ratings)
    .map(([, r]) => `- ${r.icon} **${r.label}**`)
    .join("\n");
}

function formatRatingIcons(ratings) {
  return Object.values(ratings).map((r) => r.icon).join("/");
}
let _pollGen = 0;
/** @type {{ gen: number, ctxId: string, prompt: string }[]} */
let _queue = [];
/** @type {{ gen: number, ctxId: string } | null} */
let _running = null;
const POLL_INTERVAL = 2000;

export const store = createStore("pluginScan", {
  gitUrl: "",
  checks: {},
  checksMeta: {},
  prompt: "",
  output: "",
  scanning: false,
  queued: false,
  scanCtxId: "",
  error: "",

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
  },

  async onOpen(url) {
    this.error = "";
    this.output = "";
    this.scanning = false;
    this.queued = false;
    if (url) this.gitUrl = url;
    const cfg = await loadConfig();
    if (cfg && Object.keys(this.checks).length === 0) {
      this.checksMeta = cfg.checks;
      const initial = {};
      for (const key of Object.keys(cfg.checks)) initial[key] = true;
      this.checks = initial;
    }
    this.buildPrompt();
  },

  cleanup() {
    _pollGen++;
  },

  async openModal(url) {
    this.gitUrl = url || "";
    await openModal("/plugins/_plugin_scan/webui/plugin-scan.html");
  },

  async buildPrompt() {
    try {
      const [cfg, template] = await Promise.all([loadConfig(), loadTemplate()]);
      if (!cfg) return;
      const { ratings, checks } = cfg;

      let text = template;
      text = text.replace(/\{\{GIT_URL\}\}/g, this.gitUrl || "<paste git URL here>");

      const selected = Object.entries(this.checks)
        .filter(([, v]) => v)
        .map(([k]) => checks[k])
        .filter(Boolean);

      text = text.replace(
        /\{\{SELECTED_CHECKS\}\}/g,
        selected.length ? selected.map((c) => `- ${c.label}`).join("\n") : "- (no checks selected)",
      );
      text = text.replace(
        /\{\{CHECK_DETAILS\}\}/g,
        selected.length
          ? selected.map((c) => `**${c.label}**: ${c.detail}\n${formatCriteria(ratings, c.criteria)}`).join("\n\n")
          : "(no checks selected)",
      );
      text = text.replace(/\{\{STATUS_LEGEND\}\}/g, formatStatusLegend(ratings));
      text = text.replace(/\{\{RATING_ICONS\}\}/g, formatRatingIcons(ratings));
      text = text.replace(/\{\{RATING_PASS\}\}/g, ratings.pass.icon);
      text = text.replace(/\{\{RATING_WARNING\}\}/g, ratings.warning.icon);
      text = text.replace(/\{\{RATING_FAIL\}\}/g, ratings.fail.icon);

      this.prompt = text;
    } catch (/** @type {any} */ e) {
      console.error("Failed to build prompt:", e);
      this.error = "Failed to load prompt template.";
    }
  },

  async copyPrompt() {
    try { await navigator.clipboard.writeText(this.prompt); } catch { /* noop */ }
  },

  /**
   * Create a context immediately and either execute or queue the scan.
   * Queued scans have their prompt logged to the chat + progress bar set to "Queued",
   * but the agent is NOT started until it's their turn.
   */
  async runScan() {
    if (!this.gitUrl) { this.error = "Please enter a Git URL."; return; }

    await this.buildPrompt();
    const capturedPrompt = this.prompt;
    const gen = ++_pollGen;
    this.error = "";
    this.output = "";

    let ctxId;
    try {
      const resp = await api.callJsonApi("/chat_create", {});
      if (!resp.ok) throw new Error("Failed to create chat context");
      ctxId = resp.ctxid;
    } catch (/** @type {any} */ e) {
      this.error = `Scan failed: ${e.message || e}`;
      return;
    }
    this.scanCtxId = ctxId;

    if (_running) {
      try {
        await api.callJsonApi("/plugins/_plugin_scan/plugin_scan_queue", { context: ctxId, text: capturedPrompt, queued: true });
      } catch { /* best-effort */ }
      _queue.push({ gen, ctxId, prompt: capturedPrompt });
      this.queued = true;
      this.scanning = false;
    } else {
      try {
        await api.callJsonApi("/plugins/_plugin_scan/plugin_scan_queue", { context: ctxId, text: capturedPrompt });
      } catch { /* best-effort */ }
      this.queued = false;
      this.scanning = true;
      this._runNext(gen, ctxId, capturedPrompt);
    }
  },

  /** @param {number} gen  @param {string} ctxId  @param {string} prompt */
  async _runNext(gen, ctxId, prompt) {
    _running = { gen, ctxId };
    try {
      await api.callJsonApi("/plugins/_plugin_scan/plugin_scan_start", { text: prompt, context: ctxId });
      await this._pollLoop(gen, ctxId);
    } catch (/** @type {any} */ e) {
      if (gen === _pollGen) {
        this.error = `Scan failed: ${e.message || e}`;
        this.scanning = false;
        this.queued = false;
      }
    } finally {
      _running = null;
      if (_queue.length) {
        const next = /** @type {{ gen: number, ctxId: string, prompt: string }} */ (_queue.shift());
        if (next.gen === _pollGen) { this.queued = false; this.scanning = true; }
        this._runNext(next.gen, next.ctxId, next.prompt);
      }
    }
  },

  /** @param {number} gen  @param {string} ctxId */
  async _pollLoop(gen, ctxId) {
    let started = false;
    while (true) {
      await new Promise((r) => setTimeout(r, POLL_INTERVAL));
      try {
        const snap = await api.callJsonApi("/poll", {
          context: ctxId, log_from: 0, notifications_from: 0,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        });

        if (gen === _pollGen && snap.logs?.length) {
          const last = snap.logs.filter((/** @type {any} */ l) => l.type === "response" && l.no > 0).pop();
          if (last) this.output = last.content || "";
        }

        if (snap.log_progress_active) started = true;
        if (started && !snap.log_progress_active) {
          if (gen === _pollGen) this.scanning = false;
          return;
        }
        if (snap.deselect_chat) return;
      } catch (/** @type {any} */ e) {
        if (gen === _pollGen) console.error("Poll error:", e);
      }
    }
  },

  openChatInNewWindow() {
    if (!this.scanCtxId) return;
    const url = new URL(window.location.href);
    url.searchParams.set("ctxid", this.scanCtxId);
    window.open(url.toString(), "_blank");
  },
});
