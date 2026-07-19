import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";
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

function clonePlain(value) {
  if (value === undefined) return undefined;
  return JSON.parse(JSON.stringify(value));
}

function isBlankPresetValue(value) {
  if (value === undefined || value === null || value === '') return true;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}

const IMPLICIT_PRESET_SLOT_DEFAULTS = {
  utility: {
    ctx_length: 128000,
    ctx_input: 0.7,
    rl_requests: 0,
    rl_input: 0,
    rl_output: 0,
    kwargs: {},
  },
  embedding: {
    rl_requests: 0,
    rl_input: 0,
    kwargs: {},
  },
};
const PRESET_REPLACE_FIELDS = new Set(['kwargs']);

function presetDefaultValuesEqual(value, defaultValue) {
  if (typeof defaultValue === 'number') return Number(value) === defaultValue;
  return JSON.stringify(value) === JSON.stringify(defaultValue);
}

function cleanPresetSlot(
  slot,
  stripApiKey = true,
  slotKey = '',
  preserveImplicitDefaults = false,
) {
  const clean = {};
  const implicitDefaults = IMPLICIT_PRESET_SLOT_DEFAULTS[slotKey] || {};
  for (const [key, value] of Object.entries(slot || {})) {
    if (key.startsWith('_')) continue;
    if (stripApiKey && key === 'api_key') continue;
    if (key === 'api_base' && value === '') {
      clean[key] = value;
      continue;
    }
    if (key === 'kwargs' && isBlankPresetValue(value)) continue;
    if (isBlankPresetValue(value)) continue;
    if (
      !preserveImplicitDefaults
      && key in implicitDefaults
      && presetDefaultValuesEqual(value, implicitDefaults[key])
    ) continue;
    clean[key] = value;
  }
  return clean;
}

function hasModelIdentity(slot) {
  return !!(slot?.provider || slot?.name);
}

export function mergeModelSlot(baseSlot, presetSlot, stripApiKey = true, slotKey = '') {
  const result = clonePlain(baseSlot || {});
  const clean = cleanPresetSlot(presetSlot, stripApiKey, slotKey);
  for (const [key, value] of Object.entries(clean)) {
    if (
      value &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      result[key] &&
      typeof result[key] === 'object' &&
      !Array.isArray(result[key])
    ) {
      result[key] = mergeModelSlot(result[key], value, false);
    } else {
      result[key] = clonePlain(value);
    }
  }
  for (const key of PRESET_REPLACE_FIELDS) {
    if (Object.prototype.hasOwnProperty.call(clean, key)) {
      const value = clean[key];
      result[key] = value && typeof value === 'object' && !Array.isArray(value) ? clonePlain(value) : {};
    } else if (Object.prototype.hasOwnProperty.call(baseSlot || {}, key)) {
      result[key] = {};
    }
  }
  return result;
}

export function configFromPreset(preset, baseConfig, stripApiKey = true) {
  const config = clonePlain(baseConfig || {});
  const slots = [
    ['chat', 'chat_model'],
    ['utility', 'utility_model'],
    ['embedding', 'embedding_model'],
  ];

  for (const [slotKey, sectionKey] of slots) {
    const slot = preset?.[slotKey];
    if (!slot || typeof slot !== 'object') continue;
    if (!hasModelIdentity(slot)) continue;
    config[sectionKey] = mergeModelSlot(config[sectionKey] || {}, slot, stripApiKey, slotKey);
  }

  return config;
}

// ── Alpine Store ──

const API_BASE = "/plugins/_model_config";
export const DEFAULT_PRESET_NAME = "Default";

export const store = createStore("modelConfig", {
  // Core state
  chatProviders: [],
  embeddingProviders: [],
  chatProviderDetails: [],
  embeddingProviderDetails: [],
  modelConfigured: false,
  modelConfiguredLabel: "",
  _loaded: false,

  // API Keys state (from mixin)
  ...apiKeysState,

  // Global presets state
  globalPresets: [],
  _presetsLoaded: false,
  _lastPresetReferenceChanges: {},

  // Model summary state
  modelsSummary: [],
  modelsSummaryPreset: DEFAULT_PRESET_NAME,
  modelsSummaryLoading: false,
  _modelsSummaryLoaded: false,
  _modelsSummaryPromise: null,
  presetEditorInitialName: DEFAULT_PRESET_NAME,
  _presetEditorSelectionPinned: false,

  // Switcher state (from mixin)
  ...switcherState,

  init() {},

  // ── API Keys methods (from mixin) ──
  ...apiKeysMethods,

  // ── Switcher methods (from mixin) ──
  ...switcherMethods,

  // ── Core methods ──

  _normalizePresets(rawPresets) {
    const source = (rawPresets || []).filter(p => p && typeof p === 'object');
    const rawDefault = source.find(p => String(p.name || '').toLowerCase() === 'default') || {};
    const slot = value => ({ provider: '', name: '', api_key: '', api_base: '', kwargs: {}, ...(value || {}) });
    const defaultConfig = {
      chat_model: slot(rawDefault.chat),
      utility_model: slot(rawDefault.utility),
      embedding_model: slot(rawDefault.embedding),
    };

    return source.map(p => {
      const effective = String(p.name || '').toLowerCase() === 'default'
        ? defaultConfig
        : configFromPreset(p, defaultConfig, true);
      return {
        name: p.name || '',
        chat: { ...slot(effective.chat_model), _kwargs_text: kwargsToText(effective.chat_model?.kwargs) },
        utility: { ...slot(effective.utility_model), _kwargs_text: kwargsToText(effective.utility_model?.kwargs) },
        embedding: { ...slot(effective.embedding_model), _kwargs_text: kwargsToText(effective.embedding_model?.kwargs) },
      };
    });
  },

  async ensureLoaded() {
    if (this._loaded) return;
    const data = await this._fetchConfigData();
    this.chatProviders = data.chat_providers || [];
    this.embeddingProviders = data.embedding_providers || [];
    this.chatProviderDetails = data.chat_provider_details || [];
    this.embeddingProviderDetails = data.embedding_provider_details || [];
    this.apiKeyStatus = data.api_key_status || {};
    this.modelConfigured = !!data.model_configured;
    this.modelConfiguredLabel = data.model_configured_label || "";
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

  async _fetchConfigData(input = {}) {
    const res = await fetchApi(`${API_BASE}/model_config_get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input)
    });
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  },

  // Config field initialization (converts kwargs dicts to editable text)
  initConfigFields(config) {
    if (config?.chat_model) config.chat_model._kwargs_text = kwargsToText(config.chat_model.kwargs);
    if (config?.utility_model) config.utility_model._kwargs_text = kwargsToText(config.utility_model.kwargs);
    if (config?.embedding_model) config.embedding_model._kwargs_text = kwargsToText(config.embedding_model.kwargs);
  },

  syncContextConfigFields(context, refreshCleanSnapshot = false) {
    const config = context?.settings;
    if (!config || typeof config !== 'object') return;

    const snapshotBeforeInit = refreshCleanSnapshot && typeof context._toComparableJson === 'function'
      ? context._toComparableJson(config)
      : null;

    const selected = String(config.model_preset || DEFAULT_PRESET_NAME).trim();
    context.settings = {
      model_preset: this.globalPresets.some(p => p.name === selected)
        ? selected
        : DEFAULT_PRESET_NAME,
    };

    if (
      refreshCleanSnapshot &&
      typeof context._toComparableJson === 'function' &&
      context.settingsSnapshotJson === snapshotBeforeInit
    ) {
      context.settingsSnapshotJson = context._toComparableJson(context.settings);
    }
  },

  // Global presets
  createPresetEditor(initialName = '') {
    const store = this;
    let nextPresetKey = 0;
    const presets = clonePlain(this.globalPresets).map(preset => ({
      ...preset,
      _originalName: preset.name,
      _key: nextPresetKey++,
    }));
    const initial = presets.find(p => p.name === initialName)
      || presets.find(p => p.name === DEFAULT_PRESET_NAME)
      || presets[0]
      || null;

    return {
      presets,
      selectedKey: initial?._key ?? null,
      get selectedPreset() {
        return this.presets.find(p => p._key === this.selectedKey) || null;
      },
      get canRenameSelected() {
        return !!this.selectedPreset && this.selectedPreset._originalName !== DEFAULT_PRESET_NAME;
      },
      get canDeleteSelected() {
        return this.canRenameSelected;
      },
      uniquePresetName(preferred = 'New Preset') {
        const names = new Set(this.presets.map(p => String(p.name || '').toLowerCase()));
        let candidate = preferred;
        let suffix = 2;
        while (names.has(candidate.toLowerCase())) candidate = `${preferred} ${suffix++}`;
        return candidate;
      },
      addPreset() {
        const base = clonePlain(
          this.presets.find(p => p.name === DEFAULT_PRESET_NAME)
          || this.presets[0]
          || {
            chat: { provider: '', name: '', api_base: '', kwargs: {}, _kwargs_text: '' },
            utility: { provider: '', name: '', api_base: '', kwargs: {}, _kwargs_text: '' },
            embedding: { provider: '', name: '', api_base: '', kwargs: {}, _kwargs_text: '' },
          }
        );
        const preset = {
          ...base,
          _key: nextPresetKey++,
          _originalName: '',
          name: this.uniquePresetName(),
        };
        this.presets = [...this.presets, preset];
        this.selectedKey = preset._key;
      },
      removeSelectedPreset() {
        if (!this.canDeleteSelected) return;
        const removeKey = this.selectedKey;
        this.presets = this.presets.filter(p => p._key !== removeKey);
        this.selectedKey = this.presets.find(p => p.name === DEFAULT_PRESET_NAME)?._key
          ?? this.presets[0]?._key
          ?? null;
      },
      async savePresets() {
        if (this.selectedPreset && !String(this.selectedPreset.name || '').trim()) {
          globalThis.justToast?.('Preset names cannot be empty.', 'error');
          return false;
        }
        try {
          await store.persistAllDirtyApiKeys();
        } catch (e) {
          console.error('Failed to save API keys:', e);
          globalThis.justToast?.(e?.message || 'Failed to save API keys.', 'error');
          return false;
        }
        if (!await store.saveGlobalPresets(this.presets)) return false;
        this.refreshPresets();
        return true;
      },
      refreshPresets() {
        const selectedName = this.selectedPreset?.name || initialName || DEFAULT_PRESET_NAME;
        this.presets = clonePlain(store.globalPresets).map(preset => ({
          ...preset,
          _originalName: preset.name,
          _key: nextPresetKey++,
        }));
        this.selectedKey = this.presets.find(p => p.name === selectedName)?._key
          ?? this.presets.find(p => p.name === DEFAULT_PRESET_NAME)?._key
          ?? this.presets[0]?._key
          ?? null;
      },
      async resetPresets() {
        if (!await store.resetGlobalPresets()) return;
        this.refreshPresets();
        globalThis.justToast?.('Presets reset to default.', 'info');
      },
    };
  },

  async loadGlobalPresets() {
    try {
      const res = await fetchApi(`${API_BASE}/model_presets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get' })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      this.globalPresets = this._normalizePresets(data.presets);
    } catch (e) {
      console.error('Failed to load global presets:', e);
      this.globalPresets = [];
    }
    this._presetsLoaded = true;
  },

  async saveGlobalPresets(presets) {
    const previousNames = this.globalPresets.map(p => String(p.name || '')).filter(Boolean);
    // Strip UI-only and globally-managed fields before saving
    const clean = presets.map(p => {
      const c = { name: p.name };
      const isDefault = p._originalName === DEFAULT_PRESET_NAME;
      for (const slot of ['chat', 'utility']) {
        if (p[slot]) {
          const rest = cleanPresetSlot(p[slot], true, slot, isDefault);
          if (hasModelIdentity(rest)) c[slot] = rest;
        }
      }
      if (p.embedding) {
        const embedding = cleanPresetSlot(p.embedding, true, 'embedding', isDefault);
        if (hasModelIdentity(embedding)) c.embedding = embedding;
      }
      return c;
    });
    const renames = presets
      .filter(p => p._originalName && p._originalName !== p.name)
      .map(p => ({ from: p._originalName, to: p.name }));
    try {
      const res = await fetchApi(`${API_BASE}/model_presets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'save', presets: clean, renames })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      this.globalPresets = this._normalizePresets(data.presets || clean);
      const savedNames = new Set(this.globalPresets.map(p => p.name));
      this._lastPresetReferenceChanges = Object.fromEntries([
        ...previousNames
          .filter(name => !savedNames.has(name))
          .map(name => [name.toLowerCase(), DEFAULT_PRESET_NAME]),
        ...renames.map(rename => [String(rename.from).toLowerCase(), rename.to]),
      ]);
      this.modelsSummaryPreset = this.remapPresetName(this.modelsSummaryPreset);
      this.switcherConfiguredPreset = this.remapPresetName(this.switcherConfiguredPreset);
      this.switcherEffectivePreset = this.remapPresetName(this.switcherEffectivePreset);
      this.switcherPresets = this.globalPresets.filter(p => p.name);
      globalThis.justToast?.('Presets saved', 'success');
      return this.globalPresets;
    } catch (e) {
      console.error('Failed to save global presets:', e);
      globalThis.justToast?.(e?.message || 'Failed to save presets', 'error');
      return false;
    }
  },

  async resetGlobalPresets() {
    const previousNames = this.globalPresets.map(p => String(p.name || '')).filter(Boolean);
    try {
      const res = await fetchApi(`${API_BASE}/model_presets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reset' })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      this.globalPresets = this._normalizePresets(data.presets);
      const savedNames = new Set(this.globalPresets.map(p => p.name));
      this._lastPresetReferenceChanges = Object.fromEntries(
        previousNames
          .filter(name => !savedNames.has(name))
          .map(name => [name.toLowerCase(), DEFAULT_PRESET_NAME])
      );
      this.modelsSummaryPreset = this.remapPresetName(this.modelsSummaryPreset);
      this.switcherConfiguredPreset = this.remapPresetName(this.switcherConfiguredPreset);
      this.switcherEffectivePreset = this.remapPresetName(this.switcherEffectivePreset);
      this.switcherPresets = this.globalPresets.filter(p => p.name);
      this._presetsLoaded = true;
      return true;
    } catch (e) {
      console.error('Failed to reset presets:', e);
      globalThis.justToast?.('Failed to reset presets', 'error');
      return false;
    }
  },

  /**
   * Install hooks on the plugin settings context.
   * Keep the generic plugin settings modal selection-only across scope changes,
   * saves, and resets.
   */
  installSettingsHooks(context) {
    if (!context || context.__modelConfigHooksInstalled) return;

    this.syncContextConfigFields(context, true);

    const originalLoadSettings = context.loadSettings?.bind(context);
    if (originalLoadSettings) {
      context.loadSettings = async (...args) => {
        const result = await originalLoadSettings(...args);
        this.syncContextConfigFields(context, true);
        return result;
      };
    }

    context.save = async () => {
      context.error = null;
      this.syncContextConfigFields(context);
      context.isSaving = true;
      try {
        const res = await fetchApi(`${API_BASE}/model_presets`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'select',
            name: context.settings.model_preset,
            project_name: context.projectName || '',
            agent_profile: context.agentProfileKey || '',
          }),
        });
        if (!res.ok) {
          context.error = await res.text() || 'Save failed';
          return;
        }
        context.settingsSnapshotJson = context._toComparableJson(context.settings);
        const contextId = window.Alpine?.store('chats')?.selected || '';
        if (contextId) await this.refreshSwitcher(contextId);
        window.closeModal?.();
      } catch (e) {
        context.error = e?.message || 'Save failed';
      } finally {
        context.isSaving = false;
      }
    };

    const originalReset = context.resetToDefault.bind(context);
    context.resetToDefault = async () => {
      const before = context.settings;
      await originalReset();
      if (context.settings !== before) {
        this.syncContextConfigFields(context);
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

  async searchModelsDetailed(provider, query, modelType, apiBase) {
    if (!provider) return { models: [], provider: '', source: 'none', error: '' };
    try {
      const res = await fetchApi(`${API_BASE}/model_search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, query: query || '', model_type: modelType || 'chat', api_base: apiBase || '' })
      });
      const data = await res.json();
      return {
        models: data.models || [],
        provider: data.provider || provider,
        source: data.source || '',
        error: data.error || '',
      };
    } catch (e) {
      console.error('Model search failed:', e);
      return { models: [], provider, source: 'error', error: e?.message || String(e) };
    }
  },

  async searchModels(provider, query, modelType, apiBase) {
    const data = await this.searchModelsDetailed(provider, query, modelType, apiBase);
    return data.models || [];
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

  presetModelRows(preset) {
    const chatP = this.chatProviders || [];
    const embedP = this.embeddingProviders || [];
    const label = (list, id) => (list.find(x => x.value === id) || {}).label || id || '\u2014';
    return [
      { icon: 'chat', title: 'Main', cfg: preset?.chat, pList: chatP },
      { icon: 'manufacturing', title: 'Utility', cfg: preset?.utility, pList: chatP },
      { icon: 'database', title: 'Embedding', cfg: preset?.embedding, pList: embedP },
    ].map(s => ({ icon: s.icon, title: s.title, provider: label(s.pList, s.cfg?.provider), name: s.cfg?.name || '\u2014' }));
  },

  getPreset(name) {
    return this.globalPresets.find(p => p.name === name)
      || this.globalPresets.find(p => p.name === DEFAULT_PRESET_NAME)
      || null;
  },

  remapPresetName(name) {
    const current = String(name || DEFAULT_PRESET_NAME);
    const renamed = this._lastPresetReferenceChanges[current.toLowerCase()];
    if (renamed && this.globalPresets.some(p => p.name === renamed)) return renamed;
    if (this.globalPresets.some(p => p.name === current)) return current;
    return DEFAULT_PRESET_NAME;
  },

  createScopedPresetSelector(context) {
    const store = this;
    return {
      context,
      loading: true,
      showScopedSettings: false,
      get presets() { return store.globalPresets; },
      get presetDescription() {
        const project = String(context?.projectName || '');
        const profile = String(context?.agentProfileKey || '');
        if (project && profile) return 'Default for this project and agent profile.';
        if (project) return 'Default for this project.';
        if (profile) return 'Default for this agent profile.';
        return 'Global default for all projects and agent profiles.';
      },
      get selectedPresetName() {
        return String(context?.settings?.model_preset || DEFAULT_PRESET_NAME);
      },
      get modelRows() { return store.presetModelRows(store.getPreset(this.selectedPresetName)); },
      async init() {
        this.loading = true;
        try {
          await store.ensureLoaded();
          await store.loadGlobalPresets();
          store.syncContextConfigFields(context, true);
          store.installSettingsHooks(context);
        } finally {
          this.loading = false;
        }
      },
      selectPreset(name) {
        context.settings.model_preset = name || DEFAULT_PRESET_NAME;
      },
      async editPresets() {
        await store.openPresetEditor(this.selectedPresetName);
        context.settings.model_preset = store.remapPresetName(this.selectedPresetName);
      },
      apiKeys() { return store.openApiKeysFromSummary(); },
    };
  },

  createGlobalPresetSelector() {
    const store = this;
    return {
      contextId: '',
      selectedPresetName: DEFAULT_PRESET_NAME,
      loading: true,
      presetDescription: 'Global default for new chats. Changing it also updates the open chat.',
      showScopedSettings: true,
      get presets() { return store.globalPresets; },
      get modelRows() { return store.presetModelRows(store.getPreset(this.selectedPresetName)); },
      async init(contextId = '') {
        this.contextId = String(contextId || '');
        this.loading = true;
        try {
          await store.ensureLoaded();
          const data = await store._fetchConfigData(
            this.contextId ? { context_id: this.contextId } : {}
          );
          store.globalPresets = store._normalizePresets(data.presets || []);
          store._presetsLoaded = true;
          this.selectedPresetName = data.selected_preset || data.configured_preset || DEFAULT_PRESET_NAME;
        } finally {
          this.loading = false;
        }
      },
      async selectPreset(name) {
        if (this.loading) return false;
        this.loading = true;
        try {
          const res = await fetchApi(`${API_BASE}/model_presets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action: 'select',
              name,
              context_id: this.contextId,
            }),
          });
          if (!res.ok) {
            const message = await res.text();
            globalThis.justToast?.(message || 'Failed to select model preset', 'error');
            return false;
          }
          const data = await res.json();
          this.selectedPresetName = data.selected_preset || name;
          store.modelsSummaryPreset = this.selectedPresetName;
          store.modelsSummary = this.modelRows;
          if (this.contextId) await store.refreshSwitcher(this.contextId);
          globalThis.justToast?.(`Model preset: ${this.selectedPresetName}`, 'success');
          return true;
        } catch (e) {
          console.error('Failed to select model preset:', e);
          globalThis.justToast?.(e?.message || 'Failed to select model preset', 'error');
          return false;
        } finally {
          this.loading = false;
        }
      },
      async editPresets() {
        await store.openPresetEditor(this.selectedPresetName, this.contextId);
        this.selectedPresetName = store.remapPresetName(this.selectedPresetName);
      },
      apiKeys() { return store.openApiKeysFromSummary(); },
      scopedSettings() { return store.openScopedPresetSettings(); },
    };
  },

  // Model summary for agent-settings page
  async loadModelsSummary(contextId = '') {
    await this.ensureLoaded();
    const data = await this._fetchConfigData(contextId ? { context_id: contextId } : {});
    const cfg = data.config || {};
    const chatP = data.chat_providers || [];
    const embedP = data.embedding_providers || [];
    this.globalPresets = this._normalizePresets(data.presets || this.globalPresets);
    this.modelsSummaryPreset = data.selected_preset || data.configured_preset || DEFAULT_PRESET_NAME;
    const label = (list, id) => (list.find(x => x.value === id) || {}).label || id || '\u2014';
    return [
      { icon: 'chat', title: 'Main', cfg: cfg.chat_model, pList: chatP },
      { icon: 'manufacturing', title: 'Utility', cfg: cfg.utility_model, pList: chatP },
      { icon: 'database', title: 'Embedding', cfg: cfg.embedding_model, pList: embedP },
    ].map(s => ({ icon: s.icon, title: s.title, provider: label(s.pList, s.cfg?.provider), name: s.cfg?.name || '\u2014' }));
  },

  async refreshModelsSummary(contextId = '') {
    if (this._modelsSummaryPromise) return await this._modelsSummaryPromise;

    this.modelsSummaryLoading = true;
    this._modelsSummaryPromise = (async () => {
      try {
        const models = await this.loadModelsSummary(contextId);
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
    return await this.openScopedPresetSettings();
  },

  async openScopedPresetSettings() {
    try {
      await pluginSettingsStore.openConfig('_model_config');
    } finally {
      await this.refreshModelsSummary();
    }
  },

  async openPresetsFromSummary() {
    await this.openPresetEditor(this.modelsSummaryPreset);
  },

  async openPresetEditor(name = DEFAULT_PRESET_NAME, contextId = '') {
    this.presetEditorInitialName = name || DEFAULT_PRESET_NAME;
    this._lastPresetReferenceChanges = {};
    if (contextId) await this.refreshSwitcher(contextId);
    this._presetEditorSelectionPinned = true;
    try {
      await window.openModal?.('/plugins/_model_config/webui/main.html');
    } finally {
      this._presetEditorSelectionPinned = false;
    }
  },

  async preparePresetEditor(contextId = '') {
    if (this._presetEditorSelectionPinned) return;
    try {
      const data = await this._fetchConfigData(
        contextId ? { context_id: contextId } : {}
      );
      this.presetEditorInitialName = data.selected_preset
        || data.configured_preset
        || DEFAULT_PRESET_NAME;
    } catch (e) {
      console.error('Failed to resolve the active model preset:', e);
      this.presetEditorInitialName = DEFAULT_PRESET_NAME;
    }
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
