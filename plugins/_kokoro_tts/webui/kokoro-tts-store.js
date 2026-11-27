import { createStore } from "/js/AlpineStore.js";
import { toastFrontendError } from "/components/notifications/notification-store.js";
import { callJsonApi } from "/js/api.js";
import { ttsService } from "/js/tts-service.js";

const PLUGIN_NAME = "_kokoro_tts";

const model = {
  id: PLUGIN_NAME,
  error: "",
  enabled: false,
  config: {
    voice: "",
    voice_weights: {},
    speed: 1.1,
  },
  modelReady: false,
  modelLoading: false,
  packageVersion: "",

  async refreshStatus({ suppressError = false } = {}) {
    this.error = "";

    try {
      const status = await callJsonApi(`/plugins/${PLUGIN_NAME}/status`, {});
      this.enabled = !!status?.enabled;
      this.config = {
        voice: status?.config?.voice || "",
        voice_weights: status?.config?.voice_weights || {},
        speed: Number(status?.config?.speed || 1.1),
      };
      this.modelReady = !!status?.model?.ready;
      this.modelLoading = !!status?.model?.loading;
      this.packageVersion = status?.package?.version || "";
      if (this.enabled && !ttsService.extensionProvider) ttsService.setExtensionProvider(store);
      if (!this.enabled && ttsService.extensionProvider === store) ttsService.setExtensionProvider(null);
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      if (!suppressError) {
        void toastFrontendError("Could not read the speech settings.", this.error);
      }
    }
  },

  async synthesize(text, { onInitializing } = {}) {
    this.modelLoading = true;
    try {
      const result = await callJsonApi(`/plugins/${PLUGIN_NAME}/synthesize`,
        { text, report_initialization: !!onInitializing },
        response => {
          if (response.headers.get("X-A0-Speech-Initializing") === "1") onInitializing?.();
        });
      if (!result?.success || !result.audio) {
        throw new Error(result?.error || "Local TTS returned no audio.");
      }
      this.modelReady = true;
      return { audioBase64: result.audio, mimeType: result.mime_type || "audio/wav" };
    } finally {
      this.modelLoading = false;
    }
  },

  get statusText() {
    if (!this.enabled) return "Disabled";
    if (this.modelLoading) return "Loading";
    if (this.modelReady) return "Ready";
    return "Idle";
  },

  get statusClass() {
    if (!this.enabled) return "warn";
    if (this.modelLoading) return "warn";
    if (this.modelReady) return "ok";
    return "warn";
  },

  get voiceSummary() {
    if (this.config.voice === "paradee") return "Paradee · Heart";
    const entries = Object.entries(this.config.voice_weights || {});
    if (!entries.length) return this.config.voice || "";

    const total = entries.reduce((sum, [, weight]) => sum + Number(weight || 0), 0);
    if (total <= 0) return this.config.voice || "";
    return entries
      .map(([voice, weight]) => `${voice} ${Math.round((Number(weight) / total) * 100)}%`)
      .join(" · ");
  },

  get modelName() {
    return this.config.voice === "paradee" ? "Paradee-8M" : "Kokoro-82M";
  },

  async openConfig() {
    const { store } = await import("/components/plugins/plugin-settings-store.js");
    await store.openConfig(PLUGIN_NAME);
  },

  openPanel() {
    window.openModal?.(`/plugins/${PLUGIN_NAME}/webui/main.html`);
  },
};

export const store = createStore("kokoroTts", model);

window.addEventListener("plugin-config-saved", (event) => {
  if (event.detail?.pluginName === PLUGIN_NAME) void store.refreshStatus();
});
