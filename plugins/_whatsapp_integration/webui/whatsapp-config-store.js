import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";

const API_BASE = "/plugins/_whatsapp_integration";
const STEPS = [
  {
    title: "Pair your account and set access",
    description: "Link WhatsApp with a QR code, then choose who can reach your agent.",
  },
  {
    title: "Choose where conversations go",
    description: "Pick a project if you want one and shape how the agent should reply.",
  },
];

function ensureConfig(config) {
  if (!config || typeof config !== "object") return;
  if (typeof config.enabled !== "boolean") config.enabled = false;
  if (!config.mode) config.mode = "self-chat";
  if (!config.bridge_port) config.bridge_port = 3100;
  if (!config.poll_interval_seconds) config.poll_interval_seconds = 3;
  if (typeof config.allow_group !== "boolean") config.allow_group = false;

  if (Array.isArray(config.allowed_numbers)) return;
  if (typeof config.allowed_numbers === "string") {
    config.allowed_numbers = config.allowed_numbers
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item);
    return;
  }
  config.allowed_numbers = [];
}

export const store = createStore("whatsappConfig", {
  config: null,
  projects: [],
  guideOpen: false,
  currentStep: 0,
  testing: false,
  testResults: null,
  qrVisible: false,
  qrStatus: "",
  qrMessage: "",
  qrDataUrl: null,
  qrPollTimer: null,
  _qrSession: 0,
  disconnecting: false,
  disconnectMessage: "",
  steps: STEPS,
  _projectsLoaded: false,
  context: null,

  get showFooterNav() {
    return true;
  },

  get isFirstStep() {
    return this.currentStep === 0;
  },

  get isLastStep() {
    return this.currentStep >= this.steps.length - 1;
  },

  get nextButtonLabel() {
    return this.isLastStep ? "Done" : "Next";
  },

  get footerStepLabel() {
    return `Step ${this.currentStep + 1} of ${this.steps.length}`;
  },

  async init(config, context = null) {
    this.config = config || null;
    this.context = context;
    ensureConfig(this.config);
    this.guideOpen = !this.hasMeaningfulConfig() && window.innerWidth > 720;
    this.currentStep = 0;
    this.testing = false;
    this.testResults = null;
    this._installWizardFooter();

    if (this._projectsLoaded) return;
    try {
      const response = await API.callJsonApi("projects", { action: "list" });
      this.projects = response.data || [];
    } catch (_) {
      this.projects = [];
    }
    this._projectsLoaded = true;
  },

  cleanup() {
    if (this.context?.wizardFooter?.owner === "whatsappConfig") {
      this.context.wizardFooter = null;
    }
    this.hideQr();
    this.config = null;
    this.context = null;
    this.guideOpen = false;
    this.currentStep = 0;
    this.testing = false;
    this.testResults = null;
    this.disconnecting = false;
    this.disconnectMessage = "";
  },

  currentStepMeta() {
    return this.steps[this.currentStep] || this.steps[0];
  },

  setStep(step) {
    this.currentStep = Math.max(0, Math.min(this.steps.length - 1, Number(step) || 0));
  },

  nextStep() {
    if (!this.isLastStep) this.currentStep += 1;
  },

  previousStep() {
    if (!this.isFirstStep) this.currentStep -= 1;
  },

  hasMeaningfulConfig() {
    if (!this.config) return false;
    return !!(
      this.config.enabled
      || String(this.config.project || "").trim()
      || String(this.config.agent_instructions || "").trim()
      || (Array.isArray(this.config.allowed_numbers) && this.config.allowed_numbers.length > 0)
    );
  },

  allowedText() {
    ensureConfig(this.config);
    return (this.config?.allowed_numbers || []).join(", ");
  },

  allowedIsEmpty() {
    ensureConfig(this.config);
    return (this.config?.allowed_numbers || []).length === 0;
  },

  setAllowed(value) {
    ensureConfig(this.config);
    this.config.allowed_numbers = value
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item);
  },

  onEnabledChange() {
    if (this.config?.enabled) return;
    this.hideQr();
  },

  accessWarning() {
    if (!this.config?.enabled) return "";
    if (!this.allowedIsEmpty()) return "";
    return "Allowed numbers is empty. If other people can message this number, they can reach your Agent Zero.";
  },

  statusLabel() {
    if (!this.config?.enabled) return "Off";
    if (this.qrStatus === "connected") return "Live";
    if (this.allowedIsEmpty()) return "Open access";
    return "Ready";
  },

  statusTone() {
    const label = this.statusLabel();
    if (label === "Live") return "success";
    if (label === "Ready") return "ready";
    if (label === "Off") return "muted";
    return "warning";
  },

  modeSummary() {
    if (!this.config) return "";
    return this.config.mode === "self-chat" ? "Self-chat" : "Dedicated number";
  },

  projectSummary() {
    return this.config?.project ? `Project: ${this.projectLabel(this.config.project)}` : "No project";
  },

  projectOptionValue(project) {
    return String(project?.key || project?.name || "");
  },

  projectOptionLabel(project) {
    return project?.label || project?.title || project?.name || project?.key || "";
  },

  projectLabel(projectKey) {
    const normalizedProjectKey = String(projectKey || "").trim();
    if (!normalizedProjectKey) return "";
    const project = (this.projects || []).find((item) =>
      String(item?.key || "") === normalizedProjectKey || String(item?.name || "") === normalizedProjectKey
    );
    if (project) return this.projectOptionLabel(project);
    return normalizedProjectKey;
  },

  async testConnection() {
    this.testing = true;
    this.testResults = null;
    try {
      this.testResults = await API.callJsonApi(`${API_BASE}/test_connection`, {
        config: { bridge_port: this.config?.bridge_port },
      });
    } catch (error) {
      this.testResults = {
        success: false,
        results: [{ test: "WhatsApp", ok: false, message: String(error) }],
      };
    }
    this.testing = false;
  },

  testButtonLabel() {
    return this.testing ? "Checking..." : "Check WhatsApp connection";
  },

  async showQr() {
    if (!this.config) return;
    this.hideQr();
    this.config.enabled = true;
    this.disconnectMessage = "";
    this.qrVisible = true;
    this.qrStatus = "loading";
    this.qrMessage = "Preparing QR code...";
    this.qrDataUrl = null;
    await this.pollQr();
  },

  hideQr() {
    this._qrSession += 1;
    this.qrVisible = false;
    this.qrDataUrl = null;
    this.qrStatus = "";
    if (this.qrPollTimer) {
      clearTimeout(this.qrPollTimer);
      this.qrPollTimer = null;
    }
  },

  async pollQr(session = this._qrSession) {
    if (!this.qrVisible || session !== this._qrSession) return;
    try {
      const response = await API.callJsonApi(`${API_BASE}/qr_code`, {});
      if (!this.qrVisible || session !== this._qrSession) return;
      this.qrStatus = response.status || "error";
      this.qrMessage = response.message || "";
      this.qrDataUrl = response.qr || null;
    } catch (error) {
      if (!this.qrVisible || session !== this._qrSession) return;
      this.qrStatus = "error";
      this.qrMessage = String(error);
      this.qrDataUrl = null;
    }
    this.qrPollTimer = null;
    if (this.qrStatus !== "connected" && this.qrStatus !== "error") {
      this.qrPollTimer = setTimeout(() => this.pollQr(session), 3000);
    }
  },

  async disconnectAccount() {
    if (!window.confirm("Disconnect this WhatsApp account? You will need to scan a new QR code to reconnect.")) return;
    this.hideQr();
    this.disconnecting = true;
    this.disconnectMessage = "";
    try {
      const response = await API.callJsonApi(`${API_BASE}/disconnect`, {});
      this.disconnectMessage = response.success ? "Account disconnected" : (response.message || "Disconnect failed");
    } catch (error) {
      this.disconnectMessage = String(error);
    }
    this.disconnecting = false;
  },

  _installWizardFooter() {
    if (!this.context) return;
    this.context.wizardFooter = {
      owner: "whatsappConfig",
      visible: () => this.showFooterNav,
      canGoBack: () => !this.isFirstStep,
      backLabel: () => "Back",
      note: () => this.footerStepLabel,
      showNext: () => !this.isLastStep,
      nextLabel: () => this.nextButtonLabel,
      nextDisabled: () => false,
      showSave: () => this.isLastStep,
      onBack: () => this.previousStep(),
      onNext: () => this.nextStep(),
    };
  },
});
