import { createStore } from "/js/AlpineStore.js";
import { toastFrontendError } from "/components/notifications/notification-store.js";
import { store as pluginListStore } from "/components/plugins/list/pluginListStore.js";
import * as API from "/js/api.js";

const STORAGE_KEY = "dismissed_discovery_cards";

const model = {
  // --- State ---
  /** @type {any[]} */
  cards: [],
  hasDismissedCards: false,
  _initialized: false,
  _isLoading: false,

  // --- Lifecycle ---
  init() {
    if (this._initialized) return;
    this._initialized = true;
  },

  // --- Actions ---

  async refreshCards() {
    if (this._isLoading) return;
    this._isLoading = true;
    
    try {
      const response = await API.callJsonApi("/banners", {
        banners: [],
        context: {
            is_onboarding: document.body.dataset.mode === "onboarding"
        },
      });
      
      const banners = response?.banners || [];
      const dismissed = this._getDismissedIds();
      
      // Filter out standard banners, keep only hero and feature
      // Also respect the onboarding filtering
      const is_onboarding = document.body.dataset.mode === "onboarding";
      
      this.cards = banners
        .filter((card) => card.type === "hero" || card.type === "feature")
        .filter((card) => !is_onboarding || card.show_in_onboarding === true)
        .filter((card) => !dismissed.has(card.id))
        .sort((left, right) => (right.priority || 0) - (left.priority || 0));
        
      this.hasDismissedCards = dismissed.size > 0;
    } catch (error) {
      console.error("Failed to fetch discovery cards:", error);
    } finally {
      this._isLoading = false;
    }
  },

  dismissCard(cardId) {
    const dismissed = this._getDismissedIds();
    dismissed.add(cardId);
    this._persistDismissedIds(dismissed);
    
    // Optimistically update UI
    this.cards = this.cards.filter(c => c.id !== cardId);
    this.hasDismissedCards = true;
  },

  undismissCards() {
    localStorage.removeItem(STORAGE_KEY);
    this.refreshCards();
  },

  async executeCta(action) {
    if (!action) return;

    try {
      if (action === "open-plugin-hub") {
        await pluginListStore.open("pluginHub");
        return;
      }

      if (action.startsWith("open-plugin-config:")) {
        const pluginName = action.split(":")[1];
        await pluginListStore.openPluginConfig(pluginName);
        return;
      }

      if (action.startsWith("open-url:")) {
        const url = action.slice("open-url:".length);
        if (url) {
          window.open(url, "_blank", "noopener,noreferrer");
        }
        return;
      }
    } catch (error) {
      console.error("Discovery action failed:", error);
      const message = error instanceof Error ? error.message : String(error);
      await toastFrontendError(message, "Discovery");
    }
  },

  // --- Helpers (Private-ish) ---

  _getDismissedIds() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      if (!Array.isArray(raw)) return new Set();
      return new Set(raw);
    } catch {
      return new Set();
    }
  },

  _persistDismissedIds(ids) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(ids)));
  },

  // --- Computed ---

  get topHeroCards() {
    return this.cards.filter((card) => card.type === "hero" && card.placement !== "after-features");
  },

  get bottomHeroCards() {
    return this.cards.filter((card) => card.type === "hero" && card.placement === "after-features");
  },

  get heroCards() {
    return [...this.topHeroCards, ...this.bottomHeroCards];
  },

  get featureCards() {
    return this.cards.filter((card) => card.type === "feature");
  },
};

const store = createStore("discoveryStore", model);
export { store };
