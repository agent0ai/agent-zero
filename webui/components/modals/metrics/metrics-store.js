import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";

const metricsStore = {
  loading: false,
  error: null,
  activeTab: "overview",

  // Snapshot data
  totalCalls: 0,
  successCalls: 0,
  failedCalls: 0,
  totalTokensIn: 0,
  totalTokensOut: 0,
  avgLatency: 0,
  p50Latency: 0,
  p95Latency: 0,
  p99Latency: 0,
  byModel: [],
  timeline: [],
  recentErrors: [],
  recentEvents: [],
  uptimeSeconds: 0,
  bufferSize: 0,
  bufferCapacity: 0,

  // Polling
  _pollTimer: null,

  switchTab(tab) {
    this.activeTab = tab;
  },

  async fetchMetrics() {
    try {
      this.loading = true;
      const resp = await API.callJsonApi("/metrics_dashboard", { action: "snapshot" });
      if (resp.success) {
        this.totalCalls = resp.total_calls;
        this.successCalls = resp.success_calls;
        this.failedCalls = resp.failed_calls;
        this.totalTokensIn = resp.total_tokens_in;
        this.totalTokensOut = resp.total_tokens_out;
        this.avgLatency = resp.avg_latency_ms;
        this.p50Latency = resp.p50_latency_ms;
        this.p95Latency = resp.p95_latency_ms;
        this.p99Latency = resp.p99_latency_ms;
        this.byModel = resp.by_model;
        this.timeline = resp.timeline;
        this.recentErrors = resp.recent_errors;
        this.recentEvents = resp.recent_events;
        this.uptimeSeconds = resp.uptime_seconds;
        this.bufferSize = resp.buffer_size;
        this.bufferCapacity = resp.buffer_capacity;
      }
      this.error = null;
    } catch (e) {
      this.error = e.message;
    } finally {
      this.loading = false;
    }
  },

  async clearMetrics() {
    try {
      await API.callJsonApi("/metrics_dashboard", { action: "clear" });
      await this.fetchMetrics();
    } catch (e) {
      this.error = e.message;
    }
  },

  onOpen() {
    this.fetchMetrics();
    this._pollTimer = setInterval(() => this.fetchMetrics(), 5000);
  },

  cleanup() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
  },

  // Formatting helpers
  fmtNum(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
    return String(n);
  },

  fmtLatency(ms) {
    if (ms >= 60_000) return (ms / 60_000).toFixed(1) + "m";
    if (ms >= 1000) return (ms / 1000).toFixed(1) + "s";
    return ms + "ms";
  },

  fmtUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h > 0) return h + "h " + m + "m";
    return m + "m";
  },

  successRate() {
    if (this.totalCalls === 0) return "—";
    return ((this.successCalls / this.totalCalls) * 100).toFixed(1) + "%";
  },

  fmtTime(ts) {
    if (!ts) return "";
    try {
      const d = new Date(ts.endsWith("Z") ? ts : ts + "Z");
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return ts;
    }
  },

  // Mini sparkline SVG for timeline
  sparklinePath(data, key, width, height) {
    if (!data || data.length < 2) return "";
    const values = data.map(d => d[key] || 0);
    const max = Math.max(...values, 1);
    const step = width / (values.length - 1);
    let path = "";
    values.forEach((v, i) => {
      const x = i * step;
      const y = height - (v / max) * height;
      path += (i === 0 ? "M" : "L") + x.toFixed(1) + "," + y.toFixed(1);
    });
    return path;
  },
};

export const store = createStore("metricsDashboard", metricsStore);
