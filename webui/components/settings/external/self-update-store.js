import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";
import { openModal, closeModal } from "/js/modals.js";

const HEALTH_POLL_INTERVAL_MS = 2000;
const HEALTH_WAIT_BUFFER_MS = 30000;
const SELF_UPDATE_RETURN_URL_KEY = "a0:self-update:return-url";
const SELF_UPDATE_OVERLAY_ID = "self-update-progress-overlay";
const SELF_UPDATE_MODAL_PATH = "settings/external/self-update-modal.html";
const MIN_SELECTOR_VERSION = [1, 0];

const model = {
  loading: false,
  saving: false,
  restarting: false,
  tagsLoading: false,
  error: "",
  tagsError: "",
  info: null,
  tagSuggestions: [],
  tagDropdownOpen: false,
  tagExistenceChecked: false,
  restartStatusText: "",
  restartDetailText: "",
  form: {
    branch: "main",
    tag: "",
    backup_usr: true,
    backup_path: "",
    backup_name: "",
    backup_conflict_policy: "rename",
  },
  _reconnectTimer: null,
  _tagRequestId: 0,

  get isBusy() {
    return this.loading || this.saving || this.restarting;
  },

  get isSupported() {
    return Boolean(this.info?.supported);
  },

  get currentVersion() {
    return this.info?.current?.short_tag || "unknown";
  },

  get currentBranch() {
    return this.info?.current?.branch || "";
  },

  get groupedTagSuggestions() {
    const tags = Array.isArray(this.tagSuggestions) ? this.tagSuggestions : [];
    const query = (this.form.tag || "").trim().toLowerCase();
    if (!query) {
      return { matched: [], rest: tags };
    }

    const matched = [];
    const rest = [];
    for (const tag of tags) {
      if ((tag || "").toLowerCase().includes(query)) {
        matched.push(tag);
      } else {
        rest.push(tag);
      }
    }
    return { matched, rest };
  },

  get trimmedTag() {
    return (this.form.tag || "").trim();
  },

  get selectedTagExistsOnBranch() {
    const tag = this.trimmedTag;
    return Boolean(tag) && this.tagSuggestions.includes(tag);
  },

  get versionCompatibilityWarning() {
    const current = this.parseCompatibilityTag(this.currentVersion);
    const target = this.parseCompatibilityTag(this.form.tag);
    if (!current || !target) return "";
    if (current.major !== target.major) {
      return (
        "Changing the first version number requires downloading a new Docker image, " +
        "because those releases can include operating system level changes or other breaking changes."
      );
    }
    return "";
  },

  get tagExistenceWarning() {
    const tag = this.trimmedTag;
    if (
      !this.tagExistenceChecked ||
      this.tagsLoading ||
      this.tagsError ||
      !tag ||
      !this.parseSelectorTag(tag) ||
      !this.isSupportedSelectorTag(tag)
    ) {
      return "";
    }
    if (!this.selectedTagExistsOnBranch) {
      return `Version ${tag} does not exist on branch ${this.form.branch || "main"}.`;
    }
    return "";
  },

  get canScheduleUpdate() {
    return (
      this.isSupported &&
      !this.isBusy &&
      !this.tagsLoading &&
      this.isSupportedSelectorTag(this.form.tag) &&
      this.selectedTagExistsOnBranch &&
      !this.versionCompatibilityWarning
    );
  },

  async init() {
    await this.refresh();
  },

  cleanup() {
    this.clearReconnectTimer();
    this.error = "";
    this.tagsError = "";
    this.loading = false;
    this.saving = false;
    this.restarting = false;
    this.tagsLoading = false;
    this.tagDropdownOpen = false;
    this.tagExistenceChecked = false;
    this.restartStatusText = "";
    this.restartDetailText = "";
    this.removeProgressOverlay();
  },

  clearReconnectTimer() {
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }
  },

  formatTimestamp(value) {
    if (!value) return "";
    try {
      return new Date(value).toLocaleString();
    } catch {
      return value;
    }
  },

  formatBranchTag(branch, tag) {
    return `${branch || "main"} / ${tag || "None"}`;
  },

  getSavedReturnUrl() {
    try {
      return sessionStorage.getItem(SELF_UPDATE_RETURN_URL_KEY) || "";
    } catch {
      return "";
    }
  },

  saveReturnUrl(url = "") {
    try {
      if (url) {
        sessionStorage.setItem(SELF_UPDATE_RETURN_URL_KEY, url);
      } else {
        sessionStorage.removeItem(SELF_UPDATE_RETURN_URL_KEY);
      }
    } catch {
      // ignore storage errors
    }
  },

  getProgressOverlay() {
    return document.getElementById(SELF_UPDATE_OVERLAY_ID);
  },

  ensureProgressOverlay() {
    let overlay = this.getProgressOverlay();
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = SELF_UPDATE_OVERLAY_ID;
      overlay.innerHTML = `
        <div class="self-update-progress-card">
          <div class="self-update-progress-spinner"></div>
          <div class="self-update-progress-title"></div>
          <div class="self-update-progress-detail"></div>
        </div>
      `;
      Object.assign(overlay.style, {
        position: "fixed",
        inset: "0",
        zIndex: "10000",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
        background:
          "color-mix(in srgb, var(--color-background) 74%, transparent)",
        backdropFilter: "blur(6px)",
      });
      document.body.appendChild(overlay);

      const style = document.createElement("style");
      style.id = `${SELF_UPDATE_OVERLAY_ID}-styles`;
      style.textContent = `
        #${SELF_UPDATE_OVERLAY_ID} .self-update-progress-card {
          width: min(28rem, calc(100vw - 2rem));
          border-radius: 1rem;
          border: 1px solid var(--color-border);
          background: color-mix(
            in srgb,
            var(--color-panel) 92%,
            var(--color-background)
          );
          color: var(--color-text);
          box-shadow: 0 24px 64px color-mix(
            in srgb,
            var(--color-background) 65%,
            transparent
          );
          padding: 1.5rem;
          text-align: center;
          font-family: var(--font-family-main);
        }
        #${SELF_UPDATE_OVERLAY_ID} .self-update-progress-spinner {
          width: 2.5rem;
          height: 2.5rem;
          margin: 0 auto 1rem;
          border-radius: 999px;
          border: 3px solid color-mix(
            in srgb,
            var(--color-border) 55%,
            transparent
          );
          border-top-color: var(--color-primary);
          animation: self-update-spin 1s linear infinite;
        }
        #${SELF_UPDATE_OVERLAY_ID} .self-update-progress-title {
          font-size: 1.05rem;
          font-weight: 700;
          margin-bottom: 0.5rem;
        }
        #${SELF_UPDATE_OVERLAY_ID} .self-update-progress-detail {
          color: var(--color-text-muted);
          line-height: 1.5;
        }
        @keyframes self-update-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `;
      document.head.appendChild(style);
    }
    this.updateProgressOverlay();
  },

  updateProgressOverlay() {
    const overlay = this.getProgressOverlay();
    if (!overlay) return;
    const title = overlay.querySelector(".self-update-progress-title");
    const detail = overlay.querySelector(".self-update-progress-detail");
    if (title) {
      title.textContent = this.restartStatusText || "Applying self-update";
    }
    if (detail) {
      detail.textContent =
        this.restartDetailText ||
        "Agent Zero is restarting, applying the requested release, and will reload this page when the health check responds again.";
    }
  },

  removeProgressOverlay() {
    this.getProgressOverlay()?.remove();
    document.getElementById(`${SELF_UPDATE_OVERLAY_ID}-styles`)?.remove();
  },

  setRestartState(statusText, detailText = "") {
    this.restartStatusText = statusText;
    this.restartDetailText = detailText;
    if (this.restarting) {
      this.ensureProgressOverlay();
    }
  },

  async refresh() {
    this.loading = true;
    this.error = "";
    try {
      const response = await API.callJsonApi("self_update_get", {});
      if (!response?.success) {
        throw new Error(response?.error || "Failed to load self-update info.");
      }
      this.info = response;
      this.applyFormState(response.pending || response.defaults || {});
      this.tagExistenceChecked = Boolean((this.form.tag || "").trim());
      await this.searchTags({ openResults: false });
    } catch (error) {
      console.error("Failed to load self-update info:", error);
      this.error = error.message || "Failed to load self-update info.";
    } finally {
      this.loading = false;
    }
  },

  applyFormState(source) {
    this.form.branch =
      this.info?.defaults?.branch ||
      this.currentBranch ||
      source?.branch ||
      "main";
    this.form.tag =
      typeof source?.tag === "string" ? source.tag : this.currentVersion;
    this.form.backup_usr =
      typeof source?.backup_usr === "boolean" ? source.backup_usr : true;
    this.form.backup_path = source?.backup_path || "";
    this.form.backup_name = source?.backup_name || "";
    this.form.backup_conflict_policy =
      source?.backup_conflict_policy || "rename";
  },

  closeTagDropdown() {
    this.tagDropdownOpen = false;
  },

  async openModal() {
    await openModal(SELF_UPDATE_MODAL_PATH);
  },

  openTagDropdown() {
    this.tagDropdownOpen = true;
  },

  async onBranchChanged() {
    this.openTagDropdown();
    this.tagExistenceChecked = Boolean(this.trimmedTag);
    await this.searchTags();
  },

  onTagInput() {
    this.tagExistenceChecked = false;
    this.openTagDropdown();
  },

  async onTagBlur() {
    this.tagExistenceChecked = Boolean(this.trimmedTag);
    await this.searchTags({ openResults: false });
  },

  async searchTags({ openResults = true } = {}) {
    const requestId = ++this._tagRequestId;
    this.tagsLoading = true;
    this.tagsError = "";

    try {
      const response = await API.callJsonApi("self_update_tags", {
        branch: this.form.branch,
        query: "",
      });
      if (!response?.success) {
        throw new Error(response?.error || "Failed to fetch release tags.");
      }
      if (requestId !== this._tagRequestId) {
        return;
      }
      this.tagSuggestions = Array.isArray(response?.tags)
        ? response.tags.filter((tag) => this.isSupportedSuggestionTag(tag))
        : [];
      this.tagsError = response?.error || "";
      this.tagDropdownOpen = openResults;
    } catch (error) {
      console.error("Failed to fetch self-update tags:", error);
      if (requestId !== this._tagRequestId) {
        return;
      }
      this.tagSuggestions = [];
      this.tagsError = error.message || "Failed to fetch release tags.";
      this.tagDropdownOpen = openResults;
    } finally {
      if (requestId === this._tagRequestId) {
        this.tagsLoading = false;
      }
    }
  },

  selectTag(tag) {
    this.form.tag = tag;
    this.tagExistenceChecked = true;
    this.tagDropdownOpen = false;
  },

  parseSelectorTag(value) {
    const match = /^v(\d+)\.(\d+)$/.exec((value || "").trim());
    if (!match) return null;
    return [
      Number.parseInt(match[1], 10),
      Number.parseInt(match[2], 10),
    ];
  },

  isSupportedSuggestionTag(value) {
    return this.isSupportedSelectorTag(value);
  },

  isSupportedSelectorTag(value) {
    const parsed = this.parseSelectorTag(value);
    if (!parsed) return false;
    for (let i = 0; i < MIN_SELECTOR_VERSION.length; i += 1) {
      if (parsed[i] > MIN_SELECTOR_VERSION[i]) return true;
      if (parsed[i] < MIN_SELECTOR_VERSION[i]) return false;
    }
    return true;
  },

  parseCompatibilityTag(value) {
    const match = /^v(\d+)\.(\d+)(?:\..+)?$/.exec((value || "").trim());
    if (!match) return null;
    return {
      major: Number.parseInt(match[1], 10),
      minor: Number.parseInt(match[2], 10),
    };
  },

  async scheduleUpdate() {
    if (!this.form.branch?.trim()) {
      this.error = "Choose a branch.";
      return;
    }

    if (!this.form.tag?.trim()) {
      this.error = "Enter a release tag to schedule.";
      return;
    }

    if (!this.parseSelectorTag(this.form.tag)) {
      this.error = "Release tag must use the format vX.Y.";
      return;
    }

    if (!this.isSupportedSelectorTag(this.form.tag)) {
      this.error = "Release tag must be v1.0 or newer.";
      return;
    }

    if (!this.selectedTagExistsOnBranch) {
      this.tagExistenceChecked = true;
      await this.searchTags({ openResults: false });
      if (!this.selectedTagExistsOnBranch) {
        this.error = `Version ${this.trimmedTag} does not exist on branch ${this.form.branch || "main"}.`;
        return;
      }
    }

    this.saving = true;
    this.error = "";
    try {
      const response = await API.callJsonApi("self_update_schedule", {
        branch: this.form.branch,
        tag: this.form.tag,
        backup_usr: this.form.backup_usr,
        backup_path: this.form.backup_path,
        backup_name: this.form.backup_name,
        backup_conflict_policy: this.form.backup_conflict_policy,
      });
      if (!response?.success) {
        throw new Error(response?.error || "Failed to schedule the self-update.");
      }

      if (this.info) {
        this.info.pending = response.pending;
      }
      await notificationStore.frontendWarning(
        "Agent Zero is restarting to apply the requested branch and release tag.",
        "Self Update",
        10,
        "self-update-restart",
        undefined,
        true,
      );
      this.saveReturnUrl(window.location.href);
      await this.restartAndReload();
    } catch (error) {
      console.error("Failed to schedule self-update:", error);
      this.error = error.message || "Failed to schedule the self-update.";
    } finally {
      this.saving = false;
    }
  },

  async restartAndReload() {
    this.restarting = true;
    this.clearReconnectTimer();
    let observedBackendUnavailable = false;
    this.setRestartState(
      "Starting self-update",
      "The request was saved. Agent Zero is about to restart and apply the requested branch and tag."
    );
    this.ensureProgressOverlay();

    try {
      const token = await API.getCsrfToken();
      const restartResponse = await fetch("/api/restart", {
        method: "POST",
        credentials: "same-origin",
        keepalive: true,
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": token,
        },
        body: JSON.stringify({}),
      });
      if (restartResponse && !restartResponse.ok) {
        throw new Error(`Restart request failed with HTTP ${restartResponse.status}.`);
      }
    } catch (_error) {
      // The restart request often terminates the backend mid-flight.
    }

    const maxWaitMs =
      ((this.info?.pending?.health_timeout_seconds ||
        this.info?.defaults?.health_timeout_seconds ||
        120) *
        1000) +
      HEALTH_WAIT_BUFFER_MS;
    const deadline = Date.now() + maxWaitMs;
    let lastError = "";
    this.setRestartState(
      "Update in progress",
      "Agent Zero is restarting and the updater is running. This page will reload automatically when /api/health starts responding again."
    );

    while (Date.now() < deadline) {
      try {
        const response = await fetch("/api/health", {
          method: "GET",
          credentials: "same-origin",
          cache: "no-store",
        });
        if (response.ok && observedBackendUnavailable) {
          const returnUrl = this.getSavedReturnUrl() || window.location.href;
          this.saveReturnUrl("");
          window.location.replace(returnUrl);
          return;
        }
        if (response.ok) {
          this.setRestartState(
            "Restarting backend",
            "Waiting for Agent Zero to disconnect before reloading the page."
          );
          lastError = "Health check is still responding before the restart has completed.";
        } else {
          observedBackendUnavailable = true;
          this.setRestartState(
            "Update in progress",
            "Agent Zero is restarting and the updater is running. This page will reload automatically when the health check becomes healthy again."
          );
          lastError = `Health check returned HTTP ${response.status}.`;
        }
      } catch (error) {
        observedBackendUnavailable = true;
        this.setRestartState(
          "Update in progress",
          "Agent Zero is temporarily unavailable while it restarts. Waiting for the new runtime to become healthy."
        );
        lastError = error?.message || String(error);
      }

      await new Promise((resolve) => {
        this._reconnectTimer = setTimeout(() => {
          this._reconnectTimer = null;
          resolve();
        }, HEALTH_POLL_INTERVAL_MS);
      });
    }

    this.restarting = false;
    this.removeProgressOverlay();
    this.saveReturnUrl("");
    this.error =
      "Agent Zero did not come back within the expected window. It may still be rolling back. " +
      (lastError ? `Last health check error: ${lastError}` : "");
    await this.refresh();
  },

  close() {
    closeModal(SELF_UPDATE_MODAL_PATH);
  },
};

const store = createStore("selfUpdateStore", model);

export { store };
