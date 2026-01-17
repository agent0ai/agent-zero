import { createStore } from "/js/AlpineStore.js";
import * as css from "/js/css.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";

// Preferences store centralizes user preference toggles and side-effects
const model = {
  // UI toggles (initialized with safe defaults, loaded from localStorage in init)
  get autoScroll() {
    return this._autoScroll;
  },
  set autoScroll(value) {
    this._autoScroll = value;
    this._applyAutoScroll(value);
  },
  _autoScroll: true,

  get darkMode() {
    return this._darkMode;
  },
  set darkMode(value) {
    this._darkMode = value;
    this._applyDarkMode(value);
  },
  _darkMode: true,

  get speech() {
    return this._speech;
  },
  set speech(value) {
    this._speech = value;
    this._applySpeech(value);
  },
  _speech: false,

  get showThoughts() {
    return this._showThoughts;
  },
  set showThoughts(value) {
    this._showThoughts = value;
    this._applyShowThoughts(value);
  },
  _showThoughts: true,

  get showJson() {
    return this._showJson;
  },
  set showJson(value) {
    this._showJson = value;
    this._applyShowJson(value);
  },
  _showJson: false,

  get showUtils() {
    return this._showUtils;
  },
  set showUtils(value) {
    this._showUtils = value;
    this._applyShowUtils(value);
  },
  _showUtils: false,

  // Initialize preferences and apply current state
  init() {
    try {
      // Load persisted preferences with safe fallbacks
      try {
        const storedDarkMode = localStorage.getItem("darkMode");
        this._darkMode = storedDarkMode !== "false";
      } catch {
        this._darkMode = true; // Default to dark mode if localStorage is unavailable
      }

      try {
        const storedSpeech = localStorage.getItem("speech");
        this._speech = storedSpeech === "true";
      } catch {
        this._speech = false; // Default to speech off if localStorage is unavailable
      }

      // Apply all preferences
      this._applyDarkMode(this._darkMode);
      this._applyAutoScroll(this._autoScroll);
      this._applySpeech(this._speech);
      this._applyShowThoughts(this._showThoughts);
      this._applyShowJson(this._showJson);
      this._applyShowUtils(this._showUtils);
    } catch (e) {
      console.error("Failed to initialize preferences store", e);
    }
  },

  _applyAutoScroll(value) {
    // nothing for now
  },

  _applyDarkMode(value) {
    if (value) {
      document.body.classList.remove("light-mode");
      document.body.classList.add("dark-mode");
    } else {
      document.body.classList.remove("dark-mode");
      document.body.classList.add("light-mode");
    }
    localStorage.setItem("darkMode", value);
  },

  _applySpeech(value) {
    localStorage.setItem("speech", value);
    if (!value) speechStore.stopAudio();
  },

  _applyShowThoughts(value) {
    css.toggleCssProperty(
      ".msg-thoughts",
      "display",
      value ? undefined : "none"
    );
  },

  _applyShowJson(value) {
    css.toggleCssProperty(".msg-json", "display", value ? "block" : "none");
  },

  _applyShowUtils(value) {
    css.toggleCssProperty(
      ".message-util",
      "display",
      value ? undefined : "none"
    );
  },
};

export const store = createStore("preferences", model);
