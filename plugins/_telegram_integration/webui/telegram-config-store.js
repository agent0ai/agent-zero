import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";

const API_BASE = "/plugins/_telegram_integration";
const STEPS = [
  {
    title: "Connect your bot",
    description: "Start with BotFather, then paste the bot token here.",
  },
  {
    title: "Choose who can use it",
    description: "Finish the core setup, choose access, and decide how messages arrive.",
  },
  {
    title: "Shape the conversation",
    description: "Choose how the bot behaves in groups and how the agent should reply.",
  },
];

const BOTFATHER_QR =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHQAAAB0AQAAAAB84SuKAAAA50lEQVR4nMWVQWoFMQxDnz+zl2/w73+suYF8Aheni98ux1BqglEgQjOx7ETzM+r1awt/v4+ILCAHLPjqJivLAx7zLwjh7Dxg+T/pKj84/4nr5FHPgxb6bRLjAY/50QE6sED3Uz79HZrr7/ZzPiM/X2B7w/cw263uFZ+2sOb6rMf8iyZNNiqt6lfFG1fembHxzxszKQ1a9a8SO26STf9RU8MUqUX/0DLSmULSpn4T6Kx+zn+d+cMdJrWYP4zvxjy91SeSt6mKjf51cinGgOznsVP2rn7dksaEU8uF/yPAGvsu/B///H59AYlVhAI4J5PTAAAAAElFTkSuQmCC";

function ensureConfig(config) {
  if (!config || typeof config !== "object") return;
  if (!Array.isArray(config.bots)) config.bots = [];
}

export const store = createStore("telegramConfig", {
  config: null,
  projects: [],
  editing: null,
  testing: null,
  testResults: null,
  testResultsFor: null,
  botSteps: [],
  didInit: false,
  steps: STEPS,
  botFatherQr: BOTFATHER_QR,
  _projectsLoaded: false,
  context: null,

  get bots() {
    ensureConfig(this.config);
    return Array.isArray(this.config?.bots) ? this.config.bots : [];
  },

  get activeIndex() {
    return typeof this.editing === "number" ? this.editing : -1;
  },

  get activeBot() {
    return this.activeIndex >= 0 ? this.bots[this.activeIndex] || null : null;
  },

  get showFooterNav() {
    return this.activeIndex >= 0;
  },

  get currentStep() {
    return this.activeIndex >= 0 && typeof this.botSteps[this.activeIndex] === "number"
      ? this.botSteps[this.activeIndex]
      : 0;
  },

  get isFirstStep() {
    return this.currentStep === 0;
  },

  get isLastStep() {
    return this.currentStep >= this.steps.length - 1;
  },

  get nextDisabled() {
    return !!this.stepBlockedReason();
  },

  get nextButtonLabel() {
    return this.isLastStep ? "Done" : "Next";
  },

  get footerStepLabel() {
    return `Step ${this.currentStep + 1} of ${this.steps.length}`;
  },

  async init(config, context = null) {
    if (!config || typeof config !== "object") return;

    this.config = config || null;
    this.context = context;
    this.didInit = false;
    ensureConfig(this.config);
    this.editing = this.bots.length === 1 ? 0 : null;
    this.testing = null;
    this.testResults = null;
    this.testResultsFor = null;
    this.botSteps = this.bots.map((bot) => this.initialStepForBot(bot));
    if (this.bots.length === 0) this._startInitialBotFlow();
    this._installWizardFooter();
    this.didInit = true;

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
    if (this.context?.wizardFooter?.owner === "telegramConfig") {
      this.context.wizardFooter = null;
    }
    this.config = null;
    this.context = null;
    this.editing = null;
    this.testing = null;
    this.testResults = null;
    this.testResultsFor = null;
    this.botSteps = [];
    this.didInit = false;
  },

  defaultBot() {
    return {
      name: "",
      enabled: false,
      notify_messages: false,
      token: "",
      mode: "polling",
      webhook_url: "",
      webhook_secret: "",
      allowed_users: [],
      group_mode: "mention",
      welcome_enabled: false,
      welcome_message: "",
      user_projects: {},
      default_project: "",
      agent_instructions: "",
      attachment_max_age_hours: 0,
    };
  },

  addBot() {
    ensureConfig(this.config);
    this.config.bots.push(this.defaultBot());
    this.botSteps.push(0);
    this.editing = this.config.bots.length - 1;
    this.testResults = null;
    this.testResultsFor = null;
  },

  removeBot(idx) {
    this.bots.splice(idx, 1);
    this.botSteps.splice(idx, 1);
    if (this.editing === idx) this.editing = null;
    if (this.editing !== null && this.editing > idx) this.editing -= 1;
    if (this.testResultsFor === idx) {
      this.testResults = null;
      this.testResultsFor = null;
    }
  },

  toggleEditing(idx) {
    this.editing = this.editing === idx ? null : idx;
    if (this.editing !== null && typeof this.botSteps[this.editing] !== "number") {
      this.botSteps[this.editing] = this.initialStepForBot(this.bots[this.editing]);
    }
    if (this.testResultsFor !== idx) {
      this.testResults = null;
      this.testResultsFor = null;
    }
  },

  currentStepMeta() {
    return this.steps[this.currentStep] || this.steps[0];
  },

  setStep(step) {
    if (this.activeIndex < 0) return;
    const next = Math.max(0, Math.min(this.steps.length - 1, Number(step) || 0));
    this.botSteps[this.activeIndex] = next;
  },

  previousStep() {
    if (this.isFirstStep) return;
    this.setStep(this.currentStep - 1);
  },

  nextStep() {
    if (this.stepBlockedReason()) return;
    if (this.isLastStep) {
      this.editing = null;
      return;
    }
    this.setStep(this.currentStep + 1);
  },

  stepBlockedReason() {
    const bot = this.activeBot;
    if (!bot) return "";
    if (this.currentStep === 0 && !String(bot.token || "").trim()) {
      return "Add your bot token first.";
    }
    if (this.currentStep === 1 && bot.mode === "webhook" && !String(bot.webhook_url || "").trim()) {
      return "Add your webhook URL first.";
    }
    return "";
  },

  canTest(bot) {
    if (!bot) return false;
    if (!String(bot.token || "").trim()) return false;
    if (bot.mode === "webhook" && !String(bot.webhook_url || "").trim()) return false;
    return true;
  },

  botStatusLabel(bot) {
    if (!String(bot?.token || "").trim()) return "New";
    if (bot?.mode === "webhook" && !String(bot?.webhook_url || "").trim()) return "Needs URL";
    if (bot?.enabled && this.canTest(bot)) return "Live";
    if (this.canTest(bot)) return "Ready";
    return "Needs info";
  },

  botStatusTone(bot) {
    const label = this.botStatusLabel(bot);
    if (label === "Live") return "success";
    if (label === "Ready") return "ready";
    if (label === "New") return "muted";
    return "warning";
  },

  botTitle(bot, idx) {
    return String(bot?.name || "").trim() || `Bot ${idx + 1}`;
  },

  botSubtitle(bot) {
    const pieces = [bot.mode === "webhook" ? "Webhook" : "Polling"];
    pieces.push(Array.isArray(bot.allowed_users) && bot.allowed_users.length > 0 ? "Private access" : "Open access");
    if (bot.default_project) pieces.push(`Project: ${bot.default_project}`);
    return pieces.join(" · ");
  },

  whitelistText(bot) {
    return (bot.allowed_users || []).join(", ");
  },

  setWhitelist(bot, value) {
    bot.allowed_users = value
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item);
  },

  userProjectsText(bot) {
    return Object.entries(bot.user_projects || {})
      .map(([userId, project]) => `${userId}=${project}`)
      .join(", ");
  },

  setUserProjects(bot, value) {
    const mapping = {};
    value
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item)
      .forEach((item) => {
        const [userId, project] = item.split("=").map((part) => part.trim());
        if (userId) mapping[userId] = project || "";
      });
    bot.user_projects = mapping;
  },

  accessWarning(bot) {
    if (!bot?.enabled) return "";
    if (Array.isArray(bot.allowed_users) && bot.allowed_users.length > 0) return "";
    return "Allowed users is empty. Anyone who finds this bot can reach your Agent Zero.";
  },

  async testConnection(idx) {
    const bot = this.bots[idx];
    if (!this.canTest(bot)) return;

    this.testing = idx;
    this.testResults = null;
    this.testResultsFor = idx;

    try {
      this.testResults = await API.callJsonApi(`${API_BASE}/test_connection`, { bot });
    } catch (error) {
      this.testResults = {
        success: false,
        results: [{ test: "Telegram bot", ok: false, message: String(error) }],
      };
    }

    this.testing = null;
  },

  testButtonLabel(bot, idx) {
    if (this.testing === idx) return "Checking...";
    if (this.canTest(bot)) return "Check Telegram connection";
    return "Fill in the basics first";
  },

  testIntro() {
    return "We will validate the bot token with Telegram so you know this bot can connect.";
  },

  resultTitle(result) {
    return result.test || "Check";
  },

  resultMessage(result) {
    return result.message || (result.ok ? "Done." : "Something went wrong.");
  },

  initialStepForBot(bot) {
    return String(bot?.token || "").trim() ? 1 : 0;
  },

  _startInitialBotFlow() {
    this.addBot();
    if (!this.context) return;
    const toComparableJson = typeof this.context._toComparableJson === "function"
      ? this.context._toComparableJson.bind(this.context)
      : JSON.stringify;
    this.context.settingsSnapshotJson = toComparableJson(this.context.settings);
  },

  _installWizardFooter() {
    if (!this.context) return;
    this.context.wizardFooter = {
      owner: "telegramConfig",
      visible: () => this.showFooterNav,
      canGoBack: () => !this.isFirstStep,
      backLabel: () => "Back",
      note: () => this.footerStepLabel,
      showNext: () => this.showFooterNav && !this.isLastStep,
      nextLabel: () => this.nextButtonLabel,
      nextDisabled: () => this.nextDisabled,
      showSave: () => !this.showFooterNav || this.isLastStep,
      onBack: () => this.previousStep(),
      onNext: () => this.nextStep(),
    };
  },
});
