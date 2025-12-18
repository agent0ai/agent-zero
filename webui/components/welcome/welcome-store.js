import { createStore } from "/js/AlpineStore.js";
import { getContext } from "/index.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as memoryStore } from "/components/settings/memory/memory-dashboard-store.js";
import { store as projectsStore } from "/components/projects/projects-store.js";
import * as bannerChecks from "/js/banner-checks.js";
import * as API from "/js/api.js";

const model = {
  // State
  isVisible: true,
  banners: [],
  bannersLoading: false,
  lastBannerRefresh: 0,
  cachedSettings: null,

  init() {
    // Initialize visibility based on current context
    this.updateVisibility();
    
    // Initial banner refresh if visible
    if (this.isVisible) {
      this.refreshBanners();
    }

    // Watch for context changes with faster polling for immediate response
    setInterval(() => {
      this.updateVisibility();
    }, 50); // 50ms for very responsive updates
  },

  // Update visibility based on current context
  updateVisibility() {
    const hasContext = !!getContext();
    const wasVisible = this.isVisible;
    this.isVisible = !hasContext;
    
    // Refresh banners when welcome screen becomes visible
    if (this.isVisible && !wasVisible) {
      this.refreshBanners();
    }
  },

  // Hide welcome screen
  hide() {
    this.isVisible = false;
  },

  // Show welcome screen
  show() {
    this.isVisible = true;
    this.refreshBanners();
  },

  /** Refresh frontend + backend banners */
  async refreshBanners() {
    const now = Date.now();
    if (now - this.lastBannerRefresh < 1000) {
      return;
    }
    this.lastBannerRefresh = now;
    
    this.bannersLoading = true;
    
    try {
      await this.fetchSettings();
      
      const frontendContext = bannerChecks.buildFrontendContext(this.cachedSettings);
      const frontendBanners = this.runFrontendBannerChecks(frontendContext);
      
      const backendBanners = await this.runBackendBannerChecks(frontendBanners, frontendContext);
      
      this.banners = this.mergeBanners(frontendBanners, backendBanners);
      
    } catch (error) {
      console.error("Failed to refresh banners:", error);
      // On error, still show frontend banners if available
      try {
        const frontendContext = bannerChecks.buildFrontendContext(this.cachedSettings);
        this.banners = this.runFrontendBannerChecks(frontendContext);
      } catch (e) {
        this.banners = [];
      }
    } finally {
      this.bannersLoading = false;
    }
  },

  /** Fetch backend settings for banner checks */
  async fetchSettings() {
    try {
      const response = await API.callJsonApi("/settings_get", null);
      if (response && response.settings) {
        this.cachedSettings = this.extractSettingsForBanners(response.settings);
      }
    } catch (error) {
      console.error("Failed to fetch settings for banners:", error);
    }
  },

  /** Extract relevant settings from the full settings response */
  extractSettingsForBanners(settingsOutput) {
    const result = {
      chat_model_provider: '',
      api_keys: {},
      auth_login: '',
      auth_password: '',
    };
    
    if (!settingsOutput || !settingsOutput.sections) {
      return result;
    }
    
    for (const section of settingsOutput.sections) {
      for (const field of section.fields || []) {
        if (field.id === 'chat_model_provider') {
          result.chat_model_provider = field.value || '';
        } else if (field.id === 'auth_login') {
          result.auth_login = field.value || '';
        } else if (field.id === 'auth_password') {
          result.auth_password = field.value || '';
        } else if (field.id && field.id.startsWith('api_key_')) {
          // Extract API keys (e.g., api_key_openai -> openai)
          const provider = field.id.replace('api_key_', '');
          result.api_keys[provider] = field.value || '';
        }
      }
    }
    
    return result;
  },

  /** Run all frontend banner checks */
  runFrontendBannerChecks(context) {
    return bannerChecks.runAllChecks(context);
  },

  /** Run backend banner checks via API */
  async runBackendBannerChecks(frontendBanners, context) {
    try {
      const response = await API.callJsonApi("/banners", {
        banners: frontendBanners,
        context: context
      });
      
      return response?.banners || [];
    } catch (error) {
      console.error("Failed to fetch backend banners:", error);
      return [];
    }
  },

  /** Merge & deduplicate banners by ID (backend overrides frontend) */
  mergeBanners(frontendBanners, backendBanners) {
    const bannerMap = new Map();
    
    for (const banner of frontendBanners) {
      if (banner.id) {
        bannerMap.set(banner.id, banner);
      }
    }
    
    for (const banner of backendBanners) {
      if (banner.id) {
        bannerMap.set(banner.id, banner);
      }
    }
    
    const merged = Array.from(bannerMap.values());
    merged.sort((a, b) => (b.priority || 0) - (a.priority || 0));
    
    return merged;
  },

  get sortedBanners() {
    return [...this.banners].sort((a, b) => (b.priority || 0) - (a.priority || 0));
  },

  /** Dismiss banner */
  dismissBanner(bannerId, permanent = false) {
    // Remove from current banners
    this.banners = this.banners.filter(b => b.id !== bannerId);
    
    // Store dismissed state (for future implementation)
    // const storage = permanent ? localStorage : sessionStorage;
    // const dismissedKey = 'dismissed_banners';
    // const dismissed = JSON.parse(storage.getItem(dismissedKey) || '[]');
    // if (!dismissed.includes(bannerId)) {
    //   dismissed.push(bannerId);
    //   storage.setItem(dismissedKey, JSON.stringify(dismissed));
    // }
  },

  /** Handle banner actions */
  handleBannerAction(action, data = {}) {
    switch (action) {
      case 'open-settings':
        const settingsButton = document.getElementById("settings");
        if (settingsButton) {
          settingsButton.click();
        }
        break;
      case 'dismiss':
        if (data.bannerId) {
          this.dismissBanner(data.bannerId, data.permanent);
        }
        break;
      default:
        console.warn(`Unknown banner action: ${action}`);
    }
  },

  getBannerClass(type) {
    const classes = {
      info: 'banner-info',
      warning: 'banner-warning',
      error: 'banner-error',
    };
    return classes[type] || 'banner-info';
  },

  getBannerIcon(type) {
    const icons = {
      info: 'info',
      warning: 'warning',
      error: 'error',
    };
    return icons[type] || 'info';
  },

  // Execute an action by ID
  executeAction(actionId) {
    switch (actionId) {
      case "new-chat":
        chatsStore.newChat();
        break;
      case "settings":
        // Open settings modal
        const settingsButton = document.getElementById("settings");
        if (settingsButton) {
          settingsButton.click();
        }
        break;
      case "projects":
        projectsStore.openProjectsModal();
        break;
      case "memory":
        memoryStore.openModal();
        break;
      case "website":
        window.open("https://agent-zero.ai", "_blank");
        break;
      case "github":
        window.open("https://github.com/agent0ai/agent-zero", "_blank");
        break;
    }
  },
};

// Create and export the store
const store = createStore("welcomeStore", model);
export { store };
