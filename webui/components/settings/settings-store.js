import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";
import {
  getBrowserTimezone,
  setConfiguredTimeFormat,
  setConfiguredTimezone,
} from "/js/time-utils.js";

// Constants
const VIEW_MODE_STORAGE_KEY = "settingsActiveTab";
const DEFAULT_TAB = "agent";
const UPDATE_STATUS_REFRESH_COOLDOWN_MS = 60 * 1000;
// Match the modal header/padding breathing room before promoting a section link.
const SECTION_ACTIVATION_OFFSET = 56;

const UI_CONTROLS = Object.freeze([
  { id: "projectSelector", label: "Project selector", icon: "folder_open" },
  { id: "time", label: "Time", icon: "schedule" },
  { id: "connectionStatus", label: "Connection status", icon: "wifi" },
  { id: "rightCanvasRail", label: "Right canvas rail", icon: "dock_to_right" },
]);

const TAB_ITEMS = Object.freeze([
  {
    id: "agent",
    label: "Agent Settings",
    icon: "smart_toy",
    sections: [
      { id: "section-agent-config", label: "Agent Config", icon: "settings" },
      { id: "section-models-summary", label: "Models", icon: "forum" },
      { id: "section-voice", label: "Voice", icon: "mic" },
      { id: "section-workdir", label: "Workdir", icon: "folder" },
      { id: "section-locale", label: "Locale", icon: "language" },
      { id: "section-interface", label: "Interface", icon: "dashboard_customize" },
      { id: "section-agent-plugins", label: "Plugins", icon: "extension" },
    ],
  },
  {
    id: "skills",
    label: "Skills",
    icon: "school",
    sections: [
      { id: "section-skills-list", label: "List Skills", icon: "view_list" },
      { id: "section-skills-import", label: "Import Skills", icon: "upload_file" },
      { id: "section-skills-scan", label: "Scan Skills", icon: "radar" },
    ],
  },
  {
    id: "external",
    label: "External Services",
    icon: "cloud_sync",
    sections: [
      { id: "section-api-keys", label: "API Keys", icon: "key" },
      { id: "section-litellm", label: "LiteLLM", icon: "tune" },
      { id: "section-secrets", label: "Secrets", icon: "lock" },
      { id: "section-auth", label: "Authentication", icon: "passkey" },
      { id: "section-external-api", label: "External API", icon: "api" },
      { id: "section-tunnel", label: "Remote Control", icon: "share" },
      { id: "section-external-plugins", label: "Plugins", icon: "extension" },
    ],
  },
  {
    id: "mcp",
    label: "MCP/A2A",
    icon: "hub",
    sections: [
      { id: "section-mcp-client", label: "External MCP Servers", icon: "hub" },
      { id: "section-mcp-server", label: "A0 MCP Server", icon: "settings_input_antenna" },
      { id: "section-a2a-server", label: "A0 A2A Server", icon: "conversion_path" },
    ],
  },
  {
    id: "developer",
    label: "Developer",
    icon: "code",
    sections: [
      { id: "section-dev", label: "Development", icon: "terminal" },
    ],
  },
  {
    id: "backup",
    label: "Check for updates",
    icon: "system_update_alt",
    sections: [
      { id: "section-self-update", label: "Self Update", icon: "system_update_alt" },
      { id: "section-backup-restore", label: "Backup & Restore", icon: "backup" },
    ],
  },
]);

// Field button actions (field id -> modal path)
const FIELD_BUTTON_MODAL_BY_ID = Object.freeze({
  mcp_servers_config: "settings/mcp/client/mcp-servers.html",
  backup_create: "settings/backup/backup.html",
  backup_restore: "settings/backup/restore.html",
  show_a2a_connection: "settings/a2a/a2a-connection.html",
  external_api_examples: "settings/external/api-examples.html",
});

// Helper for toasts
function toast(text, type = "info", timeout = 5000) {
  notificationStore.addFrontendToastOnly(type, text, "", timeout / 1000);
}

// Settings Store
const model = {
  // State
  isLoading: false,
  error: null,
  settings: null,
  additional: null,
  workdirFileStructureTestOutput: "",
  _activeSection: null,
  _paneScrollHandler: null,
  _paneScrollPane: null,
  _scrollSyncFrame: null,
  _updateStatusRefreshedAt: 0,
  expandedNavGroups: {},
  searchQuery: "",
  uiVisibility: null,
  
  // Tab state
  _activeTab: DEFAULT_TAB,
  get activeTab() {
    return this._activeTab;
  },
  set activeTab(value) {
    const previous = this._activeTab;
    this._activeTab = this.normalizeTabId(value);
    this.applyActiveTab(previous, this._activeTab);
  },

  get activeSection() {
    return this._activeSection || this.getFirstSectionId(this.activeTab);
  },

  // Lifecycle
  init() {
    // Restore persisted tab
    try {
      const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
      if (saved) this._activeTab = this.normalizeTabId(saved);
    } catch {}
    this._activeSection = this.getFirstSectionId(this._activeTab);
    this.expandedNavGroups = this.createDefaultExpandedNavGroups(this._activeTab);
  },

  async onOpen() {
    this.error = null;
    this.isLoading = true;
    this.uiVisibility = preferencesStore.uiVisibilitySnapshot();
    
    try {
      const response = await API.callJsonApi("settings_get", null);
      if (response && response.settings) {
        this.settings = response.settings;
        this.additional = response.additional || null;
        this.applyLocaleRuntime(this.settings);
        preferencesStore.setUiVisibility(this.settings.ui_control_visibility);
        this.uiVisibility = preferencesStore.uiVisibilitySnapshot();
      } else {
        throw new Error("Invalid settings response");
      }
    } catch (e) {
      console.error("Failed to load settings:", e);
      this.error = e.message || "Failed to load settings";
      toast("Failed to load settings", "error");
    } finally {
      this.isLoading = false;
    }

    this.refreshUpdateStatus();

    const hashSectionId = this.getHashSectionId();
    const openedHashSection = hashSectionId
      ? this.activateSection(hashSectionId, { persist: false })
      : false;

    // Trigger tab activation for current tab
    this._activeTab = this.normalizeTabId(this._activeTab);
    this.applyActiveTab(null, this._activeTab);
    this.bindPaneScroll();

    if (openedHashSection) {
      this.scrollToSection(hashSectionId);
    }
  },

  cleanup() {
    this.unbindPaneScroll();
    this.settings = null;
    this.additional = null;
    this.error = null;
    this.isLoading = false;
    this.searchQuery = "";
    this.uiVisibility = null;
  },

  get uiControls() {
    return UI_CONTROLS;
  },

  isUiControlVisible(control, device) {
    return this.uiVisibility?.[control]?.[device] !== false;
  },

  toggleUiControl(control, device) {
    this.uiVisibility = {
      ...this.uiVisibility,
      [control]: {
        ...this.uiVisibility?.[control],
        [device]: !this.isUiControlVisible(control, device),
      },
    };
  },

  uiControlVisibilityLabel(control) {
    const mobile = this.isUiControlVisible(control, "mobile");
    const desktop = this.isUiControlVisible(control, "desktop");
    if (mobile && desktop) return "Shown everywhere";
    if (mobile) return "Mobile only";
    if (desktop) return "Desktop only";
    return "Hidden everywhere";
  },

  // Tab management
  applyActiveTab(previous, current) {
    if (!this.sectionBelongsToTab(this._activeSection, current)) {
      this._activeSection = this.getFirstSectionId(current);
    }

    // Persist
    try {
      localStorage.setItem(VIEW_MODE_STORAGE_KEY, current);
    } catch {}

    this.setNavGroupExpanded(current, true);
    this.bindPaneScroll();
  },

  switchTab(tabName) {
    this.activeTab = tabName;
  },

  normalizeTabId(tabName) {
    return TAB_ITEMS.some((item) => item.id === tabName) ? tabName : DEFAULT_TAB;
  },

  get navItems() {
    return TAB_ITEMS;
  },

  get normalizedSearchQuery() {
    return String(this.searchQuery || "").trim().toLowerCase();
  },

  get hasSearchQuery() {
    return this.normalizedSearchQuery.length > 0;
  },

  get filteredNavItems() {
    const query = this.normalizedSearchQuery;
    if (!query) return TAB_ITEMS;

    return TAB_ITEMS
      .map((item) => {
        const itemMatches = this.getNavSearchText(item).includes(query);
        const sections = itemMatches
          ? item.sections
          : item.sections.filter((section) => this.getNavSearchText(section).includes(query));
        return sections.length ? { ...item, sections } : null;
      })
      .filter(Boolean);
  },

  get activeTabItem() {
    return TAB_ITEMS.find((item) => item.id === this.activeTab) || TAB_ITEMS[0];
  },

  get sectionItems() {
    return this.activeTabItem?.sections || [];
  },

  getFirstSectionId(tabName = this.activeTab) {
    const tab = TAB_ITEMS.find((item) => item.id === tabName) || TAB_ITEMS[0];
    return tab?.sections?.[0]?.id || null;
  },

  getNavSearchText(item) {
    return `${item?.label || ""} ${item?.id || ""}`.toLowerCase();
  },

  createDefaultExpandedNavGroups(activeTab = this.activeTab) {
    return TAB_ITEMS.reduce((groups, item) => {
      groups[item.id] = item.id === activeTab;
      return groups;
    }, {});
  },

  isNavGroupExpanded(tabName) {
    if (this.hasSearchQuery) return true;
    const tabId = this.normalizeTabId(tabName);
    return Boolean(this.expandedNavGroups?.[tabId]);
  },

  setNavGroupExpanded(tabName, expanded) {
    const tabId = this.normalizeTabId(tabName);
    this.expandedNavGroups = {
      ...(this.expandedNavGroups || {}),
      [tabId]: Boolean(expanded),
    };
  },

  toggleNavGroup(tabName) {
    const tabId = this.normalizeTabId(tabName);
    if (this.hasSearchQuery) {
      this.enterTab(tabId);
      return;
    }
    if (this.activeTab !== tabId) {
      this.enterTab(tabId);
      this.setNavGroupExpanded(tabId, true);
      return;
    }
    this.setNavGroupExpanded(tabId, !this.isNavGroupExpanded(tabId));
  },

  clearSearch() {
    this.searchQuery = "";
  },

  openFirstSearchResult() {
    const item = this.filteredNavItems[0];
    const section = item?.sections?.[0];
    if (section?.id) {
      this.scrollToSection(section.id);
    } else if (item?.id) {
      this.enterTab(item.id);
    }
  },

  get browserTimezone() {
    return getBrowserTimezone();
  },

  get effectiveTimezone() {
    if (!this.settings) return this.browserTimezone;
    return this.settings.timezone === "auto"
      ? this.browserTimezone
      : this.settings.timezone || this.browserTimezone;
  },

  applyTimezoneRuntime(timezone) {
    setConfiguredTimezone(timezone || "auto");
  },

  applyTimeFormatRuntime(timeFormat) {
    setConfiguredTimeFormat(timeFormat || "12h");
  },

  applyLocaleRuntime(settings) {
    this.applyTimezoneRuntime(settings?.timezone);
    this.applyTimeFormatRuntime(settings?.time_format);
  },

  getTabIdForSection(sectionId) {
    if (!sectionId) return null;
    const tab = TAB_ITEMS.find((item) =>
      item.sections?.some((section) => section.id === sectionId)
    );
    return tab?.id || null;
  },

  sectionBelongsToTab(sectionId, tabName = this.activeTab) {
    if (!sectionId) return false;
    return this.getTabIdForSection(sectionId) === tabName;
  },

  getHashSectionId() {
    const rawHash = window.location.hash || "";
    if (!rawHash.startsWith("#section-")) return null;
    try {
      return decodeURIComponent(rawHash.slice(1));
    } catch {
      return rawHash.slice(1);
    }
  },

  activateSection(sectionId, { persist = true } = {}) {
    const tabId = this.getTabIdForSection(sectionId);
    if (!tabId) return false;

    const previous = this._activeTab;
    this._activeTab = tabId;
    this._activeSection = sectionId;
    if (persist) {
      this.applyActiveTab(previous, tabId);
    }
    if (tabId === "backup") this.refreshUpdateStatus();
    return true;
  },

  enterTab(tabName) {
    this.activeTab = tabName;
    this._activeSection = this.getFirstSectionId(this.activeTab);
    this.setNavGroupExpanded(this.activeTab, true);
    this.resetPaneScroll();
    if (tabName === "backup") this.refreshUpdateStatus();
  },

  resetPaneScroll() {
    requestAnimationFrame(() => {
      const pane = this.getSettingsPane();
      if (pane) {
        pane.scrollTop = 0;
        this.updateActiveSectionFromScroll();
      }
    });
  },

  getSettingsPane() {
    return document.querySelector(".modal-inner.settings-modal .settings-pane");
  },

  bindPaneScroll() {
    requestAnimationFrame(() => {
      const pane = this.getSettingsPane();
      if (!pane || this._paneScrollPane === pane) {
        if (pane) this.updateActiveSectionFromScroll();
        return;
      }

      this.unbindPaneScroll();
      this._paneScrollPane = pane;
      this._paneScrollHandler = () => this.updateActiveSectionFromScroll();
      pane.addEventListener("scroll", this._paneScrollHandler, { passive: true });
      this.updateActiveSectionFromScroll();
    });
  },

  unbindPaneScroll() {
    if (this._paneScrollPane && this._paneScrollHandler) {
      this._paneScrollPane.removeEventListener("scroll", this._paneScrollHandler);
    }
    if (this._scrollSyncFrame) {
      cancelAnimationFrame(this._scrollSyncFrame);
    }
    this._paneScrollPane = null;
    this._paneScrollHandler = null;
    this._scrollSyncFrame = null;
  },

  updateActiveSectionFromScroll() {
    if (this._scrollSyncFrame) return;
    this._scrollSyncFrame = requestAnimationFrame(() => {
      this._scrollSyncFrame = null;
      const pane = this.getSettingsPane();
      if (!pane) return;

      const paneRect = pane.getBoundingClientRect();
      const activationTop = paneRect.top + SECTION_ACTIVATION_OFFSET;
      let activeId = this.getFirstSectionId(this.activeTab);

      for (const section of this.sectionItems) {
        const target = this.getSectionTarget(section.id, pane);
        if (!target || target.offsetParent === null) continue;
        if (target.getBoundingClientRect().top <= activationTop) {
          activeId = section.id;
        }
      }

      this._activeSection = activeId;
    });
  },

  get selfUpdate() {
    return globalThis.Alpine?.store?.("selfUpdateStore") || null;
  },

  getSectionTarget(sectionId, pane = this.getSettingsPane()) {
    if (!sectionId) return null;
    const escapedId = window.CSS?.escape ? window.CSS.escape(sectionId) : sectionId;
    const selector = `#${escapedId}`;
    const activePanel = pane?.querySelector(`.settings-tab-panel[data-settings-tab="${this.activeTab}"]`);
    return activePanel?.querySelector(selector) || pane?.querySelector(selector) || document.getElementById(sectionId);
  },

  scrollToSection(sectionId, event = null) {
    event?.preventDefault?.();
    if (!this.activateSection(sectionId)) {
      this._activeSection = sectionId;
    }

    const performScroll = () => {
      const pane = this.getSettingsPane();
      const target = this.getSectionTarget(sectionId, pane);
      if (!target) {
        history.replaceState(null, "", `#${sectionId}`);
        return;
      }
      if (!pane) {
        target.scrollIntoView({ behavior: "smooth", block: "start", inline: "nearest" });
        history.replaceState(null, "", `#${sectionId}`);
        return;
      }
      const paneRect = pane.getBoundingClientRect();
      const targetRect = target.getBoundingClientRect();
      pane.scrollTo({
        top: Math.max(0, pane.scrollTop + targetRect.top - paneRect.top - 12),
        behavior: "smooth",
      });
      history.replaceState(null, "", `#${sectionId}`);
      this.updateActiveSectionFromScroll();
    };

    requestAnimationFrame(() => requestAnimationFrame(performScroll));
  },

  refreshUpdateStatus(force = false) {
    const selfUpdate = this.selfUpdate;
    if (typeof selfUpdate?.refresh !== "function") return;
    const now = Date.now();
    if (!force && now - this._updateStatusRefreshedAt < UPDATE_STATUS_REFRESH_COOLDOWN_MS) {
      return;
    }
    this._updateStatusRefreshedAt = now;
    selfUpdate.refresh().catch((error) => {
      console.warn("Failed to refresh self-update status:", error);
    });
  },

  isUpdateNotification(notification) {
    if (!notification) return false;
    const group = String(notification.group || "").toLowerCase();
    const id = String(notification.id || "").toLowerCase();
    return (
      group === "update_check" ||
      group.startsWith("self-update") ||
      id.startsWith("update_check") ||
      id.includes("self-update")
    );
  },

  get latestUpdateNotification() {
    return notificationStore.notifications.find((item) => this.isUpdateNotification(item)) || null;
  },

  get hasUpdateNotification() {
    return Boolean(this.latestUpdateNotification);
  },

  get hasUpdateAttention() {
    const selfUpdate = this.selfUpdate;
    return Boolean(
      selfUpdate?.info?.pending ||
      selfUpdate?.quickUpdateAvailable ||
      selfUpdate?.hasMajorUpgrade ||
      this.hasUpdateNotification
    );
  },

  get updateAttentionLabel() {
    const selfUpdate = this.selfUpdate;
    if (selfUpdate?.info?.pending) return "Scheduled";
    if (selfUpdate?.quickUpdateAvailable) return "Update available";
    if (selfUpdate?.hasMajorUpgrade) return "New release line";
    if (this.hasUpdateNotification) return "Update notice";
    return selfUpdate?.quickStatusLabel || "Ready";
  },

  get updateAttentionTitle() {
    const selfUpdate = this.selfUpdate;
    if (selfUpdate?.info?.pending) return "Update scheduled";
    if (selfUpdate?.quickUpdateAvailable) return "Update available";
    if (selfUpdate?.hasMajorUpgrade) return "New release line available";
    if (this.hasUpdateNotification) return "Update notice";
    return "Self Update";
  },

  get updateAttentionMessage() {
    const notification = this.latestUpdateNotification;
    if (notification?.message) {
      return this.toPlainText(notification.message);
    }
    const selfUpdate = this.selfUpdate;
    if (selfUpdate?.info?.pending) {
      return "Agent Zero has a self-update request ready for the next restart.";
    }
    return selfUpdate?.quickStatusMessage || "Review versions, backups, and update readiness in one place.";
  },

  navItemHasAttention(item) {
    return item?.id === "backup" && this.hasUpdateAttention;
  },

  sectionItemHasAttention(item) {
    return item?.id === "section-self-update" && this.hasUpdateAttention;
  },

  toPlainText(value) {
    const container = document.createElement("div");
    container.innerHTML = String(value || "");
    return (container.textContent || container.innerText || "").trim();
  },



  get apiKeyProviders() {
    const seen = new Set();
    const options = [];
    const addProvider = (prov) => {
      if (!prov?.value) return;
      const key = prov.value.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      options.push({ value: prov.value, label: prov.label || prov.value });
    };
    (this.additional?.chat_providers || []).forEach(addProvider);
    (this.additional?.embedding_providers || []).forEach(addProvider);
    options.sort((a, b) => a.label.localeCompare(b.label));
    return options;
  },

  // Save settings
  async saveSettings() {
    if (!this.settings) {
      toast("No settings to save", "warning");
      return false;
    }

    this.settings.ui_control_visibility = this.uiVisibility;
    this.isLoading = true;
    try {
      const response = await API.callJsonApi("settings_set", {
        settings: this.settings,
        browser_timezone: this.browserTimezone,
      });
      if (response && response.settings) {
        this.settings = response.settings;
        this.additional = response.additional || this.additional;
        this.applyLocaleRuntime(this.settings);
        preferencesStore.setUiVisibility(response.settings.ui_control_visibility);
        toast("Settings saved successfully", "success");
        document.dispatchEvent(
          new CustomEvent("settings-updated", { detail: response.settings })
        );
        return true;
      } else {
        throw new Error("Failed to save settings");
      }
    } catch (e) {
      console.error("Failed to save settings:", e);
      toast("Failed to save settings: " + e.message, "error");
      return false;
    } finally {
      this.isLoading = false;
    }
  },

  // Close the modal
  closeSettings() {
    window.closeModal("settings/settings.html");
  },

  // Save and close
  async saveAndClose() {
    const success = await this.saveSettings();
    if (success) {
      this.closeSettings();
    }
  },

  async testWorkdirFileStructure() {
    if (!this.settings) return;
    try {
      const response = await API.callJsonApi("settings_workdir_file_structure", {
        workdir_path: this.settings.workdir_path,
        workdir_max_depth: this.settings.workdir_max_depth,
        workdir_max_files: this.settings.workdir_max_files,
        workdir_max_folders: this.settings.workdir_max_folders,
        workdir_max_lines: this.settings.workdir_max_lines,
        workdir_gitignore: this.settings.workdir_gitignore,
      });
      this.workdirFileStructureTestOutput = response?.data || "";
      window.openModal("settings/agent/workdir-file-structure-test.html");
    } catch (e) {
      console.error("Error testing workdir file structure:", e);
      toast("Error testing workdir file structure", "error");
    }
  },

  // Field helpers for external components
  // Handle button field clicks (opens sub-modals)
  async handleFieldButton(field) {
    const modalPath = FIELD_BUTTON_MODAL_BY_ID[field?.id];
    if (modalPath) window.openModal(modalPath);
  },

  // Open settings modal from external callers
  async open(initialTab = null) {
    if (initialTab) {
      this._activeTab = initialTab;
    }
    await window.openModal("settings/settings.html");
  },
};

const store = createStore("settings", model);

export { store };
