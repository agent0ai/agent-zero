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

// csrf token stored locally
let csrfToken = null;
let csrfTokenPromise = null;
let runtimeIdCache = null;
const CSRF_TIMEOUT_MS = 5000;
const CSRF_SLOW_WARN_MS = 1500;

export function getRuntimeId() {
  if (runtimeIdCache) return runtimeIdCache;
  const injected =
    window.runtimeInfo &&
    typeof window.runtimeInfo.id === "string" &&
    window.runtimeInfo.id.length > 0
      ? window.runtimeInfo.id
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

      const fetchOptions = { credentials: "same-origin" };
      if (controller) {
        fetchOptions.signal = controller.signal;
      }

      const fetchPromise = fetch("/csrf_token", fetchOptions);
      response = timeoutPromise
        ? await Promise.race([fetchPromise, timeoutPromise])
        : await fetchPromise;
    } catch (error) {
      if (error && error.name === "AbortError") {
        throw new Error("CSRF token request timed out");
      }
      throw error;
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }

    if (response.redirected && response.url.endsWith("/login")) {
      // redirect to login
      window.location.href = response.url;
      return;
    }
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
        window.runtimeInfo &&
        typeof window.runtimeInfo.id === "string" &&
        window.runtimeInfo.id.length > 0
          ? window.runtimeInfo.id
          : null;
      const cookieRuntimeId = runtimeId || injectedRuntimeId;
      if (cookieRuntimeId) {
        document.cookie = `csrf_token_${cookieRuntimeId}=${csrfToken}; SameSite=Strict; Path=/`;
      } else {
        console.warn("CSRF runtime id missing; skipping cookie name binding.");
      }
      const elapsedMs = Date.now() - startedAt;
      if (elapsedMs > CSRF_SLOW_WARN_MS && window.runtimeInfo?.isDevelopment) {
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
