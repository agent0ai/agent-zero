/**
 * Call a JSON-in JSON-out API endpoint
 * Data is automatically serialized
 * @param {string} endpoint - The API endpoint to call
 * @param {any} data - The data to send to the API
 * @returns {Promise<any>} The JSON response from the API
 */
export async function callJsonApi(endpoint, data) {
  const apiUrl = _normalizeApiUrl(endpoint);

  /** @type {{ endpoint: string, data: any, response: Response | null, result: any, error: Error | null }} */
  const ctx = {
    endpoint,
    data,
    response: null,
    result: null,
    error: null,
  };

  if (await _shouldCallApiExtensions(apiUrl)) {
    const extensions = await _getExtensions();
    await extensions.callJsExtensions("json_api_call_before", ctx);
  }

  const response = await fetchApi(ctx.endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "same-origin",
    body: JSON.stringify(ctx.data),
  });
  ctx.response = response;

  if (!response.ok) {
    const error = await response.text();
    ctx.error = new Error(error);

    if (await _shouldCallApiExtensions(apiUrl)) {
      const extensions = await _getExtensions();
      await extensions.callJsExtensions("json_api_call_error", ctx);
    }

    if (ctx.error) throw ctx.error;

    return ctx.result;
  }

  ctx.result = await response.json();

  if (await _shouldCallApiExtensions(apiUrl)) {
    const extensions = await _getExtensions();
    await extensions.callJsExtensions("json_api_call_after", ctx);
  }

  return ctx.result;
}

/**
 * Fetch wrapper for A0 APIs that ensures token exchange
 * Automatically adds CSRF token to request headers
 * @param {string} url - The URL to fetch
 * @param {Object} [request] - The fetch request options
 * @returns {Promise<Response>} The fetch response
 */
export async function fetchApi(url, request) {
  async function _wrap(retry) {
    // get the CSRF token
    const token = await getCsrfToken();

    // create a new request object if none was provided
    const finalRequest = request || {};

    // ensure headers object exists
    finalRequest.headers = finalRequest.headers || {};

    // add the CSRF token to the headers
    finalRequest.headers["X-CSRF-Token"] = token;

    // perform the fetch with the updated request
    const apiUrl = _normalizeApiUrl(url);

    /** @type {{ url: string, apiUrl: string, request: any, response: Response | null, retry: boolean }} */
    const ctx = {
      url,
      apiUrl,
      request: finalRequest,
      response: null,
      retry,
    };

    if (await _shouldCallApiExtensions(apiUrl)) {
      const extensions = await _getExtensions();
      await extensions.callJsExtensions("fetch_api_call_before", ctx);
    }

    const response = ctx.response || (await fetch(ctx.apiUrl, ctx.request));
    ctx.response = response;

    if (await _shouldCallApiExtensions(apiUrl)) {
      const extensions = await _getExtensions();
      await extensions.callJsExtensions("fetch_api_call_after", ctx);
    }

    const finalResponse = ctx.response;

    // check if there was an CSRF error
    if (finalResponse.status === 403 && retry) {
      // retry the request with new token
      csrfToken = null;
      return await _wrap(false);
    }

    if (redirect(finalResponse)) return;

    // return the response
    return finalResponse;
  }

  // perform the request
  const response = await _wrap(true);

  // return the response
  return response;
}

// csrf token stored locally
let csrfToken = null;
let csrfTokenPromise = null;
let runtimeIdCache = null;
const CSRF_TIMEOUT_MS = 5000;
const CSRF_SLOW_WARN_MS = 1500;

export function getRuntimeId() {
  if (runtimeIdCache) return runtimeIdCache;
  const injected =
    globalThis.runtimeInfo &&
    typeof globalThis.runtimeInfo.id === "string" &&
    globalThis.runtimeInfo.id.length > 0
      ? globalThis.runtimeInfo.id
      : null;
  return injected;
}

export function invalidateCsrfToken() {
  csrfToken = null;
  csrfTokenPromise = null;
}

/**
 * Get the CSRF token for API requests
 * Caches the token after first request
 * @returns {Promise<string>} The CSRF token
 */
export async function getCsrfToken() {
  if (csrfToken) return csrfToken;
  if (csrfTokenPromise) return await csrfTokenPromise;

  csrfTokenPromise = (async () => {
    const startedAt = Date.now();
    const controller =
      typeof AbortController !== "undefined" ? new AbortController() : null;
    let timeoutId = null;
    let timeoutPromise = null;
    let response;

    try {
      if (controller) {
        timeoutId = setTimeout(() => controller.abort(), CSRF_TIMEOUT_MS);
      } else {
        timeoutPromise = new Promise((_, reject) => {
          timeoutId = setTimeout(() => {
            reject(new Error("CSRF token request timed out"));
          }, CSRF_TIMEOUT_MS);
        });
      }

      /** @type {RequestInit} */
      const fetchOptions = { credentials: "same-origin" };
      if (controller) {
        fetchOptions.signal = controller.signal;
      }

      const fetchPromise = fetch("/api/csrf_token", fetchOptions);
      response = timeoutPromise
        ? await Promise.race([fetchPromise, timeoutPromise])
        : await fetchPromise;
    } catch (error) {
      if (error && error["name"] === "AbortError") {
        throw new Error("CSRF token request timed out");
      }
      throw error;
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }

    if (redirect(response)) return;

    const json = await response.json();
    if (json.ok) {
      const runtimeId =
        typeof json.runtime_id === "string" && json.runtime_id.length > 0
          ? json.runtime_id
          : null;

      csrfToken = json.token;
      if (runtimeId) {
        runtimeIdCache = runtimeId;
      }
      const injectedRuntimeId =
        globalThis.runtimeInfo &&
        typeof globalThis.runtimeInfo.id === "string" &&
        globalThis.runtimeInfo.id.length > 0
          ? globalThis.runtimeInfo.id
          : null;
      const cookieRuntimeId = runtimeId || injectedRuntimeId;
      if (cookieRuntimeId) {
        const _secureFlag =
          window.location.protocol === "https:" ? "; Secure" : "";
        document.cookie = `csrf_token_${cookieRuntimeId}=${csrfToken}; SameSite=Lax; Path=/${_secureFlag}`;
      } else {
        console.warn("CSRF runtime id missing; skipping cookie name binding.");
      }
      const elapsedMs = Date.now() - startedAt;
      if (
        elapsedMs > CSRF_SLOW_WARN_MS &&
        globalThis.runtimeInfo?.isDevelopment
      ) {
        console.warn(`CSRF token request took ${elapsedMs}ms`);
      }
      return csrfToken;
    } else {
      if (json.error) alert(json.error);
      throw new Error(json.error || "Failed to get CSRF token");
    }
  })();

  try {
    return await csrfTokenPromise;
  } finally {
    csrfTokenPromise = null;
  }
}



let _extensionsModule = null;

async function _getExtensions() {
  if (!_extensionsModule) _extensionsModule = await import("./extensions.js");
  return _extensionsModule;
}

async function _shouldCallApiExtensions(apiUrl) {
  const extensions = await _getExtensions();
  const excluded = extensions.API_EXTENSION_EXCLUDED_ENDPOINTS;
  return !(excluded instanceof Set && excluded.has(apiUrl));
}

function _normalizeApiUrl(url) {
  return url.startsWith("/api/") || url.startsWith("api/")
    ? `/${url.replace(/^\/+/, "")}`
    : `/api/${url.replace(/^\/+/, "")}`;
}

function redirect(response) {
  if (!(response.redirected && response.url.endsWith("/login"))) return false;
  const _redirectUrl = new URL(response.url);
  if (_redirectUrl.origin === window.location.origin) {
    window.location.href = response.url;
  }
  return true;
}