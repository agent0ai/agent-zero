import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
    // Connection state
    isConnected: false,
    isLoading: false,
    user: null,
    error: null,

    // Device flow state
    deviceFlow: null, // { flow_id, user_code, verification_uri, interval }
    _pollTimer: null,

    // Repository list state
    repos: [],
    filters: {
        search: "",
        type: "all",
        sort: "updated",
    },
    pagination: {
        page: 1,
        perPage: 30,
        hasNext: false,
        hasPrev: false,
    },

    // Repository detail state
    isRepoModalOpen: false,
    repoDetails: null,
    repoFiles: [],
    currentPath: "",
    activeTab: "files",

    // Computed: filtered repos based on search
    get filteredRepos() {
        if (!this.filters.search) {
            return this.repos;
        }
        const search = this.filters.search.toLowerCase();
        return this.repos.filter(
            (repo) =>
                repo.name.toLowerCase().includes(search) ||
                (repo.description && repo.description.toLowerCase().includes(search))
        );
    },

    init() {
        this.checkConnection();
    },

    async checkConnection() {
        try {
            const data = await callJsonApi("/github_user", {});
            if (data.connected) {
                this.isConnected = true;
                this.user = data.user;
                // Auto-load repos when connected
                this.loadRepos();
            } else {
                this.isConnected = false;
                this.user = null;
            }
        } catch (e) {
            this.isConnected = false;
            this.user = null;
        }
    },

    async connect() {
        this.error = null;
        this.isLoading = true;
        try {
            const data = await callJsonApi("/github_oauth", {});
            if (data.success) {
                this.deviceFlow = {
                    flow_id: data.flow_id,
                    user_code: data.user_code,
                    verification_uri: data.verification_uri,
                    interval: data.interval || 5,
                };
                this.startPolling();
            } else {
                this.error = data.error || "Failed to start GitHub connection";
            }
        } catch (e) {
            this.error = "Failed to connect to GitHub";
        } finally {
            this.isLoading = false;
        }
    },

    startPolling() {
        if (!this.deviceFlow) return;
        this.stopPolling();
        const interval = (this.deviceFlow.interval || 5) * 1000;
        this._pollTimer = setInterval(() => this.pollDeviceFlow(), interval);
    },

    stopPolling() {
        if (this._pollTimer) {
            clearInterval(this._pollTimer);
            this._pollTimer = null;
        }
    },

    async pollDeviceFlow() {
        if (!this.deviceFlow) {
            this.stopPolling();
            return;
        }

        try {
            const data = await callJsonApi("/github_callback", {
                flow_id: this.deviceFlow.flow_id,
            });

            if (data.status === "complete") {
                this.stopPolling();
                this.deviceFlow = null;
                this.isConnected = true;
                this.error = null;
                await this.checkConnection();
            } else if (data.status === "error") {
                this.stopPolling();
                this.deviceFlow = null;
                this.error = data.error || "GitHub authorization failed";
            } else if (data.status === "pending") {
                // If GitHub sent a new interval (slow_down), restart polling with it
                if (data.interval && data.interval !== this.deviceFlow.interval) {
                    this.deviceFlow.interval = data.interval;
                    this.startPolling();
                }
            }
        } catch (e) {
            this.stopPolling();
            this.deviceFlow = null;
            this.error = "Failed to check authorization status";
        }
    },

    cancelDeviceFlow() {
        this.stopPolling();
        this.deviceFlow = null;
        this.error = null;
    },

    async copyCode() {
        if (!this.deviceFlow?.user_code) return;
        try {
            await navigator.clipboard.writeText(this.deviceFlow.user_code);
        } catch (e) {
            // Fallback: select text in the code element for manual copy
        }
    },

    cleanup() {
        this.stopPolling();
    },

    async disconnect() {
        try {
            await callJsonApi("/github_disconnect", {});
            this.isConnected = false;
            this.user = null;
            this.repos = [];
            this.repoDetails = null;
            this.isRepoModalOpen = false;
        } catch (e) {
            this.error = "Failed to disconnect";
        }
    },

    async loadRepos(page = 1) {
        this.isLoading = true;
        this.error = null;
        this.pagination.page = page;

        try {
            const data = await callJsonApi("/github_repos", {
                page: page,
                per_page: this.pagination.perPage,
                type: this.filters.type,
                sort: this.filters.sort,
            });

            if (data.error) {
                this.error = data.error;
                return;
            }

            this.repos = data.repositories || [];
            this.pagination.hasNext = data.has_next || false;
            this.pagination.hasPrev = data.has_prev || false;
        } catch (e) {
            this.error = "Failed to load repositories";
        } finally {
            this.isLoading = false;
        }
    },

    searchRepos(query) {
        this.filters.search = query;
    },

    async selectRepo(owner, repoName) {
        this.isLoading = true;
        this.isRepoModalOpen = true;
        this.activeTab = "files";
        this.currentPath = "";
        this.repoFiles = [];
        this.error = null;

        try {
            const data = await callJsonApi("/github_repo_detail", {
                owner: owner,
                repo: repoName,
            });

            if (data.error) {
                this.error = data.error;
                this.isRepoModalOpen = false;
                return;
            }

            this.repoDetails = data.repository;
            this.repoDetails.languages = data.languages;
            this.repoDetails.branches = data.branches;

            await this.loadRepoFiles("");
        } catch (e) {
            this.error = "Failed to load repository details: " + e.message;
            this.isRepoModalOpen = false;
        } finally {
            this.isLoading = false;
        }
    },

    async loadRepoFiles(path) {
        if (!this.repoDetails) return;

        this.isLoading = true;
        this.currentPath = path;
        this.error = null;

        try {
            const data = await callJsonApi("/github_contents", {
                owner: this.repoDetails.owner.login,
                repo: this.repoDetails.name,
                path: path,
            });

            if (data.error) {
                this.error = data.error;
                return;
            }

            if (data.type === "directory") {
                this.repoFiles = data.contents || [];
            } else {
                this.repoFiles = [];
            }
        } catch (e) {
            this.error = "Failed to load files: " + e.message;
        } finally {
            this.isLoading = false;
        }
    },

    navigateToPath(path) {
        this.loadRepoFiles(path);
    },

    navigateUp() {
        const parts = this.currentPath.split("/").filter((p) => p);
        parts.pop();
        this.loadRepoFiles(parts.join("/"));
    },

    closeRepoModal() {
        this.isRepoModalOpen = false;
        this.repoDetails = null;
        this.repoFiles = [];
        this.currentPath = "";
    },

    formatTime(dateString) {
        if (!dateString) return "";
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return "today";
        if (diffDays === 1) return "yesterday";
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
        return `${Math.floor(diffDays / 365)} years ago`;
    },

    formatSize(bytes) {
        if (!bytes) return "";
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    },
};

const store = createStore("github", model);

export { store };
