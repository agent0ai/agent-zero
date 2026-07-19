import { createStore } from "/js/AlpineStore.js";
import { marked } from "/vendor/marked/marked.esm.js";
import sleep from "/js/sleep.js";
import * as api from "/js/api.js";
import { openModal } from "/js/modals.js";
import { getUserTimezone } from "/js/time-utils.js";
import {
  toastFrontendError,
  toastFrontendWarning,
} from "/components/notifications/notification-store.js";

const SCAN_ASSET_BASE = "/components/settings/skills";
const SCAN_POLL_INTERVAL_MS = 2000;
const SCAN_MAX_POLL_MS = 10 * 60 * 1000;
const SCAN_TITLE = "Skill Scanner";

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
  scanChecksConfig = await fetchJson(`${SCAN_ASSET_BASE}/skill-scan-checks.json`, "skill scan checks");
  return scanChecksConfig;
}

async function loadScanTemplate() {
  if (scanPromptTemplate) return scanPromptTemplate;
  scanPromptTemplate = await fetchText(`${SCAN_ASSET_BASE}/skill-scan-prompt.md`, "skill scan prompt");
  return scanPromptTemplate;
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

function splitTargetLines(value) {
  return String(value || "")
    .split(/\r?\n/u)
    .map((line) => line.trim())
    .filter(Boolean);
}

function inferTargetType(value) {
  const text = String(value || "").trim();
  if (/^(https?:\/\/|git@)/iu.test(text)) return "git_url";
  return "path";
}

function shellQuote(value) {
  return `'${String(value || "").replace(/'/g, "'\"'\"'")}'`;
}

function createDefaultScanOptions() {
  return {
    useSnykAgentScan: true,
  };
}

function formatErrorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

const model = {
  sectionTarget: "",
  sectionLoading: false,
  installedTargets: [],

  targetType: "path",
  targetLabel: "Manual target",
  targetText: "",
  targetSummary: "{}",
  cleanupPaths: [],

  scanChecks: {},
  scanChecksMeta: {},
  scanOptions: createDefaultScanOptions(),
  scanPrompt: "",
  scanOutput: "",
  scanCtxId: "",
  agentScanning: false,
  preparingUpload: false,

  get renderedScanOutput() {
    return this.scanOutput ? marked.parse(this.scanOutput, { breaks: true }) : "";
  },

  async init() {
    await this.ensureScanFramework();
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
      console.error("Failed to load skill scanner framework:", error);
      void toastFrontendError(`Failed to load skill scanner: ${formatErrorMessage(error)}`, SCAN_TITLE);
      return null;
    }
  },

  async loadInstalledTargets() {
    this.sectionLoading = true;
    try {
      const response = await api.callJsonApi("/skills_scan", { action: "targets" });
      if (!response?.success) throw new Error(response?.error || "Unable to load installed skill targets");
      this.installedTargets = response.targets || [];
      return response;
    } catch (error) {
      console.error("Failed to load installed skill targets:", error);
      void toastFrontendError(`Failed to load installed skills: ${formatErrorMessage(error)}`, SCAN_TITLE);
      return null;
    } finally {
      this.sectionLoading = false;
    }
  },

  async openForInstalledSkills() {
    const response = await this.loadInstalledTargets();
    const paths = response?.paths || [];
    if (!paths.length) {
      void toastFrontendWarning("No installed skills found to scan.", SCAN_TITLE);
      return;
    }

    await this.openModalForTarget({
      target_type: "installed",
      target_label: "Installed Agent Zero skills",
      paths,
      summary: {
        skill_count: response.skill_count || 0,
        roots: response.targets || [],
      },
    });
  },

  async openForManualTarget() {
    const target = String(this.sectionTarget || "").trim();
    if (!target) {
      await this.openForInstalledSkills();
      return;
    }

    await this.openModalForTarget({
      target_type: inferTargetType(target),
      target_label: target,
      paths: splitTargetLines(target),
      summary: {},
    });
  },

  async openForUploadedFile(file, metadata = {}) {
    if (!file) {
      void toastFrontendError("Select a skills .zip file first", SCAN_TITLE);
      return false;
    }

    this.preparingUpload = true;
    try {
      const formData = new FormData();
      formData.append("skills_file", file);
      formData.append("ctxid", globalThis.getContext ? globalThis.getContext() : "");
      if (metadata.namespace) formData.append("namespace", metadata.namespace);

      const response = await api.fetchApi("/skills_scan", {
        method: "POST",
        body: formData,
      });
      const result = await response.json();
      if (!result?.success) throw new Error(result?.error || "Failed to prepare skill scan");

      await this.openModalForTarget({
        ...result,
        summary: {
          skill_count: result.skill_count || 0,
          skills: result.skills || [],
          warnings: result.warnings || [],
          display_path: result.display_path || "",
        },
      });
      return true;
    } catch (error) {
      console.error("Failed to prepare uploaded skill scan:", error);
      void toastFrontendError(`Skill scan failed: ${formatErrorMessage(error)}`, SCAN_TITLE);
      return false;
    } finally {
      this.preparingUpload = false;
    }
  },

  async openModalForTarget(target = {}) {
    this.applyTarget(target);
    await this.ensureScanFramework();
    await this.buildScanPrompt();
    await openModal("settings/skills/skill-scan.html");
  },

  applyTarget(target = {}) {
    const paths = Array.isArray(target.paths) ? target.paths.filter(Boolean) : [];
    const fallbackText = target.scan_path || target.target_text || "";
    const targetText = paths.length ? paths.join("\n") : fallbackText;

    this.targetType = target.target_type || inferTargetType(targetText);
    this.targetLabel = target.target_label || target.label || targetText || "Manual target";
    this.targetText = targetText;
    this.targetSummary = JSON.stringify(target.summary || {}, null, 2);
    this.cleanupPaths = Array.isArray(target.cleanup_paths) ? target.cleanup_paths.filter(Boolean) : [];
    this.scanOutput = "";
    this.scanCtxId = "";
    this.agentScanning = false;
  },

  async onScanModalOpen() {
    await this.ensureScanFramework();
    if (!this.targetText && this.sectionTarget) {
      this.applyTarget({
        target_type: inferTargetType(this.sectionTarget),
        target_label: this.sectionTarget,
        paths: splitTargetLines(this.sectionTarget),
      });
    }
    await this.buildScanPrompt();
  },

  async buildScanPrompt() {
    try {
      const [cfg, template] = await Promise.all([loadScanChecks(), loadScanTemplate()]);
      const ratings = cfg.ratings || {};
      const checks = cfg.checks || {};
      const selected = Object.entries(this.scanChecks)
        .filter(([, enabled]) => enabled)
        .map(([key]) => checks[key])
        .filter(Boolean);

      const targetPaths = splitTargetLines(this.targetText);
      const targetArgs = this.targetType === "git_url"
        ? "<cloned skill repository path>"
        : targetPaths.map((path) => shellQuote(path)).join(" ");
      const cleanupText = this.cleanupPaths.length ? this.cleanupPaths.join("\n") : "(none)";

      let prompt = template;
      prompt = prompt.replace(/\{\{TARGET_TYPE\}\}/g, this.targetType || "path");
      prompt = prompt.replace(/\{\{TARGET_LABEL\}\}/g, this.targetLabel || "Manual target");
      prompt = prompt.replace(/\{\{TARGET_PATHS\}\}/g, targetPaths.length ? targetPaths.join("\n") : "(none)");
      prompt = prompt.replace(/\{\{TARGET_SUMMARY\}\}/g, this.targetSummary || "{}");
      prompt = prompt.replace(/\{\{CLEANUP_PATHS\}\}/g, cleanupText);
      prompt = prompt.replace(/\{\{SNYK_SCAN_ENABLED\}\}/g, this.scanOptions.useSnykAgentScan ? "yes" : "no");
      prompt = prompt.replace(/\{\{SNYK_TARGET_ARGS\}\}/g, targetArgs || "<target path>");
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
      console.error("Failed to build skill scan prompt:", error);
      void toastFrontendError(`Failed to build scan prompt: ${formatErrorMessage(error)}`, SCAN_TITLE);
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
      const resp = await api.callJsonApi("/chat_create", {});
      if (!resp?.ok || !resp.ctxid) throw new Error(resp?.message || "Failed to create scan chat");
      ctxId = resp.ctxid;
      this.scanCtxId = ctxId;
      await api.callJsonApi("/message_queue_add", { context: ctxId, text: prompt });
      this.agentScanning = true;
      await api.callJsonApi("/message_queue_send", { context: ctxId });
      void this.pollAgentScan(gen, ctxId);
    } catch (error) {
      this.agentScanning = false;
      console.error("Skill agent scan failed:", error);
      void toastFrontendError(`Scan failed: ${formatErrorMessage(error)}`, SCAN_TITLE);
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
        const snap = await api.callJsonApi("/poll", {
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
        if (gen === scanPollGeneration) console.error("Skill scan poll error:", error);
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

  onClose() {
    this.scanCleanup();
  },
};

const store = createStore("skillsScanStore", model);
export { store };
