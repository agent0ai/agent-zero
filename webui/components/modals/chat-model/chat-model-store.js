import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { toast, toastFetchError } from "/index.js";

const model = {
  contextId: null,
  isCustom: false,
  settings: {},
  providers: [],
  loading: false,
  saving: false,
  closePromise: null,

  resetState() {
    this.contextId = null;
    this.isCustom = false;
    this.settings = {};
    this.providers = [];
    this.loading = false;
    this.saving = false;
    this.closePromise = null;
  },

  async open(contextId) {
    if (!contextId) {
      toast("Invalid chat context", "error");
      return;
    }

    this.resetState();
    this.contextId = contextId;
    this.loading = true;

    try {
      const modalPromise = window.openModal("modals/chat-model/chat-model-modal.html");
      this.closePromise = modalPromise;
      if (modalPromise && typeof modalPromise.then === "function") {
        modalPromise.then(() => {
          if (this.closePromise === modalPromise) {
            this.resetState();
          }
        });
      }

      const data = await callJsonApi("/chat_model_get", { context: contextId });
      this.isCustom = data.is_custom || false;
      this.settings = data.settings || {};
      this.providers = data.providers || [];
    } catch (e) {
      toastFetchError("Error loading chat model settings", e);
    } finally {
      this.loading = false;
    }
  },

  async save() {
    this.saving = true;
    try {
      await callJsonApi("/chat_model_set", {
        context: this.contextId,
        is_custom: this.isCustom,
        settings: this.settings,
      });
      toast(
        this.isCustom
          ? "Custom model saved for this chat"
          : "Chat reset to global model settings",
        "success"
      );
      window.closeModal();
    } catch (e) {
      toastFetchError("Error saving chat model settings", e);
    } finally {
      this.saving = false;
    }
  },

  cancel() {
    window.closeModal();
  },
};

export const store = createStore("chatModelStore", model);
