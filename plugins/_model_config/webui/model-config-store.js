import { createStore } from "/js/AlpineStore.js";


export const MODEL_SECTIONS = [
  { key: 'chat_model', title: 'Main Model', desc: 'Primary model for chat, reasoning, and browser tasks.' },
  { key: 'utility_model', title: 'Utility Model', desc: 'Lightweight model for background tasks: memory management, prompt preparation, summarization.' },
  { key: 'embedding_model', title: 'Embedding Model', desc: 'Model for generating vector embeddings used in knowledge retrieval.' }
];

export function kwargsToText(obj) {
  if (!obj || typeof obj !== 'object') return '';
  return Object.entries(obj).map(([k, v]) => {
    if (typeof v === 'string') return k + '=' + JSON.stringify(v);
    return k + '=' + (typeof v === 'object' ? JSON.stringify(v) : String(v));
  }).join('\n');
}

export function textToKwargs(text) {
  const d = {};
  (text || '').split('\n').forEach(l => {
    l = l.trim();
    if (!l || l.startsWith('#')) return;
    const i = l.indexOf('=');
    if (i > 0) {
      const key = l.substring(0, i).trim();
      let val = l.substring(i + 1).trim();
      try { val = JSON.parse(val); } catch {}
      d[key] = val;
    }
  });
  return d;
}

export function textToHeaders(text) {
  const d = {};
  (text || '').split('\n').forEach(l => {
    l = l.trim();
    if (!l || l.startsWith('#')) return;
    const i = l.indexOf('=');
    if (i > 0) d[l.substring(0, i).trim()] = l.substring(i + 1).trim();
  });
  return d;
}

// ── Alpine Store ──

const API_BASE = "/plugins/_model_config";

export const store = createStore("modelConfig", {
  // Shared state
  chatProviders: [],
  embeddingProviders: [],
  apiKeyStatus: {},
  apiKeyValues: {},
  apiKeyDirty: {},
  allProviders: [],
  _loaded: false,

  // Global presets state
  globalPresets: [],
  _presetsLoaded: false,

  // Switcher state
  switcherAllowed: false,
  switcherOverride: null,
  switcherPresets: [],
  switcherLoading: true,

  init() {},

  _setProviderHasKey(provider, hasKey) {
    if (!provider) return;
    this.apiKeyStatus = { ...this.apiKeyStatus, [provider]: !!hasKey };
    const normalized = provider.toLowerCase();
    this.allProviders = (this.allProviders || []).map((item) =>
      item.value?.toLowerCase() === normalized ? { ...item, has_key: !!hasKey } : item
    );
  },

  _ensureApiKeySlot(provider) {
    if (!provider) return;
    if (!(provider in this.apiKeyValues)) {
      this.apiKeyValues = { ...this.apiKeyValues, [provider]: '' };
    }
    if (!(provider in this.apiKeyDirty)) {
      this.apiKeyDirty = { ...this.apiKeyDirty, [provider]: false };
    }
  },

  _setApiKeyDirty(provider, isDirty) {
    if (!provider) return;
    this._ensureApiKeySlot(provider);
    this.apiKeyDirty = { ...this.apiKeyDirty, [provider]: !!isDirty };
  },

  touchApiKey(provider) {
    this._setApiKeyDirty(provider, true);
  },

  _normalizePresets(rawPresets) {
    return (rawPresets || []).map(p => ({
      name: p.name || '',
      chat: { provider: '', name: '', api_key: '', api_base: '', ctx_length: 128000, ctx_history: 0.7, vision: true, rl_requests: 0, rl_input: 0, rl_output: 0, kwargs: {}, _kwargs_text: kwargsToText(p.chat?.kwargs), ...(p.chat || {}) },
      utility: { provider: '', name: '', api_key: '', api_base: '', ctx_length: 128000, ctx_input: 0.7, rl_requests: 0, rl_input: 0, rl_output: 0, kwargs: {}, _kwargs_text: kwargsToText(p.utility?.kwargs), ...(p.utility || {}) },
    }));
  },

  async ensureLoaded() {
    if (this._loaded) return;
    const data = await this._fetchConfigData();
    this.chatProviders = data.chat_providers || [];
    this.embeddingProviders = data.embedding_providers || [];
    this.apiKeyStatus = data.api_key_status || {};
    const keys = {};
    const dirty = {};
    const seen = new Set();
    for (const p of [...this.chatProviders, ...this.embeddingProviders]) {
      if (!p.value || seen.has(p.value)) continue;
      seen.add(p.value);
      if (!(p.value in keys)) keys[p.value] = '';
      if (!(p.value in dirty)) dirty[p.value] = false;
    }
    this.apiKeyValues = keys;
    this.apiKeyDirty = dirty;

    const allProviders = [];
    const provSeen = new Set();
    for (const p of [...this.chatProviders, ...this.embeddingProviders]) {
      if (!p.value || provSeen.has(p.value.toLowerCase())) continue;
      provSeen.add(p.value.toLowerCase());
      allProviders.push({ value: p.value, label: p.label || p.value, has_key: !!this.apiKeyStatus[p.value] });
    }
    allProviders.sort((a, b) => a.label.localeCompare(b.label));
    this.allProviders = allProviders;

    this._loaded = true;
  },

  async refreshApiKeyStatus() {
    await this.ensureLoaded();
    const res = await fetchApi(`${API_BASE}/api_keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'get' })
    });
    const data = await res.json();
    const keys = data.keys || {};

    const nextStatus = { ...this.apiKeyStatus };
    const nextValues = { ...this.apiKeyValues };
    const nextDirty = { ...this.apiKeyDirty };

    for (const provider of this.allProviders) {
      const entry = keys[provider.value] || {};
      const hasKey = !!entry.has_key;
      nextStatus[provider.value] = hasKey;
      provider.has_key = hasKey;
      if (!(provider.value in nextDirty)) {
        nextDirty[provider.value] = false;
      }
      if (!hasKey && !nextDirty[provider.value]) {
        nextValues[provider.value] = '';
      }
    }

    this.apiKeyStatus = nextStatus;
    this.apiKeyValues = nextValues;
    this.apiKeyDirty = nextDirty;
    this.allProviders = [...this.allProviders];
    return keys;
  },

  resetApiKeyDrafts() {
    const nextValues = {};
    const nextDirty = {};
    for (const provider of this.allProviders || []) {
      if (!provider?.value) continue;
      nextValues[provider.value] = '';
      nextDirty[provider.value] = false;
    }
    this.apiKeyValues = nextValues;
    this.apiKeyDirty = nextDirty;
  },

  async _fetchConfigData() {
    const res = await fetchApi(`${API_BASE}/model_config_get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    return await res.json();
  },

  // Config field initialization (converts kwargs dicts to editable text)
  initConfigFields(config) {
    if (config?.chat_model) config.chat_model._kwargs_text = kwargsToText(config.chat_model.kwargs);
    if (config?.utility_model) config.utility_model._kwargs_text = kwargsToText(config.utility_model.kwargs);
    if (config?.embedding_model) config.embedding_model._kwargs_text = kwargsToText(config.embedding_model.kwargs);
  },

  // Global presets
  async loadGlobalPresets() {
    try {
      const res = await fetchApi(`${API_BASE}/model_presets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get' })
      });
      const data = await res.json();
      this.globalPresets = this._normalizePresets(data.presets);
    } catch (e) {
      console.error('Failed to load global presets:', e);
      this.globalPresets = [];
    }
    this._presetsLoaded = true;
  },

  async saveGlobalPresets(presets) {
    // Strip UI-only fields before saving
    const clean = presets.map(p => {
      const c = { name: p.name };
      for (const slot of ['chat', 'utility']) {
        if (p[slot]) {
          const { _kwargs_text, ...rest } = p[slot];
          c[slot] = rest;
        }
      }
      return c;
    });
    try {
      await fetchApi(`${API_BASE}/model_presets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'save', presets: clean })
      });
      this.globalPresets = presets;
      this.switcherPresets = presets.filter(p => p.name);
      justToast('Presets saved');
    } catch (e) {
      console.error('Failed to save global presets:', e);
      justToast('Failed to save presets');
    }
  },

  async resetGlobalPresets() {
    try {
      const res = await fetchApi(`${API_BASE}/model_presets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reset' })
      });
      const data = await res.json();
      this.globalPresets = this._normalizePresets(data.presets);
      this.switcherPresets = this.globalPresets.filter(p => p.name);
      this._presetsLoaded = true;
    } catch (e) {
      console.error('Failed to reset presets:', e);
    }
  },

  // API Key operations
  async saveApiKeys(updates) {
    const normalized = {};
    for (const [provider, value] of Object.entries(updates || {})) {
      if (!provider || typeof value !== 'string') continue;
      normalized[provider] = value.trim() ? value : '';
    }

    if (Object.keys(normalized).length === 0) {
      return { ok: true };
    }

    const res = await fetchApi(`${API_BASE}/api_keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'set', keys: normalized })
    });
    const data = await res.json();
    if (!data?.ok) {
      throw new Error(data?.error || 'Failed to save API keys.');
    }

    const nextValues = { ...this.apiKeyValues };
    const nextDirty = { ...this.apiKeyDirty };
    for (const [provider, value] of Object.entries(normalized)) {
      nextValues[provider] = value;
      nextDirty[provider] = false;
      this._setProviderHasKey(provider, !!value.trim());
    }
    this.apiKeyValues = nextValues;
    this.apiKeyDirty = nextDirty;
    return data;
  },

  async saveApiKey(provider, value) {
    return this.saveApiKeys({ [provider]: value });
  },

  saveApiKeyIfSet(provider) {
    if (provider in this.apiKeyValues) {
      return this.saveApiKey(provider, this.apiKeyValues[provider] || '');
    }
  },

  async revealApiKey(provider) {
    const res = await fetchApi(`${API_BASE}/api_keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'reveal', provider })
    });
    const data = await res.json();
    if (!data?.ok) {
      throw new Error(data?.error || 'Failed to load API key.');
    }
    const value = data.value || '';
    if (provider) {
      this._ensureApiKeySlot(provider);
      this.apiKeyValues = { ...this.apiKeyValues, [provider]: value };
      this._setApiKeyDirty(provider, false);
      this._setProviderHasKey(provider, !!value.trim());
    }
    return value;
  },

  async persistApiKeysForConfig(config) {
    const updates = {};
    const seen = new Set();
    for (const section of this.MODEL_SECTIONS) {
      const provider = config?.[section.key]?.provider;
      if (!provider || seen.has(provider) || !this.apiKeyDirty[provider]) continue;
      seen.add(provider);
      const value = this.apiKeyValues[provider];
      updates[provider] = typeof value === 'string' ? value : '';
    }
    return this.saveApiKeys(updates);
  },

  installPluginSettingsSaveHook(context, config) {
    if (!context || context.__modelConfigSaveHookInstalled) return;
    const originalSave = context.save.bind(context);
    context.save = async () => {
      context.error = null;
      try {
        await this.persistApiKeysForConfig(config);
      } catch (e) {
        context.error = e?.message || 'Failed to save API keys.';
        return;
      }
      await originalSave();
    };
    context.__modelConfigSaveHookInstalled = true;
  },

  // Model search
  getProviders(key) {
    return key === 'embedding_model' ? this.embeddingProviders : this.chatProviders;
  },

  getSearchType(key) {
    return key === 'embedding_model' ? 'embedding' : 'chat';
  },

  async searchModels(provider, query, modelType, apiBase) {
    if (!provider) return [];
    try {
      const res = await fetchApi(`${API_BASE}/model_search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, query: query || '', model_type: modelType || 'chat', api_base: apiBase || '' })
      });
      const data = await res.json();
      return data.models || [];
    } catch (e) {
      console.error('Model search failed:', e);
      return [];
    }
  },

  groupResults(models, query) {
    const q = (query || '').trim().toLowerCase();
    if (!q) return { matched: [], rest: models };
    const matched = [];
    const rest = [];
    for (const m of models) {
      if (m.toLowerCase().includes(q)) matched.push(m);
      else rest.push(m);
    }
    return { matched, rest };
  },

  // Model Switcher
  async loadSwitcherState(contextId) {
    const result = { allowed: false, presets: [], override: null };
    try {
      await this.loadGlobalPresets();
      result.presets = this.globalPresets.filter(p => p.name);
      if (contextId) {
        const overRes = await fetchApi(`${API_BASE}/model_override`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "get", context_id: contextId }),
        });
        const overData = await overRes.json();
        result.allowed = !!overData.allowed;
        result.override = overData.override || null;
      }
    } catch (e) {
      console.error("Model switcher load failed:", e);
    }
    return result;
  },

  async setPresetOverride(contextId, presetName) {
    try {
      const res = await fetchApi(`${API_BASE}/model_override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "set_preset", context_id: contextId, preset_name: presetName }),
      });
      return !!(await res.json()).ok;
    } catch (e) {
      console.error("Failed to set preset override:", e);
      return false;
    }
  },

  async clearOverride(contextId) {
    try {
      const res = await fetchApi(`${API_BASE}/model_override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "clear", context_id: contextId }),
      });
      return !!(await res.json()).ok;
    } catch (e) {
      console.error("Failed to clear override:", e);
      return false;
    }
  },

  getPresetLabel(preset) {
    return preset?.name || "Unnamed";
  },

  getPresetSummary(preset) {
    if (!preset) return "";
    const parts = [];
    if (preset.chat?.name) parts.push(preset.chat.name);
    if (preset.utility?.name) parts.push(preset.utility.name);
    return parts.join(" / ");
  },

  // Model summary for agent-settings page
  async loadModelsSummary() {
    const data = await this._fetchConfigData();
    const cfg = data.config || {};
    const chatP = data.chat_providers || [];
    const embedP = data.embedding_providers || [];
    const label = (list, id) => (list.find(x => x.value === id) || {}).label || id || '\u2014';
    return [
      { icon: 'chat', title: 'Main', cfg: cfg.chat_model, pList: chatP },
      { icon: 'manufacturing', title: 'Utility', cfg: cfg.utility_model, pList: chatP },
      { icon: 'database', title: 'Embedding', cfg: cfg.embedding_model, pList: embedP },
    ].map(s => ({ icon: s.icon, title: s.title, provider: label(s.pList, s.cfg?.provider), name: s.cfg?.name || '\u2014' }));
  },

  // Switcher high-level methods
  async refreshSwitcher(contextId) {
    this.switcherLoading = true;
    try {
      const state = await this.loadSwitcherState(contextId);
      this.switcherAllowed = state.allowed;
      this.switcherPresets = state.presets;
      this.switcherOverride = state.override;
    } catch (e) {
      console.error('Model switcher refresh failed:', e);
    } finally {
      this.switcherLoading = false;
    }
  },

  async selectPresetSwitch(contextId, presetName) {
    const ok = await this.setPresetOverride(contextId, presetName);
    if (ok) this.switcherOverride = { preset_name: presetName };
    return ok;
  },

  async clearOverrideSwitch(contextId) {
    const ok = await this.clearOverride(contextId);
    if (ok) this.switcherOverride = null;
    return ok;
  },

  getSwitcherLabel() {
    const o = this.switcherOverride;
    if (!o) return 'Default LLM';
    return o.preset_name || o.name || o.provider || 'Custom';
  },

  // Text conversion utilities (accessible from templates via $store.modelConfig)
  textToKwargs,
  textToHeaders,
  kwargsToText,
  MODEL_SECTIONS,
});
