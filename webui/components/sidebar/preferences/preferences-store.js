import { createStore } from "/js/AlpineStore.js";

// Preferences store centralizes sidebar toggle state and side-effects
const model = {
  // UI toggles (persist only where legacy behavior requires it)
  autoScroll: true,
  darkMode: localStorage.getItem("darkMode") !== "false",
  speech: localStorage.getItem("speech") === "true",
  showThoughts: true,
  showJson: false,
  showUtils: false,

  // Initialize preferences and apply current state
  init() {
    try {
      this.applyDarkMode(this.darkMode);
      this.applyAutoScroll(this.autoScroll);
      this.applySpeech(this.speech);
      this.applyShowThoughts(this.showThoughts);
      this.applyShowJson(this.showJson);
      this.applyShowUtils(this.showUtils);
    } catch (e) {
      console.error("Failed to initialize preferences store", e);
    }
  },

  // Side-effect appliers delegate to existing global handlers for parity
  applyAutoScroll(value = this.autoScroll) {
    if (typeof globalThis.toggleAutoScroll === "function") {
      globalThis.toggleAutoScroll(value);
    }
  },

  applyDarkMode(value = this.darkMode) {
    if (typeof globalThis.toggleDarkMode === "function") {
      globalThis.toggleDarkMode(value);
    }
  },

  applySpeech(value = this.speech) {
    if (typeof globalThis.toggleSpeech === "function") {
      globalThis.toggleSpeech(value);
    }
  },

  applyShowThoughts(value = this.showThoughts) {
    if (typeof globalThis.toggleThoughts === "function") {
      globalThis.toggleThoughts(value);
    }
  },

  applyShowJson(value = this.showJson) {
    if (typeof globalThis.toggleJson === "function") {
      globalThis.toggleJson(value);
    }
  },

  applyShowUtils(value = this.showUtils) {
    if (typeof globalThis.toggleUtils === "function") {
      globalThis.toggleUtils(value);
    }
  },
};

export const store = createStore("preferences", model);


