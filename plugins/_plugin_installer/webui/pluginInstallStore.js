import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";
import { addBlankTargetsToLinks } from "/js/messages.js";
import { openModal } from "/js/modals.js";
import { marked } from "/vendor/marked/marked.esm.js";
import { toastFrontendSuccess, toastFrontendError } from "/components/notifications/notification-store.js";
import { showConfirmDialog } from "/js/confirmDialog.js";
import { store as imageViewerStore } from "/components/modals/image-viewer/image-viewer-store.js";
import { store as pluginListStore } from "/components/plugins/list/pluginListStore.js";
import { store as pluginExecuteStore } from "/components/plugins/list/plugin-execute-store.js";
import { store as pluginSettingsStore } from "/components/plugins/plugin-settings-store.js";

const PLUGIN_API = "plugins/_plugin_installer/plugin_install";
const PER_PAGE = 24;

const SECURITY_WARNING = {
  title: "Security Warning",
  message: `
    <p><strong>Third-party plugins may contain malicious code.</strong> <br> We can't guarantee their safety &mdash; install at your own risk.</p>
    <p style="margin-top: 0.75em;">We recommend scanning all plugins with A0 first.</p>
  `,
  type: "warning",
  confirmText: "Install Anyway",
  cancelText: "Cancel",
};

const model = {
  // ZIP install state
  zipFile: null,
  zipFileName: "",

  // Git install state
  gitUrl: "",
  gitToken: "",

  // Index state
  index: { authors: {}, plugins: {} },
  indexLoadPromise: null,
  installedPlugins: [],
  installedPluginDetails: {},
  search: "",
  page: 1,
  sortBy: "stars",
  browseFilter: "all",
  selectedPlugin: null,

  // Shared state
  loading: false,
  loadingMessage: "",
  result: null,

  // README state
  readmeContent: null,
  readmeLoading: false,

  // Installed plugin detail (for manage buttons)
  installedPluginInfo: null,

  detailThumbnailUrl: null,

  // Tab state
  activeTab: "store",

  setTab(tab) {
    this.activeTab = tab;
    this.result = null;
    if (tab === "store") {
      this.resetIndex();
      void this.fetchIndex();
    }
  },

  setBrowseFilter(filter) {
    this.browseFilter = filter || "all";
    this.page = 1;
  },

  /** Normalize GitHub URL and return raw.githubusercontent.com base (no trailing slash). */
  _githubRawBase(githubUrl) {
    if (!githubUrl || typeof githubUrl !== "string") return null;
    let url = githubUrl.trim().replace(/\.git$/i, "");
    if (!url.includes("github.com")) return null;
    return url.replace("https://github.com/", "https://raw.githubusercontent.com/");
  },

  _rebaseReadmeLinks(html, githubUrl, branch) {
    if (!html || typeof html !== "string" || !githubUrl || !branch) return html;

    let repoUrl;
    try {
      repoUrl = new URL(githubUrl.trim().replace(/\.git$/i, ""));
    } catch {
      return html;
    }

    if (repoUrl.hostname !== "github.com") return html;

    const [owner, repo] = repoUrl.pathname
      .replace(/^\/+|\/+$/g, "")
      .split("/");
    if (!owner || !repo) return html;

    const repoBlobBase = `https://github.com/${owner}/${repo}/blob/${branch}`;
    const doc = new DOMParser().parseFromString(html, "text/html");

    doc.querySelectorAll("a[href]").forEach((anchor) => {
      const href = (anchor.getAttribute("href") || "").trim();
      if (
        !href ||
        href.startsWith("#") ||
        href.startsWith("//") ||
        /^[a-zA-Z][a-zA-Z\d+.-]*:/.test(href)
      ) {
        return;
      }

      try {
        const resolved = new URL(href, "https://repo-root.invalid/");
        const repoPath = resolved.pathname.replace(/^\/+/, "");
        anchor.setAttribute(
          "href",
          `${repoBlobBase}/${repoPath}${resolved.search}${resolved.hash}`,
        );
      } catch {
        // Leave malformed links unchanged.
      }
    });

    return doc.body.innerHTML;
  },

  _pluginPrimaryTag(plugin) {
    const tags = Array.isArray(plugin?.tags) ? plugin.tags.filter(Boolean) : [];
    return tags[0] || "";
  },

  _formatBrowseTag(tag) {
    if (!tag || typeof tag !== "string") return "";
    return tag
      .split(/[-_]/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  },

  _matchesBrowseFilter(plugin, filterKey) {
    if (!filterKey || filterKey === "all") return true;
    if (filterKey === "installed") return !!plugin?.installed;
    if (filterKey === "update") return !!plugin?.has_update;
    if (filterKey === "popular") return (plugin?.stars || 0) >= 3;
    if (filterKey.startsWith("tag:")) {
      return this._pluginPrimaryTag(plugin) === filterKey.slice(4);
    }
    return false;
  },

  _compareTimestamp(a, b) {
    const aTime = a ? Date.parse(a) : NaN;
    const bTime = b ? Date.parse(b) : NaN;
    if (Number.isNaN(aTime) || Number.isNaN(bTime)) return 0;
    if (aTime === bTime) return 0;
    return aTime > bTime ? 1 : -1;
  },

  _hasPluginHubUpdate(indexPlugin, installedPlugin) {
    const latestCommit = (indexPlugin?.commit || "").trim();
    const currentCommit = (installedPlugin?.current_commit || "").trim();
    if (!latestCommit || !currentCommit) return false;
    if (latestCommit === currentCommit) return false;

    const latestTimestamp = indexPlugin?.updated || "";
    const currentTimestamp = installedPlugin?.current_commit_timestamp || "";
    const timestampComparison = this._compareTimestamp(latestTimestamp, currentTimestamp);
    if (timestampComparison !== 0) return timestampComparison > 0;

    return true;
  },

  // ── ZIP Install ──────────────────────────────

  handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    this.zipFile = file;
    this.zipFileName = file.name;
    this.result = null;
  },

  async installZip() {
    if (!this.zipFile) {
      void toastFrontendError("Please select a ZIP file first", "Plugin Installer");
      return;
    }

    const confirmed = await showConfirmDialog(SECURITY_WARNING);
    if (!confirmed) return;

    try {
      this.loading = true;
      this.loadingMessage = "Installing plugin from ZIP...";
      this.result = null;

      const formData = new FormData();
      formData.append("action", "install_zip");
      formData.append("plugin_file", this.zipFile);

      const response = await api.fetchApi(PLUGIN_API, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!data.success) {
        void toastFrontendError(data.error || "Installation failed", "Plugin Installer");
        return;
      }

      this.result = data;

      toastFrontendSuccess(
        `Plugin "${data.title || data.plugin_name}" installed`,
        "Plugin Installer"
      );
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      void toastFrontendError(`Installation error: ${message}`, "Plugin Installer");
    } finally {
      this.loading = false;
      this.loadingMessage = "";
    }
  },

  // ── Git Install ──────────────────────────────

  async installGit() {
    const url = (this.gitUrl || "").trim();
    if (!url) {
      void toastFrontendError("Please enter a Git URL", "Plugin Installer");
      return;
    }

    const confirmed = await showConfirmDialog(SECURITY_WARNING);
    if (!confirmed) return;

    try {
      this.loading = true;
      this.loadingMessage = "Cloning repository...";
      this.result = null;

      const data = await api.callJsonApi(PLUGIN_API, {
        action: "install_git",
        git_url: url,
        git_token: this.gitToken || "",
      });

      if (!data.success) {
        void toastFrontendError(data.error || "Clone failed", "Plugin Installer");
        return;
      }

      this.result = data;

      toastFrontendSuccess(
        `Plugin "${data.title || data.plugin_name}" installed`,
        "Plugin Installer"
      );
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      void toastFrontendError(`Clone error: ${message}`, "Plugin Installer");
    } finally {
      this.loading = false;
      this.loadingMessage = "";
    }
  },

  // ── Index Browse ─────────────────────────────

  hasIndexData() {
    const plugins = this.index?.plugins;
    return !!plugins && typeof plugins === "object" && Object.keys(plugins).length > 0;
  },

  async fetchIndex(options = {}) {
    const background = !!options?.background;
    const suppressErrors = !!options?.suppressErrors;
    if (this.indexLoadPromise) {
      return this.indexLoadPromise;
    }

    const loadPromise = (async () => {
    try {
      if (!background) {
        this.loading = true;
        this.loadingMessage = "Loading plugin index...";
      }

      const data = await api.callJsonApi(PLUGIN_API, {
        action: "fetch_index",
      });

      if (!data.success) {
        if (!suppressErrors) {
          void toastFrontendError(data.error || "Failed to load index", "Plugin Installer");
        }
        return false;
      }

      this.index = data.index;
      this.installedPlugins = data.installed_plugins || [];
      const installedResponse = await api.callJsonApi("plugins_list", {
        filter: { custom: true, builtin: false, search: "" },
      });
      const installedList = Array.isArray(installedResponse.plugins) ? installedResponse.plugins : [];
      this.installedPluginDetails = Object.fromEntries(
        installedList.map((plugin) => [plugin.name, plugin])
      );
      this.page = 1;
      return true;
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      if (!suppressErrors) {
        void toastFrontendError(`Failed to load plugin index: ${message}`, "Plugin Installer");
      }
      return false;
    } finally {
      if (!background) {
        this.loading = false;
        this.loadingMessage = "";
      }
    }
    })();

    this.indexLoadPromise = loadPromise.finally(() => {
      if (this.indexLoadPromise === loadPromise) {
        this.indexLoadPromise = null;
      }
    });

    return this.indexLoadPromise;
  },

  async ensureIndexLoaded(options = {}) {
    if (this.hasIndexData()) {
      return true;
    }

    await this.fetchIndex({
      background: !!options?.background,
      suppressErrors: !!options?.background,
    });
    return this.hasIndexData();
  },

  get pluginsList() {
    if (!this.index?.plugins) return [];
    return Object.entries(this.index.plugins).map(([key, val]) => {
      const installedPlugin = this.installedPluginDetails[key] || null;
      const installed = this.installedPlugins.some((pluginKey) => pluginKey === key);
      const plugin = {
        key,
        ...val,
        commit: val?.commit || val?.latest_commit || "",
        updated: val?.updated || val?.latest_commit_timestamp || "",
        version: val?.version || "",
        installed,
      };

      return {
        ...plugin,
        current_commit: installedPlugin?.current_commit || "",
        current_commit_timestamp: installedPlugin?.current_commit_timestamp || "",
        has_update: this._hasPluginHubUpdate(plugin, installedPlugin),
      };
    });
  },

  get browseFilters() {
    const plugins = this.pluginsList;
    const filters = [{ key: "all", label: "All", count: plugins.length }];

    const installedCount = plugins.filter((plugin) => plugin.installed).length;
    if (installedCount) {
      filters.push({ key: "installed", label: "Installed", count: installedCount });
    }

    const updateCount = plugins.filter((plugin) => plugin.has_update).length;
    filters.push({ key: "update", label: "Update", count: updateCount });

    const popularCount = plugins.filter((plugin) => (plugin.stars || 0) > 0).length;
    if (popularCount) {
      filters.push({ key: "popular", label: "Popular", count: popularCount });
    }

    const tagCounts = new Map();
    for (const plugin of plugins) {
      const tag = this._pluginPrimaryTag(plugin);
      if (!tag) continue;
      tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
    }

    for (const [tag, count] of Array.from(tagCounts.entries())
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 4)) {
      filters.push({
        key: `tag:${tag}`,
        label: this._formatBrowseTag(tag),
        count,
      });
    }

    return filters;
  },

  get filteredPlugins() {
    let list = this.pluginsList.filter((plugin) =>
      this._matchesBrowseFilter(plugin, this.browseFilter)
    );
    const q = (this.search || "").toLowerCase().trim();
    if (q) {
      list = list.filter(
        (p) =>
          (p.title || "").toLowerCase().includes(q) ||
          (p.author || "").toLowerCase().includes(q) ||
          (p.description || "").toLowerCase().includes(q) ||
          (p.key || "").toLowerCase().includes(q) ||
          (p.tags || []).some((t) => t.toLowerCase().includes(q))
      );
    }
    if (this.sortBy === "stars") {
      list.sort((a, b) => (b.stars || 0) - (a.stars || 0));
    } else {
      list.sort((a, b) =>
        (a.title || a.key).localeCompare(b.title || b.key)
      );
    }
    return list;
  },

  get browseResultsSummary() {
    const total = this.pluginsList.length;
    const visible = this.filteredPlugins.length;
    if (!total) return "No plugins available";
    if (visible === total) {
      return `${total} plugin${total === 1 ? "" : "s"} available`;
    }
    return `Showing ${visible} of ${total} plugins`;
  },

  get totalPages() {
    return Math.max(1, Math.ceil(this.filteredPlugins.length / PER_PAGE));
  },

  get paginatedPlugins() {
    const start = (this.page - 1) * PER_PAGE;
    return this.filteredPlugins.slice(start, start + PER_PAGE);
  },

  getBrowseSubtitle(plugin) {
    const author = (plugin?.author || "").trim();
    if (author) return author;
    const tag = this._pluginPrimaryTag(plugin);
    if (tag) return this._formatBrowseTag(tag);
    return plugin?.key || "";
  },

  getBrowsePrimaryTag(plugin) {
    return this._formatBrowseTag(this._pluginPrimaryTag(plugin));
  },

  setPage(p) {
    this.page = Math.max(1, Math.min(p, this.totalPages));
  },

  getPluginHubPluginByKey(pluginKey) {
    const key = typeof pluginKey === "string" ? pluginKey.trim() : "";
    if (!key) return null;
    return this.pluginsList.find((plugin) => plugin.key === key) || null;
  },

  async openPluginHubDetailByKey(pluginKey) {
    const key = typeof pluginKey === "string" ? pluginKey.trim() : "";
    if (!key) return false;

    const loaded = await this.ensureIndexLoaded();
    if (!loaded) return false;

    const plugin = this.getPluginHubPluginByKey(key);
    if (!plugin) {
      void toastFrontendError(
        `Plugin "${key}" is not available in the Plugin Hub index`,
        "Plugin Installer"
      );
      return false;
    }

    this.openDetail(plugin);
    return true;
  },

  openDetail(plugin) {
    this.selectedPlugin = { ...plugin, name: plugin?.key || "" };
    this.result = null;
    this.installedPluginInfo = null;
    this.readmeContent = null;
    this.detailThumbnailUrl = this.getThumbnailUrl(this.selectedPlugin);
    if (this.selectedPlugin.installed) {
      this.fetchInstalledPluginInfo(this.selectedPlugin.name);
    }
    this.fetchReadme(this.selectedPlugin);
    openModal("/plugins/_plugin_installer/webui/install-detail.html");
  },

  async fetchReadme(plugin) {
    const rawBase = this._githubRawBase(plugin?.github);
    if (!rawBase) return;

    try {
      this.readmeLoading = true;
      this.readmeContent = null;
      let lastError = null;

      for (const branch of ["main", "master"]) {
        try {
          const response = await fetch(`${rawBase}/${branch}/README.md`);
          if (!response.ok) continue;

          const readme = await response.text();
          let html = marked.parse(readme, { breaks: true });
          html = this._rebaseReadmeLinks(html, plugin?.github, branch);
          this.readmeContent = addBlankTargetsToLinks(html);
          return;
        } catch (error) {
          lastError = error;
        }
      }

      if (lastError) {
        console.warn("Failed to fetch readme:", lastError);
      }
    } finally {
      this.readmeLoading = false;
    }
  },

  async installFromIndex(plugin) {
    if (!plugin?.github) {
      void toastFrontendError("No GitHub URL available for this plugin", "Plugin Installer");
      return;
    }

    const confirmed = await showConfirmDialog({
      ...SECURITY_WARNING,
      extensionContext: {
        kind: "plugin_hub_plugin_install_warning",
        source: "plugin_installer",
        pluginKey: plugin.key || "",
        pluginTitle: plugin.title || plugin.key || "",
        gitUrl: plugin.github,
      },
    });
    if (!confirmed) return;

    try {
      this.loading = true;
      this.loadingMessage = "Installing";

      const data = await api.callJsonApi(PLUGIN_API, {
        action: "install_git",
        git_url: plugin.github,
        plugin_name: plugin.key,
        thumbnail_url: this.getThumbnailUrl(plugin) || "",
      });

      if (!data.success) {
        void toastFrontendError(data.error || "Installation failed", "Plugin Installer");
        return;
      }

      const installedKey = plugin.key || data.plugin_name;
      if (installedKey && !this.installedPlugins.some((pluginKey) => pluginKey === installedKey)) {
        this.installedPlugins = [...this.installedPlugins, installedKey];
      }

      this.selectedPlugin = {
        ...plugin,
        name: plugin.key || "",
        installed: true,
      };
      this.detailThumbnailUrl = this.getThumbnailUrl(this.selectedPlugin);
      this.fetchInstalledPluginInfo(plugin.key || data.plugin_name);

      toastFrontendSuccess(
        `Plugin "${data.title || data.plugin_name}" installed`,
        "Plugin Installer"
      );
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      void toastFrontendError(`Installation error: ${message}`, "Plugin Installer");
    } finally {
      this.loading = false;
      this.loadingMessage = "";
    }
  },

  async _refreshSelectedPluginState(pluginKey) {
    await this.fetchInstalledPluginInfo(pluginKey);

    const latestInstalled = this.installedPluginInfo || null;
    const currentSelectedPlugin = this.selectedPlugin ? Object.assign({}, this.selectedPlugin) : null;
    const indexPlugin = this.pluginsList.find((plugin) => plugin.key === pluginKey) || currentSelectedPlugin;
    if (!indexPlugin) return;

    this.selectedPlugin = {
      ...indexPlugin,
      name: pluginKey || indexPlugin["name"] || "",
      installed: true,
      current_commit: latestInstalled?.["current_commit"] || indexPlugin["current_commit"] || "",
      current_commit_timestamp: latestInstalled?.["current_commit_timestamp"] || indexPlugin["current_commit_timestamp"] || "",
      has_update: this._hasPluginHubUpdate(indexPlugin, latestInstalled),
    };
    this.detailThumbnailUrl = this.getThumbnailUrl(this.selectedPlugin);
  },

  // ── Installed Plugin Info ─────────────────────

  async fetchInstalledPluginInfo(pluginName) {
    this.installedPluginInfo = null;
    try {
      const response = await api.callJsonApi("plugins_list", {
        filter: { custom: true, builtin: true, search: "" },
      });
      const plugins = Array.isArray(response.plugins) ? response.plugins : [];
      this.installedPluginInfo = plugins.find((p) => p.name === pluginName) || null;
    } catch (_error) {
      this.installedPluginInfo = null;
    }
  },


  handleOpenPlugin() {
    const info = this.installedPluginInfo;
    if (!info || !info.name || !info.has_main_screen) return;
    openModal(`/plugins/${info.name}/webui/main.html`);
  },

  async handleOpenConfig() {
    if (this.installedPluginInfo) {
      try {
        await pluginSettingsStore.openConfig(this.installedPluginInfo.name);
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        void toastFrontendError(message, "Plugin Installer");
      }
    }
  },

  async handleOpenDoc(doc) {
    if (this.installedPluginInfo) {
      await pluginListStore.openPluginDoc(this.installedPluginInfo, doc);
    }
  },

  handleOpenInfo() {
    if (!this.installedPluginInfo) return;
    const pluginHubKey = (this.selectedPlugin?.key || "").trim();
    const plugin = pluginHubKey
      ? {
          ...this.installedPluginInfo,
          pluginHub: {
            key: pluginHubKey,
            title:
              this.selectedPlugin?.title ||
              this.installedPluginInfo.display_name ||
              this.installedPluginInfo.name,
          },
        }
      : this.installedPluginInfo;
    pluginListStore.openPluginInfo(plugin);
  },

  handleOpenExecute() {
    if (this.installedPluginInfo) {
      pluginExecuteStore.open(this.installedPluginInfo);
    }
  },

  async handleDeletePlugin() {
    if (!this.installedPluginInfo) return;

    try {
      this.loading = true;
      this.loadingMessage = "Uninstalling plugin...";

      await pluginListStore.deletePlugin(this.installedPluginInfo);
      const currentPlugin = this.selectedPlugin ? Object.assign({}, this.selectedPlugin) : null;
      if (currentPlugin) {
        this.selectedPlugin = { ...currentPlugin, installed: false };
        this.installedPlugins = this.installedPlugins.filter(
          (key) => key !== currentPlugin["key"]
        );
      }
      this.installedPluginInfo = null;
    } finally {
      this.loading = false;
      this.loadingMessage = "";
    }
  },

  getIndexUrl(pluginKey) {
    if (!pluginKey) return "";
    return `https://github.com/agent0ai/a0-plugins/tree/main/plugins/${pluginKey}`;
  },

  getCommitShortHash(commitHash) {
    if (!commitHash || typeof commitHash !== "string") return "";
    return commitHash.slice(0, 7);
  },

  formatUserLocaleDateTime(value) {
    if (!value || typeof value !== "string") return "";

    const trimmedValue = value.trim();
    const hasExplicitTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(trimmedValue);
    let normalizedValue = /t/i.test(trimmedValue) ? trimmedValue : trimmedValue.replace(" ", "T");

    if (!hasExplicitTimezone && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(normalizedValue)) {
      normalizedValue = `${normalizedValue}Z`;
    }

    const date = new Date(normalizedValue);
    if (Number.isNaN(date.getTime())) return value;

    return new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(date);
  },

  getRepoCommitUrl(plugin, commitHash) {
    const githubUrl = (plugin?.github || "").trim().replace(/\.git$/i, "");
    if (!githubUrl || !commitHash) return "";
    return `${githubUrl}/commit/${commitHash}`;
  },

  getCurrentInstalledCommit() {
    return this.installedPluginInfo?.["current_commit"] || this.selectedPlugin?.["current_commit"] || "";
  },

  getCurrentInstalledVersion() {
    return this.installedPluginInfo?.["version"] || "";
  },

  getCurrentInstalledCommitTimestamp() {
    return this.installedPluginInfo?.["current_commit_timestamp"] || this.selectedPlugin?.["current_commit_timestamp"] || "";
  },

  getLatestPluginHubVersion() {
    return this.selectedPlugin?.["version"] || "";
  },

  getLatestPluginHubCommit() {
    return this.selectedPlugin?.["commit"] || "";
  },

  getLatestPluginHubCommitTimestamp() {
    return this.selectedPlugin?.["updated"] || "";
  },

  async handleUpdatePlugin() {
    const selectedPlugin = this["selectedPlugin"];
    const pluginRecord = selectedPlugin && typeof selectedPlugin === "object" ? selectedPlugin : {};
    const pluginKey = pluginRecord["key"] || pluginRecord["name"] || this.installedPluginInfo?.name || "";
    if (!pluginKey) {
      void toastFrontendError("Plugin name is missing", "Plugin Installer");
      return;
    }

    const confirmed = await showConfirmDialog({
      ...SECURITY_WARNING,
      extensionContext: {
        kind: "plugin_hub_plugin_install_warning",
        source: "plugin_installer",
        pluginKey,
        pluginTitle: pluginRecord["title"] || pluginKey,
        gitUrl: pluginRecord["github"] || "",
      },
    });
    if (!confirmed) return;

    try {
      this.loading = true;
      this.loadingMessage = "Updating";

      const data = await api.callJsonApi(PLUGIN_API, {
        action: "update_plugin",
        plugin_name: pluginKey,
      });

      if (!(data?.ok && data?.success)) {
        void toastFrontendError(data?.error || "Update failed", "Plugin Installer");
        return;
      }

      await this.fetchIndex();

      const installedPluginsSource = this["installedPlugins"];
      const installedPlugins = Array.isArray(installedPluginsSource) ? Array.from(installedPluginsSource) : [];
      if (!installedPlugins.some((installedKey) => installedKey === pluginKey)) {
        installedPlugins.push(String(pluginKey));
        Reflect.set(this, "installedPlugins", installedPlugins);
      }

      await this._refreshSelectedPluginState(pluginKey);
      this.refreshPluginList();

      toastFrontendSuccess(
        `Plugin "${data.title || data.plugin_name}" updated`,
        "Plugin Installer"
      );
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      void toastFrontendError(`Update error: ${message}`, "Plugin Installer");
    } finally {
      this.loading = false;
      this.loadingMessage = "";
    }
  },

  getThumbnailUrl(plugin) {
    if (!plugin) return null;
    if (plugin.thumbnail && typeof plugin.thumbnail === "string") return plugin.thumbnail;
    const rawBase = this._githubRawBase(plugin?.github);
    return rawBase ? `${rawBase}/main/thumbnail.png` : null;
  },

  getDetailThumbnailUrl() {
    return this.detailThumbnailUrl;
  },

  openScreenshot(url) {
    if (!url) return;
    const selectedPlugin = this.selectedPlugin || null;
    imageViewerStore.open(url, {
      name: selectedPlugin?.["title"] || selectedPlugin?.["key"] || "Plugin screenshot",
    });
  },

  getReportUrl(plugin) {
    const githubUrl = plugin?.github;
    if (!githubUrl || typeof githubUrl !== "string") return "";
    try {
      const url = new URL(githubUrl.trim().replace(/\.git$/i, ""));
      if (!url.hostname.includes("github.com")) return "";
      const parts = url.pathname.split("/").filter(Boolean);
      if (parts.length >= 1) {
        const username = parts[0];
        const contentUrl = encodeURIComponent(githubUrl);
        const report = encodeURIComponent(`${username} (user)`);
        return `https://github.com/contact/report-content?content_url=${contentUrl}&report=${report}`;
      }
    } catch (e) {
      // ignore
    }
    return "";
  },

  // ── Shared ───────────────────────────────────

  resetZip() {
    this.zipFile = null;
    this.zipFileName = "";
    this.result = null;
  },

  resetGit() {
    this.gitUrl = "";
    this.gitToken = "";
    this.result = null;
  },

  resetIndex() {
    this.search = "";
    this.page = 1;
    this.sortBy = "stars";
    this.browseFilter = "all";
    this.result = null;
    this.selectedPlugin = null;
  },

  /** Refresh related list views after installer/detail actions. */
  refreshPluginList() {
    const pluginHubActive = pluginListStore.activeTab === "pluginHub";
    if (pluginHubActive) {
      void this.fetchIndex();
    }
    pluginListStore.refresh();
  },

  truncate(text, max) {
    if (!text || text.length <= max) return text || "";
    return text.substring(0, max) + "...";
  },
};

const store = createStore("pluginInstallStore", model);
export { store };
