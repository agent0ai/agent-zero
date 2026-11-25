import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import {
  toastFrontendSuccess,
  toastFrontendError,
  toastFrontendNotice,
} from "/components/notifications/notification-store.js";

export const store = createStore("compactStore", {
  compacting: false,
  stats: null,
  showModal: false,
  presets: [],
  selectedPresetName: "",
  useChatModel: true,

  minTokens: 1000,

  get canCompact() {
    return this.stats && this.stats.token_count >= this.minTokens;
  },

  get selectedModelDisplay() {
    if (this.selectedPresetName) {
      const preset = this.presets.find(
        (p) => p.name === this.selectedPresetName
      );
      if (preset) {
        const cfg = this.useChatModel ? preset.chat : preset.utility;
        if (cfg?.name) return cfg.name;
      }
    }
    return this.useChatModel
      ? this.stats?.chat_model_name || "Chat Model"
      : this.stats?.utility_model_name || "Utility Model";
  },

  async fetchStats() {
    try {
      const ctxid = globalThis.getContext?.();
      if (!ctxid) {
        toastFrontendNotice("error", "No active chat", "Compaction");
        return;
      }

      const [statsRes, presetsRes] = await Promise.all([
        callJsonApi("/plugins/_chat_compaction/compact_chat", {
          context: ctxid,
          action: "stats",
        }),
        callJsonApi("/plugins/_model_config/model_presets", {
          action: "get",
        }),
      ]);

      if (!statsRes?.ok) {
        throw new Error(statsRes?.message || "Failed to fetch stats");
      }

      this.stats = statsRes.stats;
      this.presets = presetsRes?.ok ? presetsRes.presets || [] : [];
      this.showModal = true;
    } catch (e) {
      toastFrontendError(e.message, "Compaction");
    }
  },

  async compact() {
    this.compacting = true;
    try {
      const ctxid = globalThis.getContext?.();
      if (!ctxid) {
        throw new Error("No active chat");
      }

      const res = await callJsonApi("/plugins/_chat_compaction/compact_chat", {
        context: ctxid,
        action: "compact",
        use_chat_model: this.useChatModel,
        preset_name: this.selectedPresetName || null,
      });

      if (!res?.ok) {
        throw new Error(res?.message || "Compaction failed");
      }

      toastFrontendSuccess("Compaction started", "Compaction");
      this.showModal = false;
    } catch (e) {
      toastFrontendError(e.message, "Compaction");
    } finally {
      this.compacting = false;
    }
  },

  closeModal() {
    this.showModal = false;
    this.stats = null;
    this.presets = [];
    this.selectedPresetName = "";
    this.useChatModel = true;
  },
});
