/**
 * Call a JSON-in JSON-out API endpoint
 * Data is automatically serialized
 * @param {string} endpoint - The API endpoint to call
 * @param {any} data - The data to send to the API
 * @returns {Promise<any>} The JSON response from the API
 */
export async function callJsonApi(endpoint, data) {
  const response = await fetchApi(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "same-origin",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }
  const jsonResponse = await response.json();
  return jsonResponse;
}

/**
 * Load settings and flatten them to a simple key/value map.
 * @returns {Promise<Object>} Flattened settings map.
 */
export async function loadSettings() {
  const response = await callJsonApi("/settings_get", {});
  const flat = {};
  const sections = response?.settings?.sections || [];
  for (const section of sections) {
    const fields = section?.fields || [];
    for (const field of fields) {
      if (field?.id !== undefined) {
        flat[field.id] = field.value;
      }
    }
  }
  return flat;
}

/**
 * Save a partial settings delta using the settings_set API.
 * @param {Object} delta - Partial settings fields to update.
 * @returns {Promise<Object>} API response.
 */
export async function saveSettings(delta) {
  const fields = Object.entries(delta || {}).map(([id, value]) => ({ id, value }));
  return await callJsonApi("/settings_set", { sections: [{ fields }] });
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
    let token = null;
    try {
      token = await getCsrfToken();
    } catch (err) {
      console.warn("CSRF token unavailable, continuing without token:", err);
    }

    // create a new request object if none was provided
    const finalRequest = request || {};

    // ensure headers object exists
    finalRequest.headers = finalRequest.headers || {};

    // add the CSRF token to the headers
    if (token) {
      finalRequest.headers["X-CSRF-Token"] = token;
    }

    // perform the fetch with the updated request
    const response = await fetch(url, finalRequest);

    // check if there was an CSRF error
    if (response.status === 403 && retry) {
      // retry the request with new token
      csrfToken = null;
      return await _wrap(false);
    } else if (response.redirected && response.url.endsWith("/login")) {
      // redirect to login
      window.location.href = response.url;
      return;
    }

    // return the response
    return response;
  }

  // perform the request
  const response = await _wrap(true);

  // return the response
  return response;
}

/**
 * Probe backend reachability and warm-up status without requiring auth/csrf.
 * @returns {Promise<{state: "ready"|"warming"|"offline", message: string}>}
 */
export async function probeBackendStatus() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 2000);

  try {
    const response = await fetch("/health", {
      method: "GET",
      credentials: "same-origin",
      signal: controller.signal,
    });

    if (!response.ok) {
      return { state: "warming", message: "Backend is starting up..." };
    }

    return { state: "ready", message: "Backend connected" };
  } catch (_error) {
    return { state: "offline", message: "Backend is unreachable" };
  } finally {
    clearTimeout(timeout);
  }
}

let chatReadinessCache = { ts: 0, value: null };

/**
 * Validate chat runtime readiness (provider/model/backend) before sending messages.
 * Cached briefly to keep typing/send latency low.
 * @returns {Promise<{ready: boolean, message: string, checks?: any[]}>}
 */
export async function getChatReadiness() {
  const now = Date.now();
  if (chatReadinessCache.value && now - chatReadinessCache.ts < 10000) {
    return chatReadinessCache.value;
  }

  try {
    const response = await fetchApi("/chat_readiness", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
      credentials: "same-origin",
    });
    const json = await response.json();
    chatReadinessCache = { ts: now, value: json };
    return json;
  } catch (error) {
    return {
      ready: false,
      message: `Readiness check failed: ${error?.message || error}`,
      checks: [],
    };
  }
}

// csrf token stored locally
let csrfToken = null;

/**
 * Get the CSRF token for API requests
 * Caches the token after first request
 * @returns {Promise<string>} The CSRF token
 */
async function getCsrfToken() {
  if (csrfToken) return csrfToken;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 2000);
  let response;
  try {
    response = await fetch("/csrf_token", {
      credentials: "same-origin",
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
  if (response.redirected && response.url.endsWith("/login")) {
    // redirect to login
    window.location.href = response.url;
    return;
  }
  const json = await response.json();
  if (json.ok) {
    csrfToken = json.token;
    document.cookie = `csrf_token_${json.runtime_id}=${csrfToken}; SameSite=Strict; Path=/`;
    return csrfToken;
  } else {
    if (json.error) alert(json.error);
    throw new Error(json.error || "Failed to get CSRF token");
  }
}
