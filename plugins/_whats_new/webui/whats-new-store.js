import { createStore } from "/js/AlpineStore.js";
import { closeModal } from "/js/modals.js";
import { slides } from "/plugins/_whats_new/webui/whats-new-slides.js";

const NEVER_SHOW_STORAGE_KEY = "a0_whats_new_never_show";

const emptySlide = {
  eyebrow: "What's New",
  title: "No new updates right now",
  summary: "New highlights will appear here when there are fresh Agent Zero updates.",
  mediaType: "none",
  media: "",
  mediaLabel: "No new updates right now.",
  bullets: [],
};

function storageValue(key) {
  try {
    return globalThis.localStorage?.getItem(key) || "";
  } catch {
    return "";
  }
}

function isNeverShowEnabled() {
  const value = storageValue(NEVER_SHOW_STORAGE_KEY);
  if (!value) return false;

  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed === "object") return parsed.enabled !== false;
    return Boolean(parsed);
  } catch {
    return !["0", "false", "no", "off"].includes(value.trim().toLowerCase());
  }
}

function persistNeverShowPreference(enabled) {
  try {
    if (enabled) {
      globalThis.localStorage?.setItem(
        NEVER_SHOW_STORAGE_KEY,
        JSON.stringify({
          enabled: true,
          updatedAt: new Date().toISOString(),
        }),
      );
    } else {
      globalThis.localStorage?.removeItem(NEVER_SHOW_STORAGE_KEY);
    }
  } catch {
    // localStorage may be unavailable in private or locked-down browser modes.
  }
}

export const store = createStore("whatsNew", {
  slides,
  currentIndex: 0,
  neverShowAgain: false,

  onOpen() {
    this.currentIndex = 0;
    this.neverShowAgain = isNeverShowEnabled();
  },

  cleanup() {
    persistNeverShowPreference(this.neverShowAgain);
  },

  get currentSlide() {
    return this.slides[this.currentIndex] || emptySlide;
  },

  hasSlides() {
    return this.slides.length > 0;
  },

  isFirst() {
    return this.currentIndex <= 0;
  },

  isLast() {
    return this.currentIndex >= this.slides.length - 1;
  },

  progressLabel() {
    if (!this.hasSlides()) return "";
    return `${this.currentIndex + 1} of ${this.slides.length}`;
  },

  dotLabel(index) {
    const slide = this.slides[index];
    return slide ? `Show ${slide.title}` : `Show item ${index + 1}`;
  },

  goTo(index) {
    const nextIndex = Number(index);
    if (!Number.isInteger(nextIndex)) return;
    if (nextIndex < 0 || nextIndex >= this.slides.length) return;
    this.currentIndex = nextIndex;
  },

  previous() {
    if (!this.isFirst()) this.currentIndex -= 1;
  },

  setNeverShowAgain(value) {
    this.neverShowAgain = Boolean(value);
    persistNeverShowPreference(this.neverShowAgain);
  },

  next() {
    if (this.isLast()) {
      this.finish();
      return;
    }
    this.currentIndex += 1;
  },

  finish() {
    closeModal();
  },

  skip() {
    closeModal();
  },
});
