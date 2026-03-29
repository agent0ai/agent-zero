import { createStore } from "/js/AlpineStore.js";
import { toastFrontendError } from "/components/notifications/notification-store.js";
import { callJsonApi } from "/js/api.js";
import { ttsService } from "/js/tts-service.js";

const PLUGIN_NAME = "_kokoro_tts";

const model = {
  runtimeInitialized: false,
  statusLoaded: false,
  loading: false,
  error: "",
  enabled: false,
  config: {
    voice: "",
    speed: 1.1,
  },
  modelReady: false,
  modelLoading: false,
  packageVersion: "",
  providerCleanup: null,

  async initRuntime() {
    if (this.runtimeInitialized) return;
    this.runtimeInitialized = true;
    await this.refreshStatus({ suppressError: true });
  },

  async ensureStatusLoaded() {
    if (this.statusLoaded || this.loading) return;
    await this.refreshStatus({ suppressError: true });
  },

  async refreshStatus({ suppressError = false } = {}) {
    this.loading = true;
    this.error = "";

    try {
      const status = await callJsonApi(`/plugins/${PLUGIN_NAME}/status`, {});
      this.statusLoaded = true;
      this.enabled = !!status?.enabled;
      this.config = {
        voice: status?.config?.voice || "",
        speed: Number(status?.config?.speed || 1.1),
      };
      this.modelReady = !!status?.model?.ready;
      this.modelLoading = !!status?.model?.loading;
      this.packageVersion = status?.package?.version || "";

      if (this.enabled) {
        this.registerProvider();
      } else {
        this.unregisterProvider();
      }
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      this.unregisterProvider();
      if (!suppressError) {
        void toastFrontendError(this.error, "Kokoro TTS");
      }
    } finally {
      this.loading = false;
    }
  },

  registerProvider() {
    if (this.providerCleanup || !this.enabled) return;

    this.providerCleanup = ttsService.registerProvider(PLUGIN_NAME, {
      synthesize: async (text) => {
        const result = await callJsonApi(`/plugins/${PLUGIN_NAME}/synthesize`, {
          text,
        });
        if (!result?.success) {
          throw new Error(result?.error || "Kokoro TTS synthesis failed.");
        }

        return {
          audioBase64: result.audio || "",
          mimeType: result.mime_type || "audio/wav",
        };
      },
    });
  },

  unregisterProvider() {
    if (!this.providerCleanup) return;
    this.providerCleanup();
    this.providerCleanup = null;
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

  async openConfig() {
    const { store } = await import("/components/plugins/plugin-settings-store.js");
    await store.openConfig(PLUGIN_NAME);
  },

  openPanel() {
    window.openModal?.(`/plugins/${PLUGIN_NAME}/webui/main.html`);
  },
};

export const store = createStore("kokoroTts", model);
