import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";

const API_PATH = "/plugins/_context_window/context_window";
const ROWS = [
  { key: "messages", label: "Messages" },
  { key: "system_tools", label: "System tools" },
  { key: "skills", label: "Skills" },
  { key: "mcp_tools", label: "MCP tools" },
  { key: "system_prompt", label: "System prompt" },
  { key: "extras", label: "Extras" },
];
const COST_FORMATTER = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumSignificantDigits: 3,
});

preferencesStore.registerUiControlVisibility("contextWindowUsage", {
  mobile: true,
  desktop: true,
});

function formatTokens(value) {
  const amount = Math.max(Number(value) || 0, 0);
  for (const [size, suffix] of [[1_000_000, "M"], [1_000, "K"]]) {
    if (amount >= size) return `${(amount / size).toFixed(1).replace(/\.0$/, "")}${suffix}`;
  }
  return String(Math.round(amount));
}

function formatPercent(value) {
  const rounded = Math.round(Math.max(Number(value) || 0, 0) * 10) / 10;
  return `${Number.isInteger(rounded) ? rounded.toFixed(0) : rounded.toFixed(1)}%`;
}

function optionalNumber(value, key) {
  if (!value || !Object.prototype.hasOwnProperty.call(value, key)) return null;
  const number = Number(value[key]);
  return Number.isFinite(number) && number >= 0 ? number : null;
}

function formatCost(value) {
  if (value === 0) return "$0";
  return value < 0.001 ? "<$0.001" : COST_FORMATTER.format(value);
}

function buildProviderUsage(value = {}) {
  const input = optionalNumber(value, "input_tokens");
  const cached = optionalNumber(value, "cached_tokens");
  const output = optionalNumber(value, "output_tokens");
  const cost = optionalNumber(value, "cost");

  const tokenSummary = input === null && output === null
    ? ""
    : `${input === null ? "–" : formatTokens(input)} → ${output === null ? "–" : formatTokens(output)}`;

  const cachePercent = input > 0 && cached !== null
    ? Math.min((cached / input) * 100, 100)
    : null;
  return {
    hasData: cost !== null || cachePercent !== null || Boolean(tokenSummary),
    price: {
      hasData: cost !== null,
      label: cost === null ? "" : formatCost(cost),
    },
    cache: {
      hasData: cachePercent !== null,
      label: cachePercent === null ? "" : `${Math.round(cachePercent)}%`,
    },
    tokens: tokenSummary,
  };
}

function buildUsage(data = {}) {
  const tokens = Math.max(Number(data.tokens) || 0, 0);
  const contextWindow = Math.max(Number(data.context_window) || 0, 0);
  const breakdown = data.usage && typeof data.usage === "object" ? data.usage : {};
  const percent = contextWindow > 0 ? (tokens / contextWindow) * 100 : 0;
  const rows = ROWS.map(row => {
    const rowTokens = Math.max(Number(breakdown[row.key]) || 0, 0);
    const rowPercent = contextWindow > 0 ? (rowTokens / contextWindow) * 100 : 0;
    return {
      ...row,
      tokensLabel: formatTokens(rowTokens),
      percentLabel: formatPercent(rowPercent),
    };
  });
  const hasBreakdown = rows.some(row => Number(breakdown[row.key]) > 0);
  if (hasBreakdown) {
    const freeTokens = Math.max(contextWindow - tokens, 0);
    const freePercent = contextWindow > 0 ? (freeTokens / contextWindow) * 100 : 0;
    rows.push({
      key: "free_space",
      label: "Free space",
      tokensLabel: formatTokens(freeTokens),
      percentLabel: formatPercent(freePercent),
    });
  }
  const percentLabel = formatPercent(percent);
  return {
    rows: hasBreakdown ? rows : [],
    hasBreakdown,
    missingBreakdown: !hasBreakdown,
    ariaLabel: `Context window ${percentLabel} used`,
    ringLabel: contextWindow ? `${Math.round(percent)}%` : "–",
    ringDasharray: `${Math.min(percent, 100)} 100`,
    summaryTokens: `${formatTokens(tokens)}/${contextWindow ? formatTokens(contextWindow) : "–"} tokens`,
    summaryPercent: `${percentLabel} used`,
    meterStyle: `width:${Math.min(percent, 100)}%`,
    provider: buildProviderUsage(data.provider_usage),
  };
}

const model = {
  usage: buildUsage(),
  loadSeq: 0,
  open: false,

  get contextId() {
    return chatsStore?.getSelectedChatId?.() || globalThis.getContext?.() || "";
  },

  async onMount(watch) {
    await this.refresh();
    watch("$store.chats.selected", value => this.refresh(value || ""));
    watch("$store.chats.selectedContext?.running", (running, previous) => {
      if (previous && !running) void this.refresh();
    });
  },

  cleanup() {
    this.open = false;
    this.loadSeq += 1;
  },

  toggle() {
    this.open = !this.open;
    if (this.open) void this.refresh();
  },

  async refresh(contextId = this.contextId) {
    const requestSeq = ++this.loadSeq;
    if (!contextId) {
      this.usage = buildUsage();
      return this.usage;
    }
    try {
      const data = await callJsonApi(API_PATH, { context: contextId });
      if (requestSeq === this.loadSeq) this.usage = buildUsage(data);
    } catch (error) {
      if (requestSeq === this.loadSeq) console.error("Context window load failed:", error);
    }
    return this.usage;
  },
};

export const store = createStore("contextWindow", model);
