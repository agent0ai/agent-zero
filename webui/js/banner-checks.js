function isLocalhost(hostname) {
  const localPatterns = ['localhost', '127.0.0.1', '::1', '0.0.0.0'];
  
  if (localPatterns.includes(hostname)) return true;
  
  // RFC1918 private ranges
  if (/^192\.168\.\d{1,3}\.\d{1,3}$/.test(hostname)) return true;
  if (/^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(hostname)) return true;
  if (/^172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}$/.test(hostname)) return true;
  
  if (hostname.endsWith('.local')) return true;
  
  return false;
}

export function checkUnsecuredConnection(context) {
  const { hostname, protocol, hasCredentials } = context;
  const isLocal = isLocalhost(hostname);
  const isHttps = protocol === 'https:';
  
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

export function checkMissingApiKey(context) {
  const { modelProviders, apiKeys } = context;
  
  if (!modelProviders) return null;
  
  // These providers run locally, no API key needed
  const localProviders = ['ollama', 'lm_studio', 'huggingface'];
  
  const modelTypeNames = {
    chat: 'Chat Model',
    utility: 'Utility Model',
    browser: 'Web Browser Model',
    embedding: 'Embedding Model',
  };
  
  const missingProviders = [];
  
  for (const [modelType, provider] of Object.entries(modelProviders)) {
    if (!provider) continue;
    
    const providerLower = provider.toLowerCase();
    if (localProviders.includes(providerLower)) continue;
    
    // Backend returns '************' placeholder for existing keys
    const apiKeyValue = apiKeys && apiKeys[providerLower];
    const hasApiKey = apiKeyValue && apiKeyValue.trim() !== '';
    
    if (!hasApiKey) {
      missingProviders.push({
        modelType: modelTypeNames[modelType] || modelType,
        provider: provider,
      });
    }
  }
  
  if (missingProviders.length === 0) return null;
  
  const modelList = missingProviders.map(p => `${p.modelType} (${p.provider})`).join(', ');
  
  return {
    id: 'missing-api-key',
    type: 'error',
    priority: 100,
    title: 'Missing API Key',
    html: `No API key configured for: ${modelList}. 
           Agent Zero will not be able to function properly. 
           <a href="#" onclick="document.getElementById('settings').click(); return false;">
           Add your API key</a> in Settings → External Services → API Keys.`,
    dismissible: false,
    source: 'frontend'
  };
}

// Add new check functions here to extend
const bannerChecks = [
  checkUnsecuredConnection,
  checkMissingApiKey,
];

export function runAllChecks(context) {
  const banners = [];
  
  for (const check of bannerChecks) {
    try {
      const result = check(context);
      if (result) {
        banners.push(result);
      }
    } catch (error) {
      console.error('Banner check failed:', error);
    }
  }
  
  return banners;
}

export function buildFrontendContext(settings = {}) {
  // '****PSWD****' placeholder means password IS configured
  const hasCredentials = Boolean(
    settings?.auth_login && 
    settings?.auth_login.trim() !== '' &&
    settings?.auth_password && 
    settings.auth_password !== ''
  );
  
  const modelProviders = {
    chat: settings?.chat_model_provider || '',
    utility: settings?.util_model_provider || '',
    browser: settings?.browser_model_provider || '',
    embedding: settings?.embed_model_provider || '',
  };
  
  return {
    url: window.location.href,
    protocol: window.location.protocol,
    hostname: window.location.hostname,
    port: window.location.port,
    browser: navigator.userAgent,
    timestamp: new Date().toISOString(),
    selectedProvider: settings?.chat_model_provider || '',
    modelProviders: modelProviders,
    apiKeys: settings?.api_keys || {},
    hasCredentials: hasCredentials,
  };
}
