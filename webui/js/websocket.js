import { io } from "/vendor/socket.io.esm.min.js";
import { callJsonApi, invalidateCsrfToken } from "/js/api.js";

const MAX_PAYLOAD_BYTES = 50 * 1024 * 1024; // 50MB hard cap per contract
const DEFAULT_TIMEOUT_MS = 0;

const _UUID_HEX = [..."0123456789abcdef"];
const _OPTION_KEYS = new Set([
  "includeHandlers",
  "excludeHandlers",
  "excludeSids",
  "correlationId",
]);

/**
 * @param {unknown} value
 * @param {string} fieldName
 * @returns {Record<string, any>}
 */
function assertPlainObject(value, fieldName) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${fieldName} must be a plain object`);
  }
  return /** @type {Record<string, any>} */ (value);
}

/**
 * @returns {string}
 */
function generateUuid() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  const buffer = new Uint8Array(16);
  if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
    crypto.getRandomValues(buffer);
  } else {
    for (let i = 0; i < buffer.length; i += 1) {
      buffer[i] = Math.floor(Math.random() * 256);
    }
  }

  buffer[6] = (buffer[6] & 0x0f) | 0x40; // version 4
  buffer[8] = (buffer[8] & 0x3f) | 0x80; // variant 10

  let uuid = "";
  for (let i = 0; i < buffer.length; i += 1) {
    if (i === 4 || i === 6 || i === 8 || i === 10) {
      uuid += "-";
    }
    uuid += _UUID_HEX[buffer[i] >> 4];
    uuid += _UUID_HEX[buffer[i] & 0x0f];
  }
  return uuid;
}

/**
 * @param {unknown} value
 * @param {string} fieldName
 * @param {{ allowEmpty?: boolean }} [options]
 * @returns {string[] | undefined}
 */
function normalizeStringList(value, fieldName, options = {}) {
  if (value == null) return undefined;
  const raw = Array.isArray(value) ? value : [value];
  const normalized = [];
  for (const item of raw) {
    if (typeof item !== "string" || item.trim().length === 0) {
      throw new Error(`${fieldName} must contain non-empty strings`);
    }
    normalized.push(item.trim());
  }
  const deduped = Array.from(new Set(normalized));
  if (!options.allowEmpty && deduped.length === 0) {
    throw new Error(`${fieldName} must contain at least one value`);
  }
  return deduped.length > 0 ? deduped : undefined;
}

/**
 * @param {unknown} value
 * @returns {string[] | undefined}
 */
function normalizeSidList(value) {
  return normalizeStringList(value, "excludeSids", { allowEmpty: true });
}

/**
 * @param {unknown} value
 * @returns {string | undefined}
 */
function normalizeCorrelationId(value) {
  if (value == null) return undefined;
  if (typeof value !== "string") {
    throw new Error("correlationId must be a non-empty string");
  }
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error("correlationId must be a non-empty string");
  }
  return trimmed;
}

/**
 * Generate a correlation identifier using UUIDv4 semantics.
 *
 * @param {string} [prefix]
 * @returns {string}
 */
export function createCorrelationId(prefix) {
  const uuid = generateUuid();
  if (typeof prefix !== "string" || prefix.trim().length === 0) {
    return uuid;
  }

  const normalizedPrefix = prefix.trim();
  const suffix = normalizedPrefix.endsWith("-") ? "" : "-";
  return `${normalizedPrefix}${suffix}${uuid}`;
}

/**
 * @typedef {Object} NormalizedProducerOptions
 * @property {string[]=} includeHandlers
 * @property {string[]=} excludeHandlers
 * @property {string[]=} excludeSids
 * @property {string=} correlationId
 */

/**
 * Normalise producer options used for emit/request/broadcast helpers.
 *
 * @param {Record<string, any> | undefined} options
 * @returns {NormalizedProducerOptions}
 */
export function normalizeProducerOptions(options) {
  if (options == null) return {};
  const source = assertPlainObject(options, "options");

  const unknownKeys = Object.keys(source).filter((key) => !_OPTION_KEYS.has(key));
  if (unknownKeys.length > 0) {
    throw new Error(`Unsupported producer option(s): ${unknownKeys.join(", ")}`);
  }

  const normalized = {};

  const includeHandlers = normalizeStringList(source.includeHandlers, "includeHandlers");
  if (includeHandlers) {
    normalized.includeHandlers = includeHandlers;
  }

  const excludeHandlers = normalizeStringList(
    source.excludeHandlers,
    "excludeHandlers",
    { allowEmpty: true },
  );
  if (excludeHandlers && excludeHandlers.length > 0) {
    normalized.excludeHandlers = excludeHandlers;
  }

  const excludeSids = normalizeSidList(source.excludeSids);
  if (excludeSids && excludeSids.length > 0) {
    normalized.excludeSids = excludeSids;
  }

  const correlationId = normalizeCorrelationId(source.correlationId);
  if (correlationId) {
    normalized.correlationId = correlationId;
  }

  if (normalized.includeHandlers && normalized.excludeHandlers) {
    throw new Error("includeHandlers and excludeHandlers cannot be used together");
  }

  return normalized;
}

/**
 * @typedef {Object} ServerDeliveryEnvelope
 * @property {string} handlerId
 * @property {string} eventId
 * @property {string} correlationId
 * @property {string} ts
 * @property {Record<string, any>} data
 */

/**
 * Validate a server-sent delivery envelope before invoking subscribers.
 *
 * @param {unknown} envelope
 * @returns {ServerDeliveryEnvelope}
 */
export function validateServerEnvelope(envelope) {
  const value = assertPlainObject(envelope, "envelope");

  const handlerId = normalizeCorrelationId(value.handlerId)?.trim();
  if (!handlerId) {
    throw new Error("Server envelope missing handlerId");
  }

  const eventId = normalizeCorrelationId(value.eventId)?.trim();
  if (!eventId) {
    throw new Error("Server envelope missing eventId");
  }

  const correlationId = normalizeCorrelationId(value.correlationId);
  if (!correlationId) {
    throw new Error("Server envelope missing correlationId");
  }

  if (typeof value.ts !== "string" || value.ts.trim().length === 0) {
    throw new Error("Server envelope missing timestamp");
  }
  const timestamp = value.ts.trim();
  if (Number.isNaN(Date.parse(timestamp))) {
    throw new Error("Server envelope timestamp is invalid");
  }

  let data = value.data;
  if (data == null) {
    data = {};
  } else if (typeof data !== "object" || Array.isArray(data)) {
    throw new Error("Server envelope data must be a plain object");
  }

  const normalized = {
    handlerId,
    eventId,
    correlationId,
    ts: timestamp,
    data: Object.freeze({ ...data }),
  };

  return Object.freeze(normalized);
}

class WebSocketClient {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.connecting = false;
    this.connectPromise = null;
    this.subscriptions = new Map(); // eventType -> { handler, callbacks: Set<Function> }
    this.connectCallbacks = new Set();
    this.disconnectCallbacks = new Set();
    this.errorCallbacks = new Set();
    this.isDevelopment = Boolean(window.runtimeInfo?.isDevelopment);
    this.csrfPreflightPromise = null;
    this.csrfPreflightExpiresAt = null;
    this.csrfPreflightRuntimeId = null;
    this.csrfPreflightTtlSeconds = null;
    this._manualDisconnect = false;
    this._reconnectTimer = null;
    this._csrfRefreshTimer = null;
    this._reconnectAttempts = 0;
    this._hasConnectedOnce = false;
    this._lastRuntimeId = null;
  }

  buildPayload(data) {
    const ts = new Date().toISOString();
    if (data == null) {
      return { ts, data: {} };
    }
    if (typeof data !== "object" || Array.isArray(data)) {
      throw new Error("WebSocket payload must be a plain object");
    }
    return { ts, data: { ...data } };
  }

  applyProducerOptions(payload, normalizedOptions, allowances) {
    const result = payload;

    if (normalizedOptions.includeHandlers) {
      if (!allowances.includeHandlers) {
        throw new Error("This operation does not support includeHandlers");
      }
      result.includeHandlers = [...normalizedOptions.includeHandlers];
    }

    if (normalizedOptions.excludeHandlers) {
      if (!allowances.excludeHandlers) {
        throw new Error("This operation does not support excludeHandlers");
      }
      result.excludeHandlers = [...normalizedOptions.excludeHandlers];
    }

    if (normalizedOptions.excludeSids) {
      if (!allowances.excludeSids) {
        throw new Error("This operation does not support excludeSids");
      }
      result.excludeSids = [...normalizedOptions.excludeSids];
    }

    if (normalizedOptions.correlationId) {
      result.correlationId = normalizedOptions.correlationId;
    }

    return result;
  }

  setDevelopmentFlag(value) {
    const normalized = Boolean(value);
    this.isDevelopment = normalized;
    window.runtimeInfo = { ...(window.runtimeInfo || {}), isDevelopment: normalized };
  }

  debugLog(...args) {
    if (this.isDevelopment) {
      console.debug("[websocket]", ...args);
    }
  }

  invalidatePreflightCache(reason) {
    this.csrfPreflightExpiresAt = null;
    this.csrfPreflightRuntimeId = null;
    this.debugLog("CSRF preflight cache invalidated", { reason });
  }

  _clearReconnectTimer() {
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }
  }

  _clearCsrfRefreshTimer() {
    if (this._csrfRefreshTimer) {
      clearTimeout(this._csrfRefreshTimer);
      this._csrfRefreshTimer = null;
    }
  }

  _scheduleCsrfRefresh(reason) {
    this._clearCsrfRefreshTimer();

    const expiresAt =
      typeof this.csrfPreflightExpiresAt === "number" ? this.csrfPreflightExpiresAt : null;
    if (expiresAt == null) return;

    const ttlSeconds =
      typeof this.csrfPreflightTtlSeconds === "number" && Number.isFinite(this.csrfPreflightTtlSeconds)
        ? this.csrfPreflightTtlSeconds
        : null;

    const nowSeconds = Date.now() / 1000.0;
    const refreshAheadSeconds = ttlSeconds != null ? Math.max(10, Math.floor(ttlSeconds * 0.5)) : 60;
    const delaySeconds = Math.max(1, Math.floor(expiresAt - nowSeconds - refreshAheadSeconds));

    // Desynchronize tabs so a multi-tab setup does not spike /csrf_token.
    const jitterMs = Math.floor(Math.random() * 5000);
    const delayMs = delaySeconds * 1000 + jitterMs;

    this.debugLog("schedule csrf refresh", { reason, delayMs, expiresAt, ttlSeconds });
    this._csrfRefreshTimer = setTimeout(() => {
      this._csrfRefreshTimer = null;
      if (this._manualDisconnect) return;
      this.performPreflight({ force: true, reason: "timer" }).catch((error) => {
        this.invokeErrorCallbacks(error);
      });
    }, delayMs);
  }

  _computeReconnectDelayMs() {
    const baseMs = 1000;
    const capMs = 10000;
    const exponent = Math.min(Number(this._reconnectAttempts) || 0, 6);
    const delayMs = Math.min(capMs, baseMs * (2 ** exponent));
    const jitterMs = Math.floor(Math.random() * 200);
    return delayMs + jitterMs;
  }

  _scheduleReconnect(reason) {
    if (this._manualDisconnect) return;
    if (this.connected) return;
    if (this.connectPromise) return;
    if (!this.socket) return;
    if (this._reconnectTimer) return;

    const delayMs = this._computeReconnectDelayMs();
    this.debugLog("schedule reconnect", {
      reason,
      attempt: this._reconnectAttempts,
      delayMs,
    });

    this._reconnectTimer = setTimeout(() => {
      this._reconnectTimer = null;
      if (this._manualDisconnect || this.connected) return;

      this._reconnectAttempts += 1;
      this.connect().catch((error) => {
        this.invokeErrorCallbacks(error);
        this._scheduleReconnect("connect_failed");
      });
    }, delayMs);
  }

  async connect() {
    if (this.connected) return;
    if (this.connectPromise) return this.connectPromise;

    this._manualDisconnect = false;
    this.connecting = true;
    this.connectPromise = (async () => {
      await this.performPreflight();

      if (!this.socket) {
        this.initializeSocket();
      }

      if (this.socket.connected) return;

      await new Promise((resolve, reject) => {
        const onConnect = () => {
          this.socket.off("connect_error", onError);
          resolve();
        };
        const onError = (error) => {
          this.socket.off("connect", onConnect);
          reject(error instanceof Error ? error : new Error(String(error)));
        };

        this.socket.once("connect", onConnect);
        this.socket.once("connect_error", onError);
        this.socket.connect();
      });
    })()
      .catch((error) => {
        const wrapped = new Error(`WebSocket connection failed: ${error.message || error}`);
        // Ensure we do not get stuck offline after backend restarts rotate session cookies.
        // Auto-reconnect is handled by our own scheduler (socket.io reconnection is disabled).
        this.invalidatePreflightCache("connect_failed");
        invalidateCsrfToken();
        setTimeout(() => this._scheduleReconnect("connect_failed"), 0);
        throw wrapped;
      })
      .finally(() => {
        this.connecting = false;
        this.connectPromise = null;
      });

    return this.connectPromise;
  }

  async disconnect() {
    if (!this.socket) return;
    this._manualDisconnect = true;
    this._clearReconnectTimer();
    this._clearCsrfRefreshTimer();
    this.invalidatePreflightCache("manual_disconnect");
    invalidateCsrfToken();
    this.socket.disconnect();
    this.connected = false;
  }

  isConnected() {
    return this.connected;
  }

  async emit(eventType, data, options = {}) {
    const normalized = normalizeProducerOptions({
      includeHandlers: options.includeHandlers,
      correlationId: options.correlationId,
    });
    const payload = this.applyProducerOptions(
      this.buildPayload(data),
      normalized,
      { includeHandlers: true, excludeHandlers: false, excludeSids: false },
    );
    if (!payload.correlationId) {
      payload.correlationId = createCorrelationId("emit");
    }
    this.debugLog("emit", {
      eventType,
      correlationId: payload.correlationId,
      includeHandlers: payload.includeHandlers,
    });
    this.ensurePayloadSize(payload);
    await this.connect();
    if (!this.isConnected()) {
      throw new Error("Not connected");
    }
    this.socket.emit(eventType, payload);
  }

  async broadcast(eventType, data, options = {}) {
    const normalized = normalizeProducerOptions({
      excludeSids: options.excludeSids,
      correlationId: options.correlationId,
    });
    if (normalized.includeHandlers || normalized.excludeHandlers) {
      throw new Error("broadcast supports excludeSids only");
    }
    const payload = this.applyProducerOptions(
      this.buildPayload(data),
      normalized,
      { includeHandlers: false, excludeHandlers: false, excludeSids: true },
    );
    if (!payload.correlationId) {
      payload.correlationId = createCorrelationId("broadcast");
    }
    this.debugLog("broadcast", {
      eventType,
      correlationId: payload.correlationId,
      excludeSids: payload.excludeSids,
    });
    this.ensurePayloadSize(payload);
    await this.connect();
    if (!this.isConnected()) {
      throw new Error("Not connected");
    }
    this.socket.emit(eventType, payload);
  }

  async request(eventType, data, options = {}) {
    const normalized = normalizeProducerOptions({
      includeHandlers: options.includeHandlers,
      correlationId: options.correlationId,
    });
    const payload = this.applyProducerOptions(
      this.buildPayload(data),
      normalized,
      { includeHandlers: true, excludeHandlers: false, excludeSids: false },
    );
    if (!payload.correlationId) {
      payload.correlationId = createCorrelationId("request");
    }
    const timeoutMs = Number(options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
    this.debugLog("request", { eventType, correlationId: payload.correlationId, includeHandlers: payload.includeHandlers, timeoutMs });
    if (!Number.isFinite(timeoutMs) || timeoutMs < 0) {
      throw new Error("timeoutMs must be a non-negative number");
    }
    this.ensurePayloadSize(payload);
    await this.connect();
    if (!this.isConnected()) {
      throw new Error("Not connected");
    }

    return new Promise((resolve, reject) => {
      if (timeoutMs > 0) {
      this.socket
          .timeout(timeoutMs)
          .emit(eventType, payload, (err, response) => {
          if (err) {
            reject(new Error("Request timeout"));
            return;
          }
            resolve(this.normalizeRequestResponse(response));
          });
        return;
      }

      this.socket.emit(eventType, payload, (response) => {
        resolve(this.normalizeRequestResponse(response));
        });
    });
  }

  async requestAll(eventType, data, options = {}) {
    const normalized = normalizeProducerOptions({
      excludeHandlers: options.excludeHandlers,
      correlationId: options.correlationId,
    });
    if (normalized.includeHandlers) {
      throw new Error("requestAll supports excludeHandlers only");
    }
    const payload = this.applyProducerOptions(
      this.buildPayload(data),
      normalized,
      { includeHandlers: false, excludeHandlers: true, excludeSids: false },
    );
    if (!payload.correlationId) {
      payload.correlationId = createCorrelationId("requestAll");
    }
    const timeoutMs = Number(options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
    this.debugLog("requestAll", { eventType, correlationId: payload.correlationId, excludeHandlers: payload.excludeHandlers, timeoutMs });
    if (!Number.isFinite(timeoutMs) || timeoutMs < 0) {
      throw new Error("timeoutMs must be a non-negative number");
    }
    this.ensurePayloadSize(payload);
    await this.connect();
    if (!this.isConnected()) {
      throw new Error("Not connected");
    }

    return new Promise((resolve, reject) => {
      if (timeoutMs > 0) {
      this.socket
          .timeout(timeoutMs)
          .emit(eventType, payload, (err, response) => {
          if (err) {
            reject(new Error("Request timeout"));
            return;
          }
            resolve(this.normalizeRequestAllResponse(response));
          });
        return;
      }

      this.socket.emit(eventType, payload, (response) => {
          resolve(this.normalizeRequestAllResponse(response));
        });
    });
  }

  normalizeRequestResponse(response) {
    if (!response || typeof response !== "object") {
      return { correlationId: null, results: [] };
    }
    const correlationId =
      typeof response.correlationId === "string" && response.correlationId.trim().length > 0
        ? response.correlationId.trim()
        : null;
    const results = Array.isArray(response.results) ? response.results : [];
    return { correlationId, results };
  }

  normalizeRequestAllResponse(response) {
    const normalizeEntry = (entry, fallbackCorrelationId = null) => {
      const sid = typeof entry?.sid === "string" ? entry.sid.trim() : "";
      const correlationId =
        typeof entry?.correlationId === "string" && entry.correlationId.trim().length > 0
          ? entry.correlationId.trim()
          : fallbackCorrelationId;

      return {
        sid: sid.length > 0 ? sid : null,
        correlationId: correlationId ?? null,
        results: Array.isArray(entry?.results) ? entry.results : [],
      };
    };

    if (Array.isArray(response)) {
      return response.map((entry) => normalizeEntry(entry));
    }

    if (response && typeof response === "object") {
      const fallbackCorrelationId =
        typeof response.correlationId === "string" && response.correlationId.trim().length > 0
          ? response.correlationId.trim()
          : null;
      const results = Array.isArray(response.results) ? response.results : [];
      const aggregated = [];

      for (const item of results) {
        if (!item) continue;

        const itemCorrelationId =
          typeof item.correlationId === "string" && item.correlationId.trim().length > 0
            ? item.correlationId.trim()
            : fallbackCorrelationId;

        if (item.ok === true && item.data) {
          const nestedResults = Array.isArray(item.data.results)
            ? item.data.results
            : Array.isArray(item.data.result)
            ? item.data.result
            : null;

          if (nestedResults) {
            for (const entry of nestedResults) {
              aggregated.push(normalizeEntry(entry, itemCorrelationId));
            }
            continue;
          }
        }

        aggregated.push(
          normalizeEntry(
            {
              sid: item.sid ?? "__manager__",
              correlationId: itemCorrelationId,
              results: [item],
            },
            itemCorrelationId,
          ),
        );
      }

      return aggregated;
    }

    return [];
  }

  async on(eventType, callback) {
    if (typeof callback !== "function") {
      throw new Error("Callback must be a function");
    }

    await this.connect();

    if (!this.subscriptions.has(eventType)) {
      const handler = (payload) => {
        const entry = this.subscriptions.get(eventType);
        if (!entry) return;
        let envelope;
        try {
          envelope = validateServerEnvelope(payload);
        } catch (error) {
          console.error("WebSocket envelope validation failed:", error);
          this.invokeErrorCallbacks(error);
          return;
        }

        entry.callbacks.forEach((cb) => {
          try {
            cb(envelope);
          } catch (error) {
            console.error("WebSocket callback error:", error);
          }
        });
      };

      this.subscriptions.set(eventType, {
        handler,
        callbacks: new Set(),
      });

      this.socket.on(eventType, handler);
    }

    const entry = this.subscriptions.get(eventType);
    entry.callbacks.add(callback);
  }

  off(eventType, callback) {
    const entry = this.subscriptions.get(eventType);
    if (!entry) return;

    if (callback) {
      entry.callbacks.delete(callback);
    } else {
      entry.callbacks.clear();
    }

    if (entry.callbacks.size === 0) {
      if (this.socket) {
        this.socket.off(eventType, entry.handler);
      }
      this.subscriptions.delete(eventType);
    }
  }

  onConnect(callback) {
    if (typeof callback === "function") {
      this.connectCallbacks.add(callback);
    }
  }

  onDisconnect(callback) {
    if (typeof callback === "function") {
      this.disconnectCallbacks.add(callback);
    }
  }

  onError(callback) {
    if (typeof callback === "function") {
      this.errorCallbacks.add(callback);
    }
  }

  async performPreflight(options = {}) {
    const { force = false, reason = "" } = options || {};
    this.setDevelopmentFlag(window.runtimeInfo?.isDevelopment);
    const nowSeconds = Date.now() / 1000.0;
    const runtimeId = window.runtimeInfo?.id || null;
    const expiresAt = typeof this.csrfPreflightExpiresAt === "number" ? this.csrfPreflightExpiresAt : null;

    // If we have a still-valid WS CSRF flag for the current runtime, skip re-preflight.
    if (
      !force &&
      expiresAt != null &&
      expiresAt > nowSeconds + 5 &&
      runtimeId &&
      this.csrfPreflightRuntimeId === runtimeId
    ) {
      return;
    }

    if (this.csrfPreflightPromise) {
      return await this.csrfPreflightPromise;
    }

    this.csrfPreflightPromise = (async () => {
      const attempt = async (allowRetry) => {
        const response = await callJsonApi("/csrf_token", {});
        if (!response?.ok) {
          const message = response?.error || "CSRF preflight rejected";
          if (allowRetry) {
            // Backend restarts rotate runtime id and session cookies; cached CSRF may become invalid
            // without producing a 403. Force-refresh and retry once.
            invalidateCsrfToken();
            return await attempt(false);
          }
          throw new Error(message);
        }

        const runtimeInfo = response.runtime || {};
        if (runtimeInfo.id) {
          window.runtimeInfo = {
            ...(window.runtimeInfo || {}),
            id: runtimeInfo.id,
          };
        }
        if (typeof runtimeInfo.isDevelopment !== "undefined") {
          this.setDevelopmentFlag(runtimeInfo.isDevelopment);
        }

        const effectiveRuntimeId = window.runtimeInfo?.id || null;
        this.csrfPreflightRuntimeId = effectiveRuntimeId;
        this.csrfPreflightExpiresAt =
          typeof response.expires_at === "number" ? response.expires_at : null;
        this.csrfPreflightTtlSeconds =
          typeof response.ttl_seconds === "number" ? response.ttl_seconds : null;

        this._scheduleCsrfRefresh(force ? `forced:${reason}` : `preflight:${reason || "connect"}`);

        this.debugLog("CSRF preflight complete", {
          expiresAt: response.expires_at,
          isDevelopment: this.isDevelopment,
        });
      };

      try {
        await attempt(true);
      } catch (error) {
        throw new Error(`CSRF preflight failed: ${error.message || error}`);
      }
    })().finally(() => {
      this.csrfPreflightPromise = null;
    });

    return await this.csrfPreflightPromise;
  }

  initializeSocket() {
    this.socket = io({
      autoConnect: false,
      reconnection: false,
      transports: ["websocket", "polling"],
      withCredentials: true,
    });

    this.socket.on("connect", () => {
      this.connected = true;
      this._reconnectAttempts = 0;
      this._clearReconnectTimer();
      this._scheduleCsrfRefresh("socket connect");

      const runtimeId = window.runtimeInfo?.id || null;
      const runtimeChanged = Boolean(
        this._lastRuntimeId &&
          runtimeId &&
          this._lastRuntimeId !== runtimeId
      );
      const firstConnect = !this._hasConnectedOnce;
      this._hasConnectedOnce = true;
      this._lastRuntimeId = runtimeId;

      this.debugLog("socket connected", {
        sid: this.socket.id,
        runtimeId,
        runtimeChanged,
        firstConnect,
      });
      this.connectCallbacks.forEach((cb) => {
        try {
          cb({ runtimeId, runtimeChanged, firstConnect });
        } catch (error) {
          console.error("WebSocket onConnect callback error:", error);
        }
      });
    });

    this.socket.on("disconnect", (reason) => {
      this.connected = false;
      this.debugLog("socket disconnected", { reason });
      this._clearCsrfRefreshTimer();
      this.disconnectCallbacks.forEach((cb) => {
        try {
          cb(reason);
        } catch (error) {
          console.error("WebSocket onDisconnect callback error:", error);
        }
      });

      // Any disconnect can be a backend restart (rotated runtime id / session).
      // Force next connect attempt to re-preflight.
      this.invalidatePreflightCache(`disconnect:${reason}`);
      invalidateCsrfToken();
      if (!this._manualDisconnect) {
        this._scheduleReconnect(`disconnect:${reason}`);
      }
    });

    this.socket.on("connect_error", (error) => {
      this.debugLog("socket connect_error", error);
      this.invokeErrorCallbacks(error);

      // If we get rejected during connect (including CSRF-missing), force a new preflight.
      this.invalidatePreflightCache("connect_error");
      invalidateCsrfToken();
      this._scheduleReconnect("connect_error");
    });

    this.socket.on("error", (error) => {
      this.debugLog("socket error", error);
      this.invokeErrorCallbacks(error);
    });

    // Note: socket.io reconnection is disabled. Reconnect attempts are scheduled by WebSocketClient.
  }

  invokeErrorCallbacks(error) {
    this.errorCallbacks.forEach((cb) => {
      try {
        cb(error);
      } catch (err) {
        console.error("WebSocket onError callback error:", err);
      }
    });
  }

  ensurePayloadSize(data) {
    const size = this.calculatePayloadSize(data);
    if (size > MAX_PAYLOAD_BYTES) {
      throw new Error("Payload too large");
    }
  }

  calculatePayloadSize(data) {
    try {
      return new TextEncoder().encode(JSON.stringify(data ?? null)).length;
    } catch (_error) {
      // Fallback: rough estimate if stringify fails
      const stringified = String(data);
      return stringified.length * 2;
    }
  }
}

export const websocket = new WebSocketClient();
