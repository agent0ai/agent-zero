import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
    // Connection state
    isConnected: false,
    isLoading: false,
    user: null,
    error: null,

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
        // Check URL params for OAuth result
        const params = new URLSearchParams(window.location.search);
        if (params.get("github_connected")) {
            window.history.replaceState({}, "", window.location.pathname);
        }
        if (params.get("github_error")) {
            this.error = `GitHub connection failed: ${params.get("github_error")}`;
            window.history.replaceState({}, "", window.location.pathname);
        }
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
            if (data.success && data.auth_url) {
                window.location.href = data.auth_url;
            } else {
                this.error = data.error || "Failed to start GitHub connection";
                this.isLoading = false;
            }
        } catch (e) {
            this.error = "Failed to connect to GitHub";
            this.isLoading = false;
        }
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

    async searchRepos(query) {
        this.filters.search = query;
        // For now, just filter client-side
        // Could add server-side search later via /github_search
    },

    async selectRepo(owner, repoName) {
        console.log("[GitHub] selectRepo called:", owner, repoName);
        this.isLoading = true;
        this.isRepoModalOpen = true;
        this.activeTab = "files";
        this.currentPath = "";
        this.repoFiles = [];
        this.error = null;

        try {
            console.log("[GitHub] Fetching repo details...");
            const data = await callJsonApi("/github_repo_detail", {
                owner: owner,
                repo: repoName,
            });

            console.log("[GitHub] Repo detail response:", data);

            if (data.error) {
                this.error = data.error;
                this.isRepoModalOpen = false;
                return;
            }

            this.repoDetails = data.repository;
            this.repoDetails.languages = data.languages;
            this.repoDetails.branches = data.branches;

            console.log("[GitHub] repoDetails set, loading files...");
            // Load root files
            await this.loadRepoFiles("");
            console.log("[GitHub] Files loaded, repoFiles:", this.repoFiles?.length);
        } catch (e) {
            console.error("[GitHub] selectRepo error:", e);
            this.error = "Failed to load repository details: " + e.message;
            this.isRepoModalOpen = false;
        } finally {
            this.isLoading = false;
        }
    },

    async loadRepoFiles(path) {
        if (!this.repoDetails) {
            console.warn("[GitHub] loadRepoFiles called without repoDetails");
            return;
        }

        this.isLoading = true;
        this.currentPath = path;
        this.error = null;

        try {
            console.log("[GitHub] Loading files for:", this.repoDetails.owner.login, this.repoDetails.name, "path:", path);
            const data = await callJsonApi("/github_contents", {
                owner: this.repoDetails.owner.login,
                repo: this.repoDetails.name,
                path: path,
            });

            console.log("[GitHub] Contents response:", data);

            if (data.error) {
                this.error = data.error;
                console.error("[GitHub] Error loading files:", data.error);
                return;
            }

            if (data.type === "directory") {
                this.repoFiles = data.contents || [];
                console.log("[GitHub] Loaded", this.repoFiles.length, "files");
            } else {
                // Single file - could display content
                this.repoFiles = [];
                console.log("[GitHub] Response was a file, not directory");
            }
        } catch (e) {
            this.error = "Failed to load files: " + e.message;
            console.error("[GitHub] Exception loading files:", e);
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

    // Utility functions
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
