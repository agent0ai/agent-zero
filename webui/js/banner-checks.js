/**
 * Frontend Banner Checks
 * Modular system for generating banners based on frontend context
 */

/** Returns true if hostname is local/private */
function isLocalhost(hostname) {
  const localPatterns = [
    'localhost',
    '127.0.0.1',
    '::1',
    '0.0.0.0',
  ];
  
  if (localPatterns.includes(hostname)) return true;
  
  if (/^192\.168\.\d{1,3}\.\d{1,3}$/.test(hostname)) return true;
  if (/^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(hostname)) return true;
  if (/^172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}$/.test(hostname)) return true;
  
  if (hostname.endsWith('.local')) return true;
  
  return false;
}

/** Frontend check: unsecured / unsafe connections */
export function checkUnsecuredConnection(context) {
  const { hostname, protocol, hasCredentials } = context;
  const isLocal = isLocalhost(hostname);
  const isHttps = protocol === 'https:';
  
  // Unsecured access scenarios
  if (!isLocal && !hasCredentials) {
    return {
      id: 'unsecured-connection',
      type: 'warning',
      priority: 80,
      title: 'Unsecured Connection',
      html: `You are accessing Agent Zero from a non-local address without authentication. 
             <a href="#" onclick="document.getElementById('settings').click(); return false;">
             Configure credentials</a> in Settings → External Services → Authentication.`,
      dismissible: true,
      source: 'frontend'
    };
  }
  
  if (hasCredentials && !isLocal && !isHttps) {
    return {
      id: 'credentials-unencrypted',
      type: 'warning',
      priority: 90,
      title: 'Credentials May Be Sent Unencrypted',
      html: `Your connection is not using HTTPS. Login credentials may be transmitted in plain text. 
             Consider using HTTPS or a secure tunnel.`,
      dismissible: true,
      source: 'frontend'
    };
  }
  
  return null;
}

/** Frontend check: missing API keys */
export function checkMissingApiKey(context) {
  const { selectedProvider, apiKeys } = context;
  
  if (!selectedProvider) return null;
  
  const localProviders = ['ollama', 'lm_studio'];
  
  if (localProviders.includes(selectedProvider.toLowerCase())) {
    return null;
  }
  
  // Note: Backend returns '************' placeholder for existing keys
  const providerKey = selectedProvider.toLowerCase();
  const apiKeyValue = apiKeys && apiKeys[providerKey];
  const hasApiKey = apiKeyValue && 
                    apiKeyValue.trim() !== '' && 
                    apiKeyValue !== '************';  // Placeholder means key exists
  
  const hasPlaceholder = apiKeyValue === '************';
  
  if (!hasApiKey && !hasPlaceholder) {
    return {
      id: 'missing-api-key',
      type: 'error',
      priority: 100,
      title: 'Missing API Key',
      html: `No API key configured for <strong>${selectedProvider}</strong>. 
             Agent Zero will not be able to function properly. 
             <a href="#" onclick="document.getElementById('settings').click(); return false;">
             Add your API key</a> in Settings → External Services → API Keys.`,
      dismissible: false,
      source: 'frontend'
    };
  }
  
  return null;
}

/**
 * Registry of all frontend banner checks
 * Add new check functions here to extend the system
 */
const bannerChecks = [
  checkUnsecuredConnection,
  checkMissingApiKey,
];

/** Run all registered banner checks */
export function runAllChecks(context) {
  const banners = [];
  
  for (const check of bannerChecks) {
    try {
      const result = check(context);
      if (result) {
        banners.push(result);
      }
    } catch (error) {
      console.error(`Banner check failed:`, error);
    }
  }
  
  return banners;
}

/** Build frontend banner-check context */
export function buildFrontendContext(settings = {}) {
  const hasCredentials = Boolean(
    settings?.auth_login && 
    settings?.auth_password && 
    settings.auth_password !== '' &&
    settings.auth_password !== '****PSWD****'
  );
  
  return {
    url: window.location.href,
    protocol: window.location.protocol,
    hostname: window.location.hostname,
    port: window.location.port,
    browser: navigator.userAgent,
    timestamp: new Date().toISOString(),
    selectedProvider: settings?.chat_model_provider || '',
    apiKeys: settings?.api_keys || {},
    hasCredentials: hasCredentials,
  };
}
