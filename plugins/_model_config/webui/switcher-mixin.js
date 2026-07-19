import { fetchApi } from "/js/api.js";

const API_BASE = "/plugins/_model_config";
const CREATE_AGENT_PROFILE_PROMPT = `I want to create a new Agent Zero agent profile.

Use the a0-create-agent skill. Guide me gently with one or two questions per turn. Start by asking what this agent should be excellent at, infer sensible defaults, and only produce the AgentProfileBlueprint JSON after we confirm the compact profile summary. Prefer a normal user profile in /a0/usr/agents unless I choose another scope.`;

function normalizeModelIdentity(value) {
  if (!value || typeof value !== "object") return null;
  const provider = String(value.provider || "").trim();
  const name = String(value.name || "").trim();
  if (!provider && !name) return null;
  return { provider, name };
}

export function getModelLeafName(value) {
  const name = String(typeof value === "string" ? value : value?.name || "").trim();
  if (!name) return "";
  const leaf = name.slice(name.lastIndexOf("/") + 1).trim();
  return leaf || name;
}

export const switcherState = {
  switcherAllowed: false,
  switcherOverride: null,
  switcherConfiguredPreset: "Default",
  switcherEffectivePreset: "Default",
  switcherPresets: [],
  switcherLoading: true,
  agentProfiles: [],
  agentProfilesLoading: true,
  agentProfileSettings: null,
  agentProfileSaving: false,
};

export const switcherMethods = {
  async loadAgentProfiles(force = false) {
    if (!force && this.agentProfiles.length > 0 && this.agentProfileSettings) return this.agentProfiles;
    this.agentProfilesLoading = true;
    try {
      const res = await fetchApi("/settings_get", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      this.agentProfileSettings = data.settings || {};
      this.agentProfiles = (data.additional?.agent_subdirs || [])
        .map(profile => ({
          key: profile.value || profile.key || "",
          label: profile.label || profile.value || profile.key || "",
        }))
        .filter(profile => profile.key && profile.key !== "_example");
    } catch (e) {
      console.error("Agent profile list load failed:", e);
      this.agentProfiles = [];
    } finally {
      this.agentProfilesLoading = false;
    }
    return this.agentProfiles;
  },

  async loadSwitcherState(contextId) {
    const result = { allowed: false, presets: [], override: null, configuredPreset: "Default", effectivePreset: "Default" };
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
        result.configuredPreset = overData.configured_preset || "Default";
        result.effectivePreset = overData.effective_preset || result.configuredPreset;
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
      const data = await res.json();
      return data?.ok ? data : null;
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
      const data = await res.json();
      return data?.ok ? data : null;
    } catch (e) {
      console.error("Failed to clear override:", e);
      return false;
    }
  },

  getAgentProfileList(activeKey = "", activeLabel = "") {
    const profiles = [...(this.agentProfiles || [])];
    if (activeKey && !profiles.some(profile => profile.key === activeKey)) {
      profiles.unshift({ key: activeKey, label: activeLabel || activeKey });
    }
    return profiles;
  },

  async createAgentProfileChat(currentContextId = "") {
    try {
      const res = await fetchApi("/chat_create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_context: currentContextId || "" }),
      });
      const data = await res.json();
      if (!data.ok || !data.ctxid) return false;

      const chatsStore = window.Alpine?.store("chats");
      if (chatsStore?.selectChat) {
        await chatsStore.selectChat(data.ctxid);
      } else {
        window.setContext?.(data.ctxid);
      }

      const chatInputStore = window.Alpine?.store("chatInput");
      if (chatInputStore) {
        chatInputStore.message = CREATE_AGENT_PROFILE_PROMPT;
        setTimeout(() => {
          chatInputStore.adjustTextareaHeight?.();
          chatInputStore.focus?.();
        }, 0);
      }

      return true;
    } catch (e) {
      console.error("Failed to create agent profile chat:", e);
      window.toastFetchError?.("Failed to start profile creator", e);
      return false;
    }
  },

  async selectAgentProfile(contextId, agentProfile) {
    if (!contextId || !agentProfile) return false;
    if (this.agentProfileSaving) return false;
    const chatsStore = window.Alpine?.store("chats");
    const selectedContext = chatsStore?.selectedContext;
    if (selectedContext?.running) {
      window.justToast?.("Agent profile can be changed after the current run finishes.", "warning", 2500, "agent-profile-switch");
      return false;
    }

    const activeProfile = selectedContext?.agent_profile || "";
    if (activeProfile === agentProfile) return true;

    this.agentProfileSaving = true;
    try {
      await this.loadAgentProfiles();
      const res = await fetchApi("/agent_profile_set", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context_id: contextId, agent_profile: agentProfile }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      if (!data.ok) return false;

      const label = data.agent_profile_label || this.agentProfiles.find(profile => profile.key === agentProfile)?.label || agentProfile;
      if (selectedContext) {
        selectedContext.agent_profile = data.agent_profile || agentProfile;
        selectedContext.agent_profile_label = label;
      }
      await this.refreshSwitcher(contextId);
      window.justToast?.(`Agent profile: ${label}`, "success", 1600, "agent-profile-switch");
      return true;
    } catch (e) {
      console.error("Failed to set active agent profile:", e);
      window.toastFetchError?.("Failed to set agent profile", e);
      return false;
    } finally {
      this.agentProfileSaving = false;
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
      this.switcherConfiguredPreset = state.configuredPreset;
      this.switcherEffectivePreset = state.effectivePreset;
    } catch (e) {
      console.error('Model switcher refresh failed:', e);
    } finally {
      this.switcherLoading = false;
    }
  },

  async selectPresetSwitch(contextId, presetName) {
    const data = await this.setPresetOverride(contextId, presetName);
    if (data) {
      const selected = data.preset_name || presetName;
      this.switcherOverride = { preset_name: selected };
      this.switcherEffectivePreset = selected;
    }
    return !!data;
  },

  async clearOverrideSwitch(contextId) {
    const data = await this.clearOverride(contextId);
    if (data) {
      this.switcherOverride = null;
      this.switcherEffectivePreset = data.effective_preset || this.switcherConfiguredPreset || 'Default';
    }
    return !!data;
  },

  getSwitcherLabel() {
    const o = this.switcherOverride;
    const presetName = this.switcherEffectivePreset || o?.preset_name || 'Default';
    const preset = this.getActivePreset();
    if (preset) {
      const mainModelName = getModelLeafName(preset.chat);
      return mainModelName ? `${presetName} ${mainModelName}` : presetName;
    }
    if (!o || o.preset_name) return presetName;

    const models = this.getCustomOverrideModels();
    const mainModelName = getModelLeafName(models.main);
    return mainModelName ? `Custom ${mainModelName}` : 'Custom';
  },

  getActivePreset() {
    return this.switcherPresets.find(p => p.name === this.switcherEffectivePreset) || null;
  },

  getActiveModels() {
    const preset = this.getActivePreset();
    if (preset) {
      return {
        main: normalizeModelIdentity(preset.chat),
        utility: normalizeModelIdentity(preset.utility),
        embedding: normalizeModelIdentity(preset.embedding),
      };
    }
    return this.getCustomOverrideModels();
  },

  getCustomOverrideModels() {
    const o = this.switcherOverride;
    if (!o || o.preset_name) return { main: null, utility: null, embedding: null };
    return {
      main: normalizeModelIdentity(o.chat || o),
      utility: normalizeModelIdentity(o.utility),
      embedding: normalizeModelIdentity(o.embedding),
    };
  },
};
