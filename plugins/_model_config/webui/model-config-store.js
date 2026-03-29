import { createStore } from "/js/AlpineStore.js";
import { store as pluginSettingsStore } from "/components/plugins/plugin-settings-store.js";
import { apiKeysState, apiKeysMethods } from "/plugins/_model_config/webui/api-keys-mixin.js";
import { switcherState, switcherMethods } from "/plugins/_model_config/webui/switcher-mixin.js";


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
  // Core state
  chatProviders: [],
  embeddingProviders: [],
  _loaded: false,

  // API Keys state (from mixin)
  ...apiKeysState,

  // Global presets state
  globalPresets: [],
  _presetsLoaded: false,

  // Model summary state
  modelsSummary: [],
  modelsSummaryLoading: false,
  _modelsSummaryLoaded: false,
  _modelsSummaryPromise: null,

  // Switcher state (from mixin)
  ...switcherState,

  init() {},

  // ── API Keys methods (from mixin) ──
  ...apiKeysMethods,

  // ── Switcher methods (from mixin) ──
  ...switcherMethods,

  // ── Core methods ──

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
    // Strip UI-only and globally-managed fields before saving
    const clean = presets.map(p => {
      const c = { name: p.name };
      for (const slot of ['chat', 'utility']) {
        if (p[slot]) {
          const { _kwargs_text, api_key, ...rest } = p[slot];
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

  /**
   * Install save and reset hooks on the plugin settings context.
   * - Save: persists dirty API keys before the normal config save.
   * - Reset: reloads global presets when settings are reset to defaults.
   */
  installSettingsHooks(context, config) {
    if (!context || context.__modelConfigHooksInstalled) return;

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

    const originalReset = context.resetToDefault.bind(context);
    context.resetToDefault = async () => {
      const before = context.settings;
      await originalReset();
      if (context.settings !== before) {
        await this.resetGlobalPresets();
      }
    };

    context.__modelConfigHooksInstalled = true;
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

  async refreshModelsSummary() {
    if (this._modelsSummaryPromise) return await this._modelsSummaryPromise;

    this.modelsSummaryLoading = true;
    this._modelsSummaryPromise = (async () => {
      try {
        const models = await this.loadModelsSummary();
        this.modelsSummary = models;
        this._modelsSummaryLoaded = true;
        return models;
      } catch (e) {
        console.error('Failed to load models summary:', e);
        this.modelsSummary = [];
        this._modelsSummaryLoaded = true;
        return [];
      }
    })();

    try {
      return await this._modelsSummaryPromise;
    } finally {
      this._modelsSummaryPromise = null;
      this.modelsSummaryLoading = false;
    }
  },

  async ensureModelsSummaryLoaded() {
    if (this._modelsSummaryLoaded) return this.modelsSummary;
    return await this.refreshModelsSummary();
  },

  async openConfigFromSummary() {
    try {
      await pluginSettingsStore.openConfig('_model_config');
    } finally {
      await this.refreshModelsSummary();
    }
  },

  async openPresetsFromSummary() {
    await window.openModal?.('/plugins/_model_config/webui/main.html');
  },

  async openApiKeysFromSummary() {
    try {
      await window.openModal?.('/plugins/_model_config/webui/api-keys.html');
    } finally {
      await this.refreshApiKeyStatus().catch((e) => {
        console.error('Failed to refresh API key status:', e);
      });
    }
  },

  // Text conversion utilities (accessible from templates via $store.modelConfig)
  textToKwargs,
  textToHeaders,
  kwargsToText,
  MODEL_SECTIONS,
});
