import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";
import { openModal, closeModal } from "/js/modals.js";

const HEALTH_POLL_INTERVAL_MS = 2000;
const HEALTH_WAIT_BUFFER_MS = 30000;
const SELF_UPDATE_OVERLAY_ID = "self-update-progress-overlay";
const SELF_UPDATE_MODAL_PATH = "settings/external/self-update-modal.html";
const SELF_UPDATE_MANUAL_BACKUP_MODAL_PATH = "settings/backup/backup_restore.html";
const MIN_SELECTOR_VERSION = [1, 0];

const model = {
  loading: false,
  saving: false,
  restarting: false,
  tagsLoading: false,
  activeTab: "quick",
  error: "",
  tagsError: "",
  info: null,
  availableTagOptions: [],
  higherMajorVersions: [],
  majorUpgradeVersions: [],
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

  get hasPendingInitialLoad() {
    return !this.info && !this.error;
  },

  get isCheckingStatus() {
    return this.loading || this.hasPendingInitialLoad;
  },

  get isSupported() {
    return Boolean(this.info?.supported);
  },

  get currentVersion() {
    return (
      this.info?.current?.display_version ||
      this.info?.current?.short_tag ||
      (this.hasPendingInitialLoad ? "Loading" : "unknown")
    );
  },

  get currentBranch() {
    return this.info?.current?.branch || "";
  },

  get currentComparableVersion() {
    return this.info?.current?.short_tag || "";
  },

  get mainBranchLatestTag() {
    return this.info?.main_branch_latest?.short_tag || "";
  },

  get mainBranchLatestVersion() {
    return (
      this.info?.main_branch_latest?.display_version ||
      this.info?.main_branch_latest?.short_tag ||
      (this.hasPendingInitialLoad ? "Loading" : "Unavailable")
    );
  },

  get mainBranchLatestCommit() {
    return this.info?.main_branch_latest?.short_commit || "";
  },

  get mainBranchLatestSupported() {
    return Boolean(this.info?.main_branch_latest?.supported);
  },

  get currentReleasedAt() {
    return this.info?.current?.released_at || "";
  },

  get mainBranchLatestReleasedAt() {
    return this.info?.main_branch_latest?.released_at || "";
  },

  get trimmedTag() {
    return (this.form.tag || "").trim();
  },

  get hasAvailableTags() {
    return this.availableTagOptions.length > 0;
  },

  get availableTags() {
    return this.availableTagOptions
      .map((option) => option?.value || "")
      .filter(Boolean);
  },

  get selectedTagExistsOnBranch() {
    const tag = this.trimmedTag;
    return Boolean(tag) && this.availableTags.includes(tag);
  },

  get higherMajorVersionMessage() {
    if (!this.higherMajorVersions.length) return "";
    const versionLabels = this.higherMajorVersions.map((major) => `v${major}.x`);
    const versionText =
      versionLabels.length === 1
        ? versionLabels[0]
        : `${versionLabels.slice(0, -1).join(", ")} and ${versionLabels[versionLabels.length - 1]}`;
    return `A newer major release line is available on this branch (${versionText}). Major upgrades require downloading a newer Docker image before using self-update.`;
  },

  get hasMajorUpgrade() {
    return this.majorUpgradeVersions.length > 0;
  },

  get majorUpgradeBannerMessage() {
    if (!this.majorUpgradeVersions.length) return "";
    const versionLabels = this.majorUpgradeVersions.map((major) => `v${major}.x`);
    const versionText =
      versionLabels.length === 1
        ? versionLabels[0]
        : `${versionLabels.slice(0, -1).join(", ")} and ${versionLabels[versionLabels.length - 1]}`;
    return `A newer major release line is available (${versionText}). This self-updater keeps showing only updates from the current major version. Major upgrades require a new Docker image and data migration.`;
  },

  get versionSelectPlaceholder() {
    if (this.tagsLoading) return "Loading versions...";
    if (!this.hasAvailableTags) return "No versions available";
    return "Select a version";
  },

  get canScheduleUpdate() {
    return (
      this.isSupported &&
      !this.isBusy &&
      !this.tagsLoading &&
      this.hasAvailableTags &&
      this.isSelectableTag(this.form.tag) &&
      this.selectedTagExistsOnBranch
    );
  },

  get quickUpdateComparison() {
    return this.compareSelectorVersions(
      this.mainBranchLatestTag,
      this.currentComparableVersion,
    );
  },

  get quickUpdateAvailable() {
    return (
      this.isSupported &&
      !this.isBusy &&
      this.mainBranchLatestSupported &&
      this.quickUpdateComparison !== null &&
      this.quickUpdateComparison > 0
    );
  },

  get quickStatusLabel() {
    if (this.isCheckingStatus) return "CHECKING";
    if (!this.isSupported) return "UNAVAILABLE";
    if (!this.mainBranchLatestSupported) return "MAIN UNAVAILABLE";
    if (!this.mainBranchLatestTag) return "UNAVAILABLE";
    if (this.quickUpdateComparison === null) return "REVIEW";
    if (this.quickUpdateComparison > 0) return "UPDATE AVAILABLE";
    if (this.quickUpdateComparison === 0) return "UP TO DATE";
    return "AHEAD OF MAIN";
  },

  get quickBehindMinorCount() {
    const latest = this.parseSelectorTag(this.mainBranchLatestTag);
    const current = this.parseSelectorTag(this.currentComparableVersion);
    if (!latest || !current || this.quickUpdateComparison === null || this.quickUpdateComparison <= 0) {
      return null;
    }
    if (latest[0] !== current[0]) {
      return 4;
    }
    return latest[1] - current[1];
  },

  get quickStatusMessage() {
    if (this.isCheckingStatus) {
      return "Checking update status...";
    }
    if (!this.isSupported) {
      return "Self-update is currently available only in dockerized Agent Zero deployments that boot through /exe/run_A0.sh.";
    }
    if (!this.mainBranchLatestSupported) {
      return "The main branch is not currently available from the configured remote.";
    }
    if (!this.mainBranchLatestTag) {
      return "No supported main-branch version could be resolved right now.";
    }
    if (this.quickUpdateComparison === null) {
      return "The current checkout does not expose a comparable tagged version. Use Advanced if you still want to choose a target manually.";
    }
    if (this.quickUpdateComparison > 0) {
      if (this.quickBehindMinorCount !== null && this.quickBehindMinorCount <= 3) {
        return `This instance is ${this.quickBehindMinorCount} minor version${this.quickBehindMinorCount === 1 ? "" : "s"} behind the latest release currently available on main.`;
      }
      return `This instance is significantly behind the latest release currently available on main. Restart Agent Zero to move to ${this.mainBranchLatestVersion}.`;
    }
    if (this.quickUpdateComparison === 0) {
      return "You already have the latest version of Agent Zero main branch";
    }
    return "This checkout already reports a newer tagged version than main.";
  },

  get quickStatusBadgeClass() {
    if (this.isCheckingStatus) {
      return "status-pill-neutral";
    }
    if (!this.isSupported || !this.mainBranchLatestSupported || !this.mainBranchLatestTag) {
      return "status-pill-neutral";
    }
    if (this.quickUpdateComparison === null) {
      return "status-pill-neutral";
    }
    if (this.quickUpdateComparison === 0) {
      return "status-pill-success";
    }
    if (this.quickUpdateComparison > 0) {
      return this.quickBehindMinorCount !== null && this.quickBehindMinorCount <= 3
        ? "status-pill-info"
        : "status-pill-warning";
    }
    return "status-pill-neutral";
  },

  get quickComparisonIcon() {
    if (this.isCheckingStatus) return "progress_activity";
    if (!this.isSupported || !this.mainBranchLatestSupported || !this.mainBranchLatestTag) {
      return "help";
    }
    if (this.quickUpdateComparison === null) {
      return "help";
    }
    if (this.quickUpdateComparison === 0) {
      return "task_alt";
    }
    if (this.quickUpdateComparison > 0) {
      return this.quickBehindMinorCount !== null && this.quickBehindMinorCount <= 3
        ? "update"
        : "warning";
    }
    return "north_east";
  },

  get quickComparisonIconClass() {
    if (this.isCheckingStatus) {
      return "self-update-quick-icon-neutral";
    }
    if (!this.isSupported || !this.mainBranchLatestSupported || !this.mainBranchLatestTag) {
      return "self-update-quick-icon-neutral";
    }
    if (this.quickUpdateComparison === null) {
      return "self-update-quick-icon-neutral";
    }
    if (this.quickUpdateComparison === 0) {
      return "self-update-quick-icon-success";
    }
    if (this.quickUpdateComparison > 0) {
      return this.quickBehindMinorCount !== null && this.quickBehindMinorCount <= 3
        ? "self-update-quick-icon-info"
        : "self-update-quick-icon-warning";
    }
    return "self-update-quick-icon-neutral";
  },

  get quickMajorUpgradeNotice() {
    const latest = this.parseSelectorTag(this.mainBranchLatestTag);
    const current = this.parseSelectorTag(this.currentComparableVersion);
    if (!latest || !current || latest[0] === current[0]) {
      return "";
    }
    return (
      "This update crosses into a newer major release line. If your Docker image is older, " +
      "you may still need to update the image itself after applying the repo update."
    );
  },

  async init() {
    await this.refresh();
  },

  setTab(tab) {
    if (tab === "quick" || tab === "advanced") {
      this.activeTab = tab;
    }
  },

  cleanup() {
    this.clearReconnectTimer();
    this.error = "";
    this.tagsError = "";
    this.loading = false;
    this.saving = false;
    this.restarting = false;
    this.tagsLoading = false;
    this.availableTagOptions = [];
    this.higherMajorVersions = [];
    this.majorUpgradeVersions = [];
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

  formatReleaseTimestamp(value) {
    if (!value) {
      if (this.hasPendingInitialLoad) {
        return "Loading";
      }
      return "Release date unavailable";
    }
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(value)) {
      return value;
    }
    return this.formatTimestamp(value);
  },

  formatBranchTag(branch, tag) {
    return `${branch || "main"} / ${tag || "None"}`;
  },

  normalizeLastStatus(status) {
    return (status || "unknown").trim().toLowerCase();
  },

  getLastStatusLabel(status) {
    const normalizedStatus = this.normalizeLastStatus(status);
    return normalizedStatus ? normalizedStatus.replace(/_/g, " ") : "unknown";
  },

  getLastStatusBadgeClass(status) {
    const normalizedStatus = this.normalizeLastStatus(status);
    if (normalizedStatus === "success") {
      return "status-pill-success";
    }
    if (normalizedStatus === "failed" || normalizedStatus === "rollback_failed") {
      return "status-pill-error";
    }
    if (normalizedStatus === "rolled_back") {
      return "status-pill-warning";
    }
    return "status-pill-neutral";
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

  resetRestartState() {
    this.restartStatusText = "";
    this.restartDetailText = "";
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
      this.majorUpgradeVersions = Array.isArray(response.major_upgrade_versions)
        ? response.major_upgrade_versions
        : [];
      this.applyFormState(
        response.pending || {
          ...(response.defaults || {}),
          tag: "",
        },
      );
      this.applyAvailableTags({
        options: response.available_tag_options,
        higherMajorVersions: response.available_higher_major_versions,
        error: response.available_tags_error,
      });
    } catch (error) {
      console.error("Failed to load self-update info:", error);
      this.error = error.message || "Failed to load self-update info.";
    } finally {
      this.loading = false;
    }
  },

  applyFormState(source) {
    this.form.branch =
      source?.branch ||
      this.info?.defaults?.branch ||
      this.currentBranch ||
      "main";
    this.form.tag =
      typeof source?.tag === "string"
        ? source.tag
        : this.info?.defaults?.tag || this.currentVersion;
    this.form.backup_usr =
      typeof source?.backup_usr === "boolean" ? source.backup_usr : true;
    this.form.backup_path = source?.backup_path || "";
    this.form.backup_name = source?.backup_name || "";
    this.form.backup_conflict_policy =
      source?.backup_conflict_policy || "rename";
  },

  applyAvailableTags({ options = [], higherMajorVersions = [], error = "" } = {}) {
    this.availableTagOptions = Array.isArray(options) ? options : [];
    this.higherMajorVersions = Array.isArray(higherMajorVersions)
      ? higherMajorVersions
      : [];
    this.tagsError = error || "";

    if (!this.availableTags.length) {
      this.form.tag = "";
      return;
    }

    const preferredTag = this.trimmedTag;
    if (preferredTag && this.availableTags.includes(preferredTag)) {
      return;
    }

    this.form.tag = "";
  },

  async openModal() {
    await openModal(SELF_UPDATE_MODAL_PATH);
  },

  async openManualBackupModal() {
    await openModal(SELF_UPDATE_MANUAL_BACKUP_MODAL_PATH);
  },

  async onBranchChanged() {
    await this.fetchTags();
  },

  async fetchTags() {
    const requestId = ++this._tagRequestId;
    this.tagsLoading = true;
    this.tagsError = "";

    try {
      const response = await API.callJsonApi("self_update_tags", {
        branch: this.form.branch,
      });
      if (!response?.success) {
        throw new Error(response?.error || "Failed to fetch release tags.");
      }
      if (requestId !== this._tagRequestId) {
        return;
      }
      this.applyAvailableTags({
        options: response.tag_options,
        higherMajorVersions: response.higher_major_versions,
        error: response.error,
      });
    } catch (error) {
      console.error("Failed to fetch self-update tags:", error);
      if (requestId !== this._tagRequestId) {
        return;
      }
      this.applyAvailableTags();
      this.tagsError = error.message || "Failed to fetch release tags.";
    } finally {
      if (requestId === this._tagRequestId) {
        this.tagsLoading = false;
      }
    }
  },

  parseSelectorTag(value) {
    const match = /^v(\d+)\.(\d+)$/.exec((value || "").trim());
    if (!match) return null;
    return [
      Number.parseInt(match[1], 10),
      Number.parseInt(match[2], 10),
    ];
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

  isLatestSelectorTag(value) {
    return (value || "").trim().toLowerCase() === "latest";
  },

  isSelectableTag(value) {
    return this.isLatestSelectorTag(value) || this.isSupportedSelectorTag(value);
  },

  compareSelectorVersions(left, right) {
    const leftVersion = this.parseSelectorTag(left);
    const rightVersion = this.parseSelectorTag(right);
    if (!leftVersion || !rightVersion) {
      return null;
    }
    if (leftVersion[0] !== rightVersion[0]) {
      return leftVersion[0] - rightVersion[0];
    }
    if (leftVersion[1] !== rightVersion[1]) {
      return leftVersion[1] - rightVersion[1];
    }
    return 0;
  },

  async scheduleUpdateRequest(payload, notificationMessage) {
    this.saving = true;
    this.error = "";
    this.setRestartState(
      "Preparing update",
      "Saving the request and asking Agent Zero to restart."
    );
    this.ensureProgressOverlay();
    try {
      const response = await API.callJsonApi("self_update_schedule", payload);
      if (!response?.success) {
        throw new Error(response?.error || "Failed to schedule the self-update.");
      }

      if (this.info) {
        this.info.pending = response.pending;
      }
      notificationStore.frontendWarning(
        notificationMessage,
        "Self Update",
        10,
        "self-update-restart",
        undefined,
        true,
      ).catch((warningError) => {
        console.error("Failed to show self-update warning toast:", warningError);
      });
      await this.restartAndReload();
    } catch (error) {
      console.error("Failed to schedule self-update:", error);
      this.restarting = false;
      this.resetRestartState();
      this.removeProgressOverlay();
      this.error = error.message || "Failed to schedule the self-update.";
    } finally {
      this.saving = false;
    }
  },

  async scheduleUpdate() {
    if (!this.form.branch?.trim()) {
      this.error = "Choose a branch.";
      return;
    }

    if (!this.form.tag?.trim()) {
      this.error = "Choose a version from the list.";
      return;
    }

    if (!this.isLatestSelectorTag(this.form.tag) && !this.parseSelectorTag(this.form.tag)) {
      this.error = "Release tag must use the format vX.Y.";
      return;
    }

    if (!this.isLatestSelectorTag(this.form.tag) && !this.isSupportedSelectorTag(this.form.tag)) {
      this.error = "Release tag must be v1.0 or newer.";
      return;
    }

    if (!this.selectedTagExistsOnBranch) {
      await this.fetchTags();
      if (!this.selectedTagExistsOnBranch) {
        this.error = `Version ${this.trimmedTag} does not exist on branch ${this.form.branch || "main"}.`;
        return;
      }
    }

    await this.scheduleUpdateRequest(
      {
        branch: this.form.branch,
        tag: this.form.tag,
        backup_usr: this.form.backup_usr,
        backup_path: this.form.backup_path,
        backup_name: this.form.backup_name,
        backup_conflict_policy: this.form.backup_conflict_policy,
      },
      "Agent Zero is restarting to apply the requested branch and version target.",
    );
  },

  async scheduleQuickUpdate() {
    if (!this.mainBranchLatestSupported || !this.mainBranchLatestTag) {
      this.error = "Latest main-branch version is not available right now.";
      return;
    }

    if (this.quickUpdateComparison === null) {
      this.error =
        "The current checkout cannot be compared to the latest main version. Use Advanced to choose a version manually.";
      return;
    }

    if (this.quickUpdateComparison <= 0) {
      return;
    }

    await this.scheduleUpdateRequest(
      {
        branch: "main",
        tag: this.mainBranchLatestTag,
        backup_usr: this.info?.defaults?.backup_usr ?? true,
        backup_path: this.info?.defaults?.backup_path || "",
        backup_name: this.info?.defaults?.backup_name || "",
        backup_conflict_policy:
          this.info?.defaults?.backup_conflict_policy || "rename",
      },
      "Agent Zero is restarting to apply the latest version from main.",
    );
  },

  async restartAndReload() {
    this.restarting = true;
    this.clearReconnectTimer();
    let observedBackendUnavailable = false;
    this.setRestartState(
      "Starting self-update",
      "The request was saved. Agent Zero is about to restart and apply the requested branch and version target."
    );
    this.ensureProgressOverlay();

    let restartRequestStarted = false;
    try {
      const token = await API.getCsrfToken();
      restartRequestStarted = true;
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
        if (restartResponse.status >= 500) {
          console.warn(
            `Restart request returned HTTP ${restartResponse.status} while Agent Zero was shutting down. Continuing to wait for the new runtime.`
          );
          this.setRestartState(
            "Restarting backend",
            "Agent Zero is shutting down and applying the update. Waiting for the new runtime to come back healthy."
          );
        } else {
          throw new Error(
            `Restart request failed with HTTP ${restartResponse.status}.`
          );
        }
      } else {
        this.setRestartState(
          "Restarting backend",
          "Agent Zero accepted the restart request. Waiting for the updater to take over."
        );
      }
    } catch (error) {
      if (!restartRequestStarted) {
        this.restarting = false;
        this.resetRestartState();
        this.removeProgressOverlay();
        throw error;
      }
      console.warn(
        "Restart request connection closed while Agent Zero was restarting:",
        error
      );
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
          window.location.reload();
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
    this.resetRestartState();
    this.removeProgressOverlay();
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
