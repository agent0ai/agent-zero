import { createStore } from "/js/AlpineStore.js";

// define the model object holding data and functions
const model = {
  connected: false,
  coworkEnabled: false,
  coworkAllowedCount: 0,
  coworkPending: 0,

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
