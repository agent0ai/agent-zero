import { createStore } from "/js/AlpineStore.js";
import {
  websocket,
  createCorrelationId,
  normalizeProducerOptions,
  validateServerEnvelope,
} from "/js/websocket.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

const MAX_PAYLOAD_BYTES = 50 * 1024 * 1024;
const TOAST_DURATION = 5;

function now() {
  return new Date().toISOString();
}

function payloadSize(value) {
  try {
    return new TextEncoder().encode(JSON.stringify(value ?? null)).length;
  } catch (_error) {
    return String(value ?? "").length * 2;
  }
}

async function showToast(type, message, title) {
  const normalized = (type || "info").toLowerCase();
  switch (normalized) {
    case "error":
      return notificationStore.frontendError(
        message,
        title || "Error",
        TOAST_DURATION
      );
    case "success":
      return notificationStore.frontendSuccess(
        message,
        title || "Success",
        TOAST_DURATION
      );
    case "warning":
      return notificationStore.frontendWarning(
        message,
        title || "Warning",
        TOAST_DURATION
      );
    case "info":
    default:
      return notificationStore.frontendInfo(
        message,
        title || "Info",
        TOAST_DURATION
      );
  }
}

const model = {
  logs: "",
  running: false,
  manualRunning: false,
  subscriptionCount: 0,
  lastAggregated: null,
  receivedBroadcasts: [],
  isEnabled: false,
  _serverRestartHandler: null,

  init() {
    const rootStore = window.Alpine?.store ? window.Alpine.store("root") : undefined;
    this.isEnabled = Boolean(window.runtimeInfo?.isDevelopment || rootStore?.isDevelopment);
    if (this.isEnabled) {
      this.appendLog("WebSocket tester harness ready.");
      if (this._serverRestartHandler) {
        websocket.off("server_restart", this._serverRestartHandler);
      }
      this._serverRestartHandler = (payload) => {
        try {
          const envelope = validateServerEnvelope(payload);
          this.appendLog(
            `server_restart received (runtimeId=${envelope.data.runtimeId ?? "unknown"})`,
          );
        } catch (error) {
          this.appendLog(`server_restart envelope invalid: ${error.message || error}`);
        }
      };
      websocket
        .on("server_restart", this._serverRestartHandler)
        .catch((error) => {
          this.appendLog(`Failed to subscribe to server_restart: ${error.message || error}`);
        });
    } else {
      this.appendLog("WebSocket tester harness is available only in development runtime.");
    }
  },

  detach() {
    if (this._serverRestartHandler) {
      websocket.off("server_restart", this._serverRestartHandler);
      this._serverRestartHandler = null;
    } else {
      websocket.off("server_restart");
    }
    websocket.off("ws_tester_broadcast");
    websocket.off("ws_tester_persistence");
    websocket.off("ws_tester_broadcast_demo");
  },

  appendLog(message) {
    this.logs += `[${now()}] ${message}\n`;
  },

  clearLog() {
    this.logs = "";
    this.appendLog("Log cleared.");
  },

  assertEnabled() {
    if (!this.isEnabled) {
      throw new Error("WebSocket harness is available only in development runtime.");
    }
  },

  async ensureConnected() {
    this.assertEnabled();
    if (!websocket.isConnected()) {
      this.appendLog("Connecting WebSocket client...");
      await websocket.connect();
      this.appendLog("Connected to WebSocket server.");
    }
  },

  async runAutomaticSuite() {
    this.assertEnabled();
    if (this.running) return;
    this.running = true;
    this.lastAggregated = null;
    this.receivedBroadcasts = [];

    const results = [];

    const steps = [
      this.testEmit.bind(this),
      this.testRequest.bind(this),
      this.testRequestTimeout.bind(this),
      this.testSubscriptionPersistence.bind(this),
      this.testRequestAll.bind(this),
    ];

    try {
      this.appendLog("Starting automatic WebSocket validation suite...");
      await this.ensureConnected();

      for (const step of steps) {
        const result = await step();
        results.push(result);
        if (!result.ok) {
          await showToast("warning", `Automatic suite halted: ${result.label} failed`, "WebSocket Harness");
          this.appendLog(`Automatic suite halted on step: ${result.label} (${result.error || 'unknown error'})`);
          this.running = false;
          return;
        }
      }

      await showToast("success", "Automatic WebSocket validation succeeded", "WebSocket Harness");
      this.appendLog("Automatic suite completed successfully.");
    } catch (error) {
      this.appendLog(`Automatic suite failed: ${error.message || error}`);
      await showToast("error", `Automatic suite failed: ${error.message || error}`, "WebSocket Harness");
    } finally {
      this.running = false;
    }
  },

  async manualStep(stepFn) {
    this.assertEnabled();
    if (this.manualRunning) return;
    this.manualRunning = true;
    try {
      await this.ensureConnected();
      const result = await stepFn();
      if (result.ok) {
        await showToast("success", `${result.label} succeeded`, "WebSocket Harness");
      } else {
        await showToast("warning", `${result.label} failed: ${result.error}`, "WebSocket Harness");
      }
    } catch (error) {
      await showToast("error", `${error.message || error}`, "WebSocket Harness");
      this.appendLog(`Manual step error: ${error.message || error}`);
    } finally {
      this.manualRunning = false;
    }
  },

  async testEmit() {
    const label = "Fire-and-forget emit";
    try {
      this.appendLog("Testing fire-and-forget emit...");
      await this.ensureSubscribed("ws_tester_broadcast", true);
      const emitOptions = normalizeProducerOptions({
        correlationId: createCorrelationId("harness-emit"),
      });
      await websocket.emit(
        "ws_tester_emit",
        { message: "emit-check", timestamp: now() },
        emitOptions,
      );
      const received = await this.waitForEvent(
        "ws_tester_broadcast",
        (_data, envelope) =>
          envelope?.data?.message === "emit-check" &&
          typeof envelope?.handlerId === "string" &&
          typeof envelope?.eventId === "string" &&
          typeof envelope?.correlationId === "string" &&
          typeof envelope?.ts === "string",
      );
      this.appendLog("Received broadcast echo with valid envelope metadata.");
      return { ok: received, label, error: received ? undefined : "Envelope validation failed" };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    }
  },

  async testRequest() {
    const label = "Request-response";
    try {
      this.appendLog("Testing request-response...");
      const requestOptions = normalizeProducerOptions({
        correlationId: createCorrelationId("harness-request"),
      });
      const response = await websocket.request(
        "ws_tester_request",
        { value: 42 },
        { ...requestOptions },
      );
      const delayedResponse = await websocket.request(
        "ws_tester_request_delayed",
        { delay_ms: 750 },
        { correlationId: createCorrelationId("harness-request-no-timeout") },
      );
      const first = response.results?.[0];
      const ok = Boolean(
        response?.correlationId &&
          Array.isArray(response.results) &&
          first?.ok === true &&
          first?.handlerId &&
          first?.correlationId === response.correlationId &&
          first?.data?.echo === 42,
      );
      const delayedOk = Boolean(
        Array.isArray(delayedResponse.results) &&
          delayedResponse.results[0]?.ok === true &&
          delayedResponse.results[0]?.data?.status === "delayed",
      );
      this.appendLog(`Request-response result: ${JSON.stringify(response)}`);
      this.appendLog(`Request-response (no-timeout) result: ${JSON.stringify(delayedResponse)}`);
      return {
        ok: ok && delayedOk,
        label,
        error: ok && delayedOk ? undefined : "Unexpected response payload or default timeout behaviour",
      };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    }
  },

  async testRequestTimeout() {
    const label = "Request timeout";
    try {
      this.appendLog("Testing request timeout...");
      let threw = false;
      try {
        const timeoutOptions = normalizeProducerOptions({
          correlationId: createCorrelationId("harness-timeout"),
        });
        await websocket.request(
          "ws_tester_request_delayed",
          { delay_ms: 2000 },
          { timeoutMs: 500, ...timeoutOptions },
        );
      } catch (error) {
        threw = error.message === "Request timeout";
        if (!threw) {
          throw error;
        }
      }
      if (threw) {
        this.appendLog("Timeout correctly triggered.");
        return { ok: true, label };
      }
      this.appendLog("Timeout test failed: request resolved unexpectedly.");
      return { ok: false, label, error: "Request resolved but should timeout" };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    }
  },

  async testSubscriptionPersistence() {
    const label = "Subscription persistence";
    try {
      this.appendLog("Testing subscription persistence across reconnect...");
      await this.ensureSubscribed("ws_tester_persistence", true);
      const emitOptions = normalizeProducerOptions({
        correlationId: createCorrelationId("harness-persistence"),
      });
      await websocket.emit("ws_tester_trigger_persistence", { phase: "before" }, emitOptions);
      await this.waitForEvent("ws_tester_persistence", (data) => data?.phase === "before");
      this.appendLog("Initial subscription event received.");

      websocket.socket.disconnect();
      this.appendLog("Disconnected socket manually.");
      await websocket.connect();
      this.appendLog("Reconnected socket.");

      await websocket.emit(
        "ws_tester_trigger_persistence",
        { phase: "after" },
        emitOptions,
      );
      const received = await this.waitForEvent("ws_tester_persistence", (data) => data?.phase === "after", 2000);
      this.appendLog("Post-reconnect event received.");
      return { ok: received, label, error: received ? undefined : "Callback not triggered after reconnect" };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    }
  },

  async testRequestAll() {
    const label = "requestAll aggregation";
    try {
      this.appendLog("Testing requestAll aggregation...");
      const options = normalizeProducerOptions({
        correlationId: createCorrelationId("harness-requestAll"),
      });
      const response = await websocket.requestAll(
        "ws_tester_request_all",
        { marker: "aggregate" },
        { timeoutMs: 2000, ...options },
      );
      this.lastAggregated = response;
      const ok = Array.isArray(response) &&
        response.length > 0 &&
        response.every((entry) =>
          typeof entry?.sid === "string" &&
          typeof entry?.correlationId === "string" &&
          Array.isArray(entry.results) &&
          entry.results.length > 0 &&
          entry.results.every((result) =>
            typeof result?.handlerId === "string" &&
            typeof result?.ok === "boolean" &&
            (result.ok || typeof result?.error?.code === "string") &&
            result?.correlationId === entry.correlationId,
          ),
        );
      this.appendLog(`requestAll response: ${JSON.stringify(response)}`);
      return { ok, label, error: ok ? undefined : "Aggregation payload missing expected metadata" };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    }
  },

  async ensureSubscribed(eventType, reset = false) {
    if (reset) {
      websocket.off(eventType);
    }
    await websocket.on(eventType, (payload) => {
      try {
        const envelope = validateServerEnvelope(payload);
        if (!this.receivedBroadcasts) {
          this.receivedBroadcasts = [];
        }
        this.receivedBroadcasts.push({ eventType, payload: envelope, timestamp: now() });
      } catch (error) {
        this.appendLog(`Received invalid envelope for ${eventType}: ${error.message || error}`);
      }
    });
  },

  waitForEvent(eventType, predicate, timeout = 1500) {
    return new Promise((resolve) => {
      let timer;
      const handler = (data) => {
        let envelope;
        try {
          envelope = validateServerEnvelope(data);
        } catch (error) {
          this.appendLog(`Skipping invalid envelope for ${eventType}: ${error.message || error}`);
          return;
        }

        if (predicate(envelope.data, envelope)) {
          websocket.off(eventType, handler);
          if (timer) clearTimeout(timer);
          resolve(true);
        }
      };

      websocket.on(eventType, handler);

      timer = setTimeout(() => {
        websocket.off(eventType, handler);
        resolve(false);
      }, timeout);
    });
  },

  async runManualEmit() {
    await this.manualStep(this.testEmit.bind(this));
  },

  async runManualRequest() {
    await this.manualStep(this.testRequest.bind(this));
  },

  async runManualRequestTimeout() {
    await this.manualStep(this.testRequestTimeout.bind(this));
  },

  async runManualPersistence() {
    await this.manualStep(this.testSubscriptionPersistence.bind(this));
  },

  async runManualRequestAll() {
    await this.manualStep(this.testRequestAll.bind(this));
  },

  async triggerBroadcastDemo() {
    this.assertEnabled();
    try {
      await this.ensureConnected();
      await this.ensureSubscribed("ws_tester_broadcast_demo");
      const options = normalizeProducerOptions({
        correlationId: createCorrelationId("harness-demo"),
      });
      await websocket.emit(
        "ws_tester_broadcast_demo_trigger",
        { requested_at: now() },
        options,
      );
      await showToast("info", "Broadcast demo triggered. Check log output.", "WebSocket Harness");
    } catch (error) {
      await showToast("error", `Broadcast demo failed: ${error.message || error}`, "WebSocket Harness");
      this.appendLog(`Broadcast demo failed: ${error.message || error}`);
    }
  },

  payloadSizePreview(input) {
    return payloadSize(input);
  },
};

const store = createStore("websocketTesterStore", model);
export { store };
