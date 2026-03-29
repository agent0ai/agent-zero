const API_BASE = "/plugins/_model_config";

export const switcherState = {
  switcherAllowed: false,
  switcherOverride: null,
  switcherPresets: [],
  switcherLoading: true,
};

export const switcherMethods = {
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

  getActivePreset() {
    const o = this.switcherOverride;
    if (!o || !o.preset_name) return null;
    return this.switcherPresets.find(p => p.name === o.preset_name) || null;
  },

  getActiveModels() {
    const preset = this.getActivePreset();
    if (!preset) return { main: null, utility: null };
    return {
      main: preset.chat?.name ? { provider: preset.chat.provider, name: preset.chat.name } : null,
      utility: preset.utility?.name ? { provider: preset.utility.provider, name: preset.utility.name } : null,
    };
  },
};
