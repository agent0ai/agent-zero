import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";
import * as shortcuts from "/js/shortcuts.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";

const model = {
  // Guards
  _initialized: false,
  _settingsLoaded: false,
  _settingsLoadPromise: null,

  // Settings (defaults match backend defaults)
  alert_enabled: true,
  alert_on_task_complete: true,
  alert_on_user_input_needed: true,
  alert_on_subagent_complete: true,
  alert_sound_type: "chime", // chime | beep | custom
  alert_custom_sound_path: "",
  alert_tts_enabled: true,
  alert_tts_use_kokoro: false,
  alert_tts_message_task_complete: "Task completed",
  alert_tts_message_input_needed: "Waiting for your input",
  alert_tts_message_subagent_complete: "Subordinate agent completed",

  // Audio state
  userHasInteracted: false,
  audioContext: null,
  audioEl: null,

  init() {
    if (this._initialized) return;
    this._initialized = true;

    this.setupUserInteractionHandling();
    // Fire-and-forget settings load; handleAlertNotification will await if needed
    this.loadSettings().catch((e) =>
      console.error("[AlertStore] Failed to load settings:", e)
    );
  },

  async loadSettings() {
    try {
      const response = await fetchApi("/settings_get", { method: "POST" });
      const data = await response.json();
      const alertsSection = data?.settings?.sections?.find(
        (s) => s?.id === "alerts" || s?.title === "Alerts"
      );

      if (alertsSection?.fields?.length) {
        alertsSection.fields.forEach((field) => {
          if (Object.prototype.hasOwnProperty.call(this, field.id)) {
            this[field.id] = field.value;
          }
        });
      }

      this._settingsLoaded = true;
    } catch (error) {
      // Keep defaults; do not throw to avoid breaking notification flow
      this._settingsLoaded = true;
      console.error("[AlertStore] Failed to load alert settings:", error);
    }
  },

  setupUserInteractionHandling() {
    const enableAudio = () => {
      if (this.userHasInteracted) return;
      this.userHasInteracted = true;

      // Try to create/resume AudioContext (may still be blocked until gesture)
      try {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (Ctx && !this.audioContext) this.audioContext = new Ctx();
        if (this.audioContext?.resume) this.audioContext.resume();
      } catch (_e) {
        // ignore
      }
    };

    const events = ["click", "touchstart", "keydown", "mousedown"];
    events.forEach((event) => {
      document.addEventListener(event, enableAudio, { once: true, passive: true });
    });
  },

  // Called by notificationStore.updateFromPoll (must not throw or return unhandled promise)
  handleAlertNotification(notification) {
    void this._handleAlertNotification(notification).catch((e) =>
      console.error("[AlertStore] Alert handling failed:", e)
    );
  },

  async _handleAlertNotification(notification) {
    if (!notification) return;
    const group = String(notification.group || "");
    if (!group.startsWith("alert.")) return;

    if (!this._initialized) this.init();
    await this._ensureSettingsLoaded();

    if (!this.alert_enabled) return;

    const kind = group.slice("alert.".length); // task_complete | input_needed | subagent_complete
    if (kind === "task_complete" && !this.alert_on_task_complete) return;
    if (kind === "input_needed" && !this.alert_on_user_input_needed) return;
    if (kind === "subagent_complete" && !this.alert_on_subagent_complete) return;

    // Play sound first
    await this._playAlertSound();

    // Optional speech (uses Speech store settings: browser TTS vs Kokoro)
    if (this.alert_tts_enabled) {
      const msg = String(notification.message || "").trim();
      if (msg) {
        try {
          // Speech store is not globally auto-initialized; init it on demand.
          if (typeof speechStore.init === "function") {
            await speechStore.init();
          }
          if (
            this.alert_tts_use_kokoro &&
            typeof speechStore.speakWithKokoro === "function"
          ) {
            try {
              await speechStore.speakWithKokoro(msg, false);
            } catch (e) {
              // Fallback to default speech path if Kokoro fails
              if (typeof speechStore.speak === "function") {
                await speechStore.speak(msg);
              }
            }
          } else if (typeof speechStore.speak === "function") {
            await speechStore.speak(msg);
          }
        } catch (e) {
          console.error("[AlertStore] Failed to speak alert message:", e);
        }
      }
    }
  },

  async _ensureSettingsLoaded() {
    if (this._settingsLoaded) return;
    if (this._settingsLoadPromise) return await this._settingsLoadPromise;
    this._settingsLoadPromise = this.loadSettings();
    return await this._settingsLoadPromise;
  },

  async _getAudioContext() {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return null;
    if (!this.audioContext) this.audioContext = new Ctx();
    try {
      if (this.audioContext.state === "suspended" && this.audioContext.resume) {
        await this.audioContext.resume();
      }
    } catch (_e) {
      // ignore
    }
    return this.audioContext;
  },

  async _playAlertSound() {
    const soundType = String(this.alert_sound_type || "chime");

    // Try to play even if we haven't observed a user interaction yet; if blocked, prompt.
    try {
      if (soundType === "custom") {
        const url = String(this.alert_custom_sound_path || "").trim();
        if (url) return await this._playAudioUrl(url);
        // fall back to chime if custom missing
        return await this._playChime();
      }

      if (soundType === "beep") return await this._playBeep();
      return await this._playChime();
    } catch (e) {
      if (e?.name === "NotAllowedError") {
        this._showAudioPermissionPrompt();
        this.userHasInteracted = false;
        return;
      }
      console.error("[AlertStore] Sound playback failed:", e);
    }
  },

  _showAudioPermissionPrompt() {
    shortcuts.frontendNotification({
      type: "info",
      title: "Enable audio alerts",
      message: "Click anywhere on the page to enable audio playback for alerts.",
      displayTime: 6,
      group: "audio-alerts-permission",
      priority: shortcuts.NotificationPriority.NORMAL,
      frontendOnly: true,
    });
  },

  async _playBeep() {
    return await this._playToneSequence([{ freq: 880, dur: 0.12 }]);
  },

  async _playChime() {
    return await this._playToneSequence([
      { freq: 880, dur: 0.09 },
      { freq: 660, dur: 0.13 },
    ]);
  },

  async _playToneSequence(sequence) {
    const ctx = await this._getAudioContext();
    if (!ctx) return;

    // If we haven't unlocked audio yet, prompt (but still attempt to play).
    if (!this.userHasInteracted) {
      this._showAudioPermissionPrompt();
    }

    const startAt = ctx.currentTime + 0.02;
    let t = startAt;

    for (const tone of sequence) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(tone.freq, t);

      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.exponentialRampToValueAtTime(0.12, t + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + tone.dur);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(t);
      osc.stop(t + tone.dur + 0.01);

      t += tone.dur + 0.04;
    }

    const totalMs = Math.max(0, Math.round((t - startAt) * 1000));
    await new Promise((resolve) => setTimeout(resolve, totalMs));
  },

  async _playAudioUrl(url) {
    return await new Promise((resolve, reject) => {
      const audio = this.audioEl ? this.audioEl : (this.audioEl = new Audio());

      audio.pause();
      audio.currentTime = 0;

      audio.onended = () => resolve();
      audio.onerror = (e) => reject(e);

      audio.src = url;
      audio.play().catch((error) => reject(error));
    });
  },
};

export const store = createStore("alertStore", model);

// Reload on Settings save
document.addEventListener("settings-updated", () => store.loadSettings());

// Ensure initialization after Alpine mounts (Agent Zero lifecycle convention)
document.addEventListener("alpine:init", () => {
  const s = Alpine.store("alertStore");
  if (s && typeof s.init === "function") s.init();
});


