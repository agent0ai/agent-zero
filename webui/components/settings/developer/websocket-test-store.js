import { createStore } from "/js/AlpineStore.js";
import {
  getNamespacedClient,
  createCorrelationId,
  validateServerEnvelope,
} from "/js/websocket.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

const MAX_PAYLOAD_BYTES = 50 * 1024 * 1024;
const TOAST_DURATION = 5;

const websocket = getNamespacedClient("/dev_websocket_test");
const stateSocket = getNamespacedClient("/state_sync");

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

function clientForEventType(eventType) {
  if (typeof eventType === "string" && eventType.startsWith("state_")) {
    return stateSocket;
  }
  return websocket;
}

async function showToast(type, message, title) {
  const normalized = (type || "info").toLowerCase();
  switch (normalized) {
    case "error":
      return notificationStore.addFrontendToastOnly(
        "error",
        message,
        title || "Error",
        TOAST_DURATION,
        "ws-harness",
        10,
      );
    case "success":
      return notificationStore.addFrontendToastOnly(
        "success",
        message,
        title || "Success",
        TOAST_DURATION,
        "ws-harness",
        10,
      );
    case "warning":
      return notificationStore.addFrontendToastOnly(
        "warning",
        message,
        title || "Warning",
        TOAST_DURATION,
        "ws-harness",
        10,
      );
    case "info":
    default:
      return notificationStore.addFrontendToastOnly(
        "info",
        message,
        title || "Info",
        TOAST_DURATION,
        "ws-harness",
        10,
      );
  }
}

function withTimeout(promise, timeoutMs, label) {
  const normalizedTimeout = Number(timeoutMs);
  if (!Number.isFinite(normalizedTimeout) || normalizedTimeout <= 0) {
    return Promise.resolve(promise);
  }
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`${label} timed out after ${normalizedTimeout}ms`));
    }, normalizedTimeout);
    Promise.resolve(promise).then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      },
    );
  });
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
  _subscriptionHandlers: null,
  _broadcastSeq: 0,

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
    if (this._subscriptionHandlers && typeof this._subscriptionHandlers === "object") {
      for (const [eventType, handler] of Object.entries(this._subscriptionHandlers)) {
        if (typeof handler === "function") {
          clientForEventType(eventType).off(eventType, handler);
        }
      }
      this._subscriptionHandlers = null;
    }
    if (this._serverRestartHandler) {
      websocket.off("server_restart", this._serverRestartHandler);
      this._serverRestartHandler = null;
    } else {
      websocket.off("server_restart");
    }
    // Legacy cleanup: ensure we do not leave stray tester handlers attached.
    websocket.off("ws_tester_broadcast");
    websocket.off("ws_tester_persistence");
    websocket.off("ws_tester_broadcast_demo");
    stateSocket.off("state_push");
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
      await withTimeout(websocket.connect(), 5000, "websocket.connect");
      this.appendLog("Connected to WebSocket server.");
    }
  },

  async _toast(type, message, title) {
    try {
      await showToast(type, message, title);
    } catch (error) {
      this.appendLog(`Toast failed: ${error.message || error}`);
    }
  },

  async runAutomaticSuite() {
    this.assertEnabled();
    if (this.running) return;
    this.running = true;
    this.lastAggregated = null;
    this.receivedBroadcasts = [];
    this._broadcastSeq = 0;

    const results = [];

    const steps = [
      this.testEmit.bind(this),
      this.testRequest.bind(this),
      this.testRequestTimeout.bind(this),
      this.testSubscriptionPersistence.bind(this),
      this.testRequestAll.bind(this),
      this.testStateSyncNoPollHealthy.bind(this),
      this.testContextSwitchNoLeak.bind(this),
      this.testFallbackRecoveryDegraded.bind(this),
      this.testResyncTriggersRuntimeEpochAndSeqGap.bind(this),
    ];

    try {
      this.appendLog("Starting automatic WebSocket validation suite...");
      await this.ensureConnected();

      for (const step of steps) {
        const result = await step();
        results.push(result);
        if (!result.ok) {
          await this._toast("warning", `Automatic suite halted: ${result.label} failed`, "WebSocket Harness");
          this.appendLog(`Automatic suite halted on step: ${result.label} (${result.error || 'unknown error'})`);
          this.running = false;
          return;
        }
      }

      await this._toast("success", "Automatic WebSocket validation succeeded", "WebSocket Harness");
      this.appendLog("Automatic suite completed successfully.");
    } catch (error) {
      this.appendLog(`Automatic suite failed: ${error.message || error}`);
      await this._toast("error", `Automatic suite failed: ${error.message || error}`, "WebSocket Harness");
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
      this.appendLog(
        `${result.ok ? "PASS" : "FAIL"} - ${result.label}${result.error ? `: ${result.error}` : ""}`,
      );
      if (result.ok) {
        await this._toast("success", `${result.label} succeeded`, "WebSocket Harness");
      } else {
        await this._toast("warning", `${result.label} failed: ${result.error}`, "WebSocket Harness");
      }
    } catch (error) {
      await this._toast("error", `${error.message || error}`, "WebSocket Harness");
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
      const emitOptions = {
        correlationId: createCorrelationId("harness-emit"),
      };
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
      const requestOptions = {
        correlationId: createCorrelationId("harness-request"),
      };
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
        const timeoutOptions = {
          correlationId: createCorrelationId("harness-timeout"),
        };
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
      const emitOptions = {
        correlationId: createCorrelationId("harness-persistence"),
      };
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
      const options = {
        correlationId: createCorrelationId("harness-requestAll"),
      };
      const response = await websocket.request(
        "ws_tester_request_all",
        { marker: "aggregate" },
        { timeoutMs: 2000, ...options },
      );
      this.lastAggregated = response;

      const first = response?.results?.[0];
      const aggregated = first?.ok === true ? first?.data?.results : null;
      const ok =
        Array.isArray(aggregated) &&
        aggregated.length > 0 &&
        aggregated.every(
          (entry) =>
            typeof entry?.sid === "string" &&
            typeof entry?.correlationId === "string" &&
            Array.isArray(entry.results) &&
            entry.results.length > 0,
        );

      this.appendLog(`ws_tester_request_all response: ${JSON.stringify(response)}`);
      return { ok, label, error: ok ? undefined : "Aggregation payload missing expected metadata" };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    }
  },

  async testStateSyncNoPollHealthy() {
    const label = "State sync (state_request/state_push + no poll when HEALTHY)";
    const originalPoll = globalThis.poll;
    let pollCalls = 0;
    try {
      this.appendLog("Testing state_request/state_push contract and healthy-mode poll suppression...");

      if (typeof originalPoll === "function") {
        globalThis.poll = async (...args) => {
          pollCalls += 1;
          return await originalPoll(...args);
        };
      }

      await this.ensureSubscribed("state_push", true);
      this.appendLog("Subscribed to state_push.");

      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const response = await stateSocket.request(
        "state_request",
        {
          context: globalThis.getContext ? globalThis.getContext() : null,
          log_from: 0,
          notifications_from: 0,
          timezone,
        },
        { timeoutMs: 2000, correlationId: createCorrelationId("harness-state-request") },
      );

      const first = response?.results?.[0];
      const requestOk = Boolean(
        response?.correlationId &&
          first?.ok === true &&
          typeof first?.data?.runtime_epoch === "string" &&
          typeof first?.data?.seq_base === "number",
      );
      if (!requestOk) {
        this.appendLog(`state_request response invalid: ${JSON.stringify(response)}`);
        return { ok: false, label, error: "state_request did not return expected {runtime_epoch, seq_base}" };
      }
      this.appendLog("state_request OK.");

      const start = Date.now();
      let pushOk = false;
      while (Date.now() - start < 1000) {
        const hit = this.receivedBroadcasts.find(
          (entry) =>
            entry.eventType === "state_push" &&
            typeof entry?.payload?.data?.runtime_epoch === "string" &&
            typeof entry?.payload?.data?.seq === "number" &&
            entry?.payload?.data?.snapshot &&
            typeof entry?.payload?.data?.snapshot === "object" &&
            Array.isArray(entry?.payload?.data?.snapshot?.contexts) &&
            Array.isArray(entry?.payload?.data?.snapshot?.tasks) &&
            Array.isArray(entry?.payload?.data?.snapshot?.notifications),
        );
        if (hit) {
          pushOk = true;
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 25));
      }

      if (!pushOk) {
        return { ok: false, label, error: "Did not observe state_push within 1s after handshake" };
      }
      this.appendLog("state_push observed.");

      const syncStore =
        globalThis.Alpine && typeof globalThis.Alpine.store === "function"
          ? globalThis.Alpine.store("sync")
          : null;
      // The sync store applies snapshots asynchronously; give it a moment to
      // reach HEALTHY before asserting poll suppression.
      if (syncStore) {
        const startedHealthyWait = Date.now();
        while (Date.now() - startedHealthyWait < 1000 && syncStore.mode !== "HEALTHY") {
          await new Promise((resolve) => setTimeout(resolve, 25));
        }
      }
      const healthy = Boolean(syncStore && syncStore.mode === "HEALTHY");
      if (!healthy) {
        const mode = syncStore && typeof syncStore.mode === "string" ? syncStore.mode : "missing";
        return { ok: false, label, error: `syncStore did not reach HEALTHY mode (mode=${mode})` };
      }

      // Reset count after the store is HEALTHY; then observe for >1 poll interval.
      pollCalls = 0;
      await new Promise((resolve) => setTimeout(resolve, 600));
      const noPoll = pollCalls === 0;
      if (!noPoll) {
        return { ok: false, label, error: `poll() invoked ${pollCalls}x while HEALTHY` };
      }

      return { ok: true, label };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    } finally {
      if (typeof originalPoll === "function") {
        globalThis.poll = originalPoll;
      }
    }
  },

  async testContextSwitchNoLeak() {
    const label = "Context switching (state_request updates active context, no stale pushes)";
    const originalContext = typeof globalThis.getContext === "function" ? globalThis.getContext() : null;
    try {
      this.appendLog("Testing context switching does not leak or keep pushing stale contexts...");
      await this.ensureSubscribed("state_push", true);

      const chatsStore =
        globalThis.Alpine && typeof globalThis.Alpine.store === "function"
          ? globalThis.Alpine.store("chats")
          : null;
      if (!chatsStore || !Array.isArray(chatsStore.contexts)) {
        return { ok: false, label, error: "chats store not available" };
      }

      const ids = chatsStore.contexts
        .map((ctx) => ctx?.id)
        .filter((id) => typeof id === "string" && id.length > 0);
      const unique = Array.from(new Set(ids));
      if (unique.length < 2) {
        return { ok: false, label, error: "Need at least 2 chats to validate switching" };
      }

      const current = typeof originalContext === "string" ? originalContext : null;
      let first = unique[0];
      let second = unique[1];
      if (current && unique.includes(current)) {
        const alternate = unique.find((id) => id !== current);
        if (!alternate) {
          return { ok: false, label, error: "Need at least 2 distinct chats to validate switching" };
        }
        first = alternate;
        second = current;
      }

      const switchTo = async (ctxid) => {
        if (typeof chatsStore.selectChat === "function") {
          await chatsStore.selectChat(ctxid);
          return;
        }
        if (typeof globalThis.setContext === "function") {
          globalThis.setContext(ctxid);
          return;
        }
        throw new Error("No chat selection function available");
      };

      const waitForContextPush = async (ctxid, timeoutMs = 2000) => {
        return await this.waitForEvent(
          "state_push",
          (data) => data?.snapshot?.context === ctxid,
          timeoutMs,
        );
      };

      const waitFirst = waitForContextPush(first, 2500);
      await switchTo(first);
      const gotFirst = await waitFirst;
      if (!gotFirst) {
        return { ok: false, label, error: "Did not observe state_push for first context after switch" };
      }

      const switchedAt = Date.now();
      const waitSecond = waitForContextPush(second, 2500);
      await switchTo(second);
      const gotSecond = await waitSecond;
      if (!gotSecond) {
        return { ok: false, label, error: "Did not observe state_push for second context after switch" };
      }

      // After switching, we should not observe new pushes for the old context.
      await new Promise((resolve) => setTimeout(resolve, 300));
      const stale = this.receivedBroadcasts.find((entry) => {
        if (entry.eventType !== "state_push") return false;
        const timestamp = Date.parse(entry.timestamp);
        if (!Number.isFinite(timestamp) || timestamp < switchedAt) return false;
        return entry?.payload?.data?.snapshot?.context === first;
      });
      if (stale) {
        return { ok: false, label, error: "Observed state_push for previous context after switching" };
      }

      return { ok: true, label };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    } finally {
      if (originalContext && typeof originalContext === "string") {
        try {
          const chatsStore =
            globalThis.Alpine && typeof globalThis.Alpine.store === "function"
              ? globalThis.Alpine.store("chats")
              : null;
          if (chatsStore && typeof chatsStore.selectChat === "function") {
            await chatsStore.selectChat(originalContext);
          } else if (typeof globalThis.setContext === "function") {
            globalThis.setContext(originalContext);
          }
        } catch (_error) {
          // no-op
        }
      }
    }
  },

  async testFallbackRecoveryDegraded() {
    const label = "Fallback + recovery (DEGRADED polling, ignore pushes)";
    const originalPoll = globalThis.poll;
    const originalRequest = stateSocket.request;
    try {
      const syncStore =
        globalThis.Alpine && typeof globalThis.Alpine.store === "function"
          ? globalThis.Alpine.store("sync")
          : null;
      if (!syncStore) {
        return { ok: false, label, error: "sync store not available" };
      }
      if (typeof syncStore.sendStateRequest !== "function") {
        return { ok: false, label, error: "syncStore.sendStateRequest not available" };
      }

      // Ensure we start from a known-good state.
      await syncStore.sendStateRequest({ forceFull: true });
      if (syncStore.mode !== "HEALTHY") {
        return { ok: false, label, error: `Expected HEALTHY before test, got ${syncStore.mode}` };
      }

      // Stub poll to avoid network side-effects and track calls.
      let pollCalls = 0;
      globalThis.poll = async () => {
        pollCalls += 1;
        return { ok: true, updated: false };
      };

      // Simulate state_request failures to force DEGRADED mode.
      stateSocket.request = async (eventType, payload, options) => {
        if (eventType === "state_request") {
          throw new Error("Request timeout");
        }
        return await originalRequest.call(stateSocket, eventType, payload, options);
      };

      let threw = false;
      try {
        await syncStore.sendStateRequest({ forceFull: true });
      } catch (_error) {
        threw = true;
      }
      if (!threw) {
        return { ok: false, label, error: "Expected state_request failure but request succeeded" };
      }

      if (syncStore.mode !== "DEGRADED") {
        return { ok: false, label, error: `Expected DEGRADED after failure, got ${syncStore.mode}` };
      }
      this.appendLog("Entered DEGRADED mode after simulated state_request failure.");

      // Poll fallback should kick in quickly (1Hz idle); wait long enough for at least one tick.
      await new Promise((resolve) => setTimeout(resolve, 1200));
      if (pollCalls < 1) {
        return { ok: false, label, error: "poll() was not invoked while DEGRADED" };
      }

      // While DEGRADED, pushes should be ignored (single-writer arbitration).
      const lastSeqBefore = typeof syncStore.lastSeq === "number" ? syncStore.lastSeq : 0;
      await syncStore._handlePush({
        data: {
          runtime_epoch: typeof syncStore.runtimeEpoch === "string" ? syncStore.runtimeEpoch : "test-epoch",
          seq: lastSeqBefore + 1,
          snapshot: { ignored: true },
        },
      });
      if (syncStore.lastSeq !== lastSeqBefore) {
        return { ok: false, label, error: "state_push advanced seq while DEGRADED (should be ignored)" };
      }
      this.appendLog("Verified state_push ignored while DEGRADED.");

      // Recover: restore request path and confirm we return to HEALTHY and polling stops.
      stateSocket.request = originalRequest;
      await syncStore.sendStateRequest({ forceFull: true });
      if (syncStore.mode !== "HEALTHY") {
        return { ok: false, label, error: `Expected HEALTHY after recovery, got ${syncStore.mode}` };
      }

      pollCalls = 0;
      await new Promise((resolve) => setTimeout(resolve, 600));
      if (pollCalls !== 0) {
        return { ok: false, label, error: `poll() invoked ${pollCalls}x after recovery to HEALTHY` };
      }

      return { ok: true, label };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    } finally {
      stateSocket.request = originalRequest;
      globalThis.poll = originalPoll;
    }
  },

  async testResyncTriggersRuntimeEpochAndSeqGap() {
    const label = "Resync triggers (runtime_epoch mismatch + seq gap)";
    const syncStore =
      globalThis.Alpine && typeof globalThis.Alpine.store === "function"
        ? globalThis.Alpine.store("sync")
        : null;
    if (!syncStore) {
      return { ok: false, label, error: "sync store not available" };
    }
    if (typeof syncStore._handlePush !== "function") {
      return { ok: false, label, error: "syncStore._handlePush not available" };
    }
    const originalSendStateRequest = syncStore.sendStateRequest;
    let calls = [];
    try {
      if (typeof originalSendStateRequest !== "function") {
        return { ok: false, label, error: "syncStore.sendStateRequest not available" };
      }

      syncStore.sendStateRequest = async (options = {}) => {
        calls.push(options);
      };

      // Case 1: runtime_epoch mismatch should trigger resync.
      calls = [];
      syncStore.mode = "HEALTHY";
      syncStore.runtimeEpoch = "epoch-a";
      syncStore.lastSeq = 10;
      await syncStore._handlePush({ data: { runtime_epoch: "epoch-b", seq: 11 } });
      const runtimeTriggered = calls.length === 1 && calls[0] && calls[0].forceFull === true;
      if (!runtimeTriggered) {
        return { ok: false, label, error: "runtime_epoch mismatch did not trigger state_request resync" };
      }
      if (syncStore.mode !== "HANDSHAKE_PENDING") {
        return { ok: false, label, error: "runtime_epoch resync did not set HANDSHAKE_PENDING" };
      }

      // Case 2: seq gap should trigger resync.
      calls = [];
      syncStore.mode = "HEALTHY";
      syncStore.runtimeEpoch = "epoch-a";
      syncStore.lastSeq = 10;
      await syncStore._handlePush({ data: { runtime_epoch: "epoch-a", seq: 12 } });
      const seqTriggered = calls.length === 1 && calls[0] && calls[0].forceFull === true;
      if (!seqTriggered) {
        return { ok: false, label, error: "seq gap did not trigger state_request resync" };
      }
      if (syncStore.mode !== "HANDSHAKE_PENDING") {
        return { ok: false, label, error: "seq gap resync did not set HANDSHAKE_PENDING" };
      }

      return { ok: true, label };
    } catch (error) {
      this.appendLog(`${label} failed: ${error.message || error}`);
      return { ok: false, label, error: error.message || error };
    } finally {
      syncStore.sendStateRequest = originalSendStateRequest;
    }
  },

  async ensureSubscribed(eventType, reset = false) {
    if (!this._subscriptionHandlers || typeof this._subscriptionHandlers !== "object") {
      this._subscriptionHandlers = {};
    }

    const existing = this._subscriptionHandlers[eventType];
    if (reset && typeof existing === "function") {
      clientForEventType(eventType).off(eventType, existing);
      delete this._subscriptionHandlers[eventType];
    } else if (!reset && typeof existing === "function") {
      return;
    }

    const handler = (payload) => {
      try {
        const envelope = validateServerEnvelope(payload);
        if (!Array.isArray(this.receivedBroadcasts)) {
          this.receivedBroadcasts = [];
        }
        this._broadcastSeq = (this._broadcastSeq || 0) + 1;
        const id = envelope?.eventId
          ? `${eventType}-${envelope.eventId}`
          : `${eventType}-${this._broadcastSeq}`;
        this.receivedBroadcasts.push({
          id,
          eventType,
          payload: envelope,
          timestamp: now(),
        });
      } catch (error) {
        this.appendLog(`Received invalid envelope for ${eventType}: ${error.message || error}`);
      }
    };

    this._subscriptionHandlers[eventType] = handler;
    await clientForEventType(eventType).on(eventType, handler);
  },

  waitForEvent(eventType, predicate, timeout = 1500) {
    return new Promise((resolve) => {
      const client = clientForEventType(eventType);
      let timer;
      let done = false;
      let handler = null;

      const finish = (ok) => {
        if (done) return;
        done = true;
        if (timer) clearTimeout(timer);
        if (typeof handler === "function") {
          client.off(eventType, handler);
        }
        resolve(ok);
      };

      handler = (data) => {
        let envelope;
        try {
          envelope = validateServerEnvelope(data);
        } catch (error) {
          this.appendLog(`Skipping invalid envelope for ${eventType}: ${error.message || error}`);
          return;
        }

        if (predicate(envelope.data, envelope)) {
          finish(true);
        }
      };

      const onPromise = client.on(eventType, handler);
      if (onPromise && typeof onPromise.then === "function") {
        onPromise.catch((error) => {
          this.appendLog(`Failed to subscribe to ${eventType}: ${error.message || error}`);
          finish(false);
        });
      }

      timer = setTimeout(() => {
        finish(false);
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

  async runManualStateSync() {
    await this.manualStep(this.testStateSyncNoPollHealthy.bind(this));
  },

  async runManualContextSwitch() {
    await this.manualStep(this.testContextSwitchNoLeak.bind(this));
  },

  async runManualFallbackRecovery() {
    await this.manualStep(this.testFallbackRecoveryDegraded.bind(this));
  },

  async runManualResyncTriggers() {
    await this.manualStep(this.testResyncTriggersRuntimeEpochAndSeqGap.bind(this));
  },

  async triggerBroadcastDemo() {
    this.assertEnabled();
    try {
      await this.ensureConnected();
      await this.ensureSubscribed("ws_tester_broadcast_demo");
      const options = {
        correlationId: createCorrelationId("harness-demo"),
      };
      await websocket.emit(
        "ws_tester_broadcast_demo_trigger",
        { requested_at: now() },
        options,
      );
      await this._toast("info", "Broadcast demo triggered. Check log output.", "WebSocket Harness");
    } catch (error) {
      await this._toast("error", `Broadcast demo failed: ${error.message || error}`, "WebSocket Harness");
      this.appendLog(`Broadcast demo failed: ${error.message || error}`);
    }
  },

  payloadSizePreview(input) {
    return payloadSize(input);
  },
};

const store = createStore("websocketTesterStore", model);
export { store };
