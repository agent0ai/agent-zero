import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";

const model = {
  loading: false,
  sending: false,
  calls: [],
  toNumber: "",
  fromNumber: "",
  message: "",
  mock: true,

  async init() {
    await this.refresh();
  },

  async refresh() {
    this.loading = true;
    try {
      const response = await fetchApi("/twilio_voice_list", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limit: 50 }),
      });
      const data = await response.json();
      this.calls = data.calls || [];
    } catch (error) {
      console.error("Failed to load Twilio calls:", error);
      window.toastFrontendError("Failed to load Twilio calls", "Twilio Voice");
    } finally {
      this.loading = false;
    }
  },

  async createCall() {
    if (!this.toNumber) {
      window.toastFrontendError("To number is required", "Twilio Voice");
      return;
    }
    this.sending = true;
    try {
      const response = await fetchApi("/twilio_voice_call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to_number: this.toNumber,
          from_number: this.fromNumber,
          message: this.message,
          mock: this.mock,
        }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Call failed");
      }
      this.toNumber = "";
      this.message = "";
      await this.refresh();
      window.toastFrontendInfo("Call queued", "Twilio Voice");
    } catch (error) {
      console.error("Failed to create Twilio call:", error);
      window.toastFrontendError("Failed to create Twilio call", "Twilio Voice");
    } finally {
      this.sending = false;
    }
  },
};

const store = createStore("twilioVoiceManager", model);

export { store };
