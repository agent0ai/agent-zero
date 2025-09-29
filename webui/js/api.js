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

    // clone and prepare request to avoid mutating caller's object
    const finalRequest = Object.assign({}, request || {});
    finalRequest.headers = Object.assign({}, finalRequest.headers || {}, { "X-CSRF-Token": token });

    // perform the fetch with the prepared request
    const response = await fetch(url, finalRequest);

    // check if there was an CSRF error
    if (response.status === 403 && retry) {
      // token may be stale: clear cached token and retry once
      csrfToken = null;
      return await _wrap(false);
    }else if(response.redirected && response.url.endsWith("/login")){
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

/**
 * Get the CSRF token for API requests
 * Caches the token after first request
 * @returns {Promise<string>} The CSRF token
 */
async function getCsrfToken() {
  if (csrfToken) return csrfToken;
  try {
  const response = await fetch("/csrf_token", {
    credentials: "same-origin",
  });
  if (response.redirected && response.url.endsWith("/login")) {
    // redirect to login
    window.location.href = response.url;
    return;
  }
  const json = await response.json();
  csrfToken = json.token;
  document.cookie = `csrf_token_${json.runtime_id}=${csrfToken}; SameSite=Strict; Path=/`;
  return csrfToken;
  } catch (err) {
    throw new Error('Failed to obtain CSRF token: ' + (err && err.message));
  }
}

/**
 * Fetch the list of model groups from the server
 * @returns {Promise<Object>} The model groups object
 */
export async function listModelGroups() {
  const resp = await fetchApi(`/model_groups_list`, { method: "GET", credentials: "same-origin" });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error(txt);
  }
  return await resp.json();
}

/**
 * Select a model group on the server. This will apply the group's settings.
 * @param {string} groupName - The name of the model group to select
 * @returns {Promise<Object>} The API response JSON
 */
export async function selectModelGroup(groupName) {
  if (!groupName) throw new Error("groupName required");
  return await callJsonApi(`/model_group_select`, { group: groupName });
}

