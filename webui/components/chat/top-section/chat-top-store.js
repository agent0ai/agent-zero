import { createStore } from "/js/AlpineStore.js";

// define the model object holding data and functions
const model = {
  connected: false,
  connectionState: "connecting", // connecting | warming | ready | offline
  connectionMessage: "Connecting to backend...",
  coworkEnabled: false,
  coworkAllowedCount: 0,
  coworkPending: 0,

  setConnectionState(state, message = "") {
    this.connectionState = state;
    this.connected = state === "ready";

    if (message) {
      this.connectionMessage = message;
      return;
    }

    switch (state) {
      case "ready":
        this.connectionMessage = "Backend connected";
        break;
      case "warming":
        this.connectionMessage = "Backend is warming up";
        break;
      case "offline":
        this.connectionMessage = "Backend is unreachable";
        break;
      default:
        this.connectionMessage = "Connecting to backend...";
        break;
    }
  },

  updateCoworkStatus(payload) {
    if (!payload) return;
    this.coworkEnabled = !!payload.cowork_enabled;
    this.coworkAllowedCount = Number(payload.cowork_allowed_count || 0);
    this.coworkPending = Number(payload.cowork_pending || 0);
  },
};

// convert it to alpine store
const store = createStore("chatTop", model);

// export for use in other files
export { store };
