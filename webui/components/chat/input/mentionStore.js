import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const MAX_MENTIONS = 10;

const model = {
  // UI state
  isOpen: false,
  activeTab: "repos", // 'repos' | 'files' | 'chats'
  searchQuery: "",
  selectedIndex: 0,
  _atPosition: -1,
  _initialized: false,

  // Data sources
  repos: [],
  reposLoading: false,
  files: [],
  filesLoading: false,
  chats: [],
  chatsLoading: false,

  // Selected mentions (all types, shared array)
  mentions: [],

  // Limits
  maxMentions: MAX_MENTIONS,

  get remainingSlots() {
    return this.maxMentions - this.mentions.length;
  },

  get isFull() {
    return this.mentions.length >= this.maxMentions;
  },

  // Filtered results for active tab
  get filteredResults() {
    const search = this.searchQuery.toLowerCase();
    if (this.activeTab === "repos") {
      return this._filterRepos(search);
    } else if (this.activeTab === "files") {
      return this._filterFiles(search);
    } else if (this.activeTab === "chats") {
      return this._filterChats(search);
    }
    return [];
  },

  get isLoading() {
    if (this.activeTab === "repos") return this.reposLoading;
    if (this.activeTab === "files") return this.filesLoading;
    if (this.activeTab === "chats") return this.chatsLoading;
    return false;
  },

  get hasData() {
    if (this.activeTab === "repos") return this.repos.length > 0;
    if (this.activeTab === "files") return this.files.length > 0;
    if (this.activeTab === "chats") return this.chats.length > 0;
    return false;
  },

  get emptyMessage() {
    if (this.isLoading) return "";
    if (!this.hasData) {
      if (this.activeTab === "repos") return "No repositories found";
      if (this.activeTab === "files") return "Type to search files";
      if (this.activeTab === "chats") return "No chats found";
    }
    if (this.filteredResults.length === 0) return "No matches";
    return "";
  },

  // Initialize
  init() {
    if (this._initialized) return;
    this._initialized = true;
    try {
      const saved = localStorage.getItem("mentions");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          // Filter out uploaded file mentions (content too large for localStorage)
          this.mentions = parsed.filter((m) => m.type !== "file" || m.source !== "upload");
        }
      }
    } catch (e) {
      // Ignore corrupt localStorage
    }
  },

  // --- Tab switching ---

  setTab(tab) {
    this.activeTab = tab;
    this.searchQuery = "";
    this.selectedIndex = 0;
    this._loadTabData();
  },

  _loadTabData() {
    if (this.activeTab === "repos" && this.repos.length === 0 && !this.reposLoading) {
      this.fetchRepos();
    } else if (this.activeTab === "chats" && this.chats.length === 0 && !this.chatsLoading) {
      this.fetchChats();
    }
    // Files tab: search-driven, no preload needed
  },

  // --- Data fetching ---

  async fetchRepos() {
    if (this.reposLoading) return;
    this.reposLoading = true;
    try {
      const data = await callJsonApi("/github_repos", {
        page: 1,
        per_page: 100,
        type: "all",
        sort: "updated",
      });
      if (data.error) {
        console.error("[mentions] Failed to fetch repos:", data.error);
        return;
      }
      this.repos = (data.repositories || []).map((repo) => ({
        owner: repo.owner?.login || repo.owner,
        repo: repo.name,
        full_name: repo.full_name,
        description: repo.description || "",
      }));
    } catch (e) {
      console.error("[mentions] Error fetching repos:", e);
    } finally {
      this.reposLoading = false;
    }
  },

  async searchFiles(query) {
    if (!query || query.length < 2) {
      this.files = [];
      return;
    }
    this.filesLoading = true;
    try {
      const data = await callJsonApi("/file_search", { query });
      this.files = data.results || [];

      // Also include files from already-mentioned repos
      const repoMentions = this.mentions.filter((m) => m.type === "repo");
      // GitHub repo files are available via the repo tree already fetched
      // We append them as a separate source for search
    } catch (e) {
      console.error("[mentions] Error searching files:", e);
    } finally {
      this.filesLoading = false;
    }
  },

  async fetchChats() {
    if (this.chatsLoading) return;
    this.chatsLoading = true;
    try {
      // Chats are available from the chats store (populated by polling)
      const chatsStore = window.Alpine?.store("chats");
      if (chatsStore && chatsStore.contexts) {
        this.chats = chatsStore.contexts.map((ctx) => ({
          context_id: ctx.id,
          title: ctx.name || ctx.id,
          created_at: ctx.created_at || 0,
        }));
      }
    } catch (e) {
      console.error("[mentions] Error fetching chats:", e);
    } finally {
      this.chatsLoading = false;
    }
  },

  // --- Filtering ---

  _filterRepos(search) {
    if (!search) return this.repos;
    return this.repos.filter((repo) => {
      const fullName = (repo.full_name || "").toLowerCase();
      const description = (repo.description || "").toLowerCase();
      return fullName.includes(search) || description.includes(search);
    });
  },

  _filterFiles(search) {
    if (!search) return this.files;
    return this.files.filter((file) => {
      const name = (file.name || "").toLowerCase();
      const path = (file.path || "").toLowerCase();
      return name.includes(search) || path.includes(search);
    });
  },

  _filterChats(search) {
    // Exclude current chat
    const currentCtx = window.Alpine?.store("chats")?.selected || "";
    let filtered = this.chats.filter((chat) => chat.context_id !== currentCtx);
    if (!search) return filtered;
    return filtered.filter((chat) => {
      const title = (chat.title || "").toLowerCase();
      return title.includes(search);
    });
  },

  // --- Dropdown control ---

  openDropdown() {
    this.isOpen = true;
    this.selectedIndex = 0;
    this._loadTabData();
  },

  closeDropdown() {
    this.isOpen = false;
    this.searchQuery = "";
    this.selectedIndex = 0;
    this._atPosition = -1;
  },

  // --- Selection ---

  addMention(item) {
    if (this.isFull) return;

    let mention;
    if (this.activeTab === "repos") {
      // Dedupe by full_name
      if (this.mentions.some((m) => m.type === "repo" && m.full_name === item.full_name)) {
        this.removeAtFromInput();
        this.closeDropdown();
        return;
      }
      mention = {
        type: "repo",
        owner: item.owner,
        repo: item.repo,
        full_name: item.full_name,
      };
    } else if (this.activeTab === "files") {
      // Dedupe by path + source
      const key = `${item.source}:${item.path}`;
      if (this.mentions.some((m) => m.type === "file" && `${m.source}:${m.path}` === key)) {
        this.removeAtFromInput();
        this.closeDropdown();
        return;
      }
      mention = {
        type: "file",
        path: item.path,
        name: item.name,
        source: item.source,
        size: item.size,
      };
      // For GitHub files, include repo
      if (item.repo) mention.repo = item.repo;
    } else if (this.activeTab === "chats") {
      // Dedupe by context_id
      if (this.mentions.some((m) => m.type === "chat" && m.context_id === item.context_id)) {
        this.removeAtFromInput();
        this.closeDropdown();
        return;
      }
      mention = {
        type: "chat",
        context_id: item.context_id,
        title: item.title,
      };
    }

    if (mention) {
      this.mentions.push(mention);
      this._persistMentions();
    }

    this.removeAtFromInput();
    this.closeDropdown();
  },

  addUploadedFile(file) {
    if (this.isFull) return;

    const reader = new FileReader();
    reader.onload = () => {
      const content = reader.result;
      const mention = {
        type: "file",
        path: file.name,
        name: file.name,
        source: "upload",
        size: file.size,
        content: content,
      };
      this.mentions.push(mention);
      this._persistMentions();
    };
    reader.readAsText(file);
  },

  removeMention(index) {
    if (index >= 0 && index < this.mentions.length) {
      this.mentions.splice(index, 1);
      this._persistMentions();
    }
  },

  clearMentions() {
    this.mentions = [];
    this._persistMentions();
  },

  _persistMentions() {
    try {
      // Exclude uploaded file content from localStorage (too large)
      const toSave = this.mentions.map((m) => {
        if (m.type === "file" && m.source === "upload") {
          const { content, ...rest } = m;
          return rest;
        }
        return m;
      });
      localStorage.setItem("mentions", JSON.stringify(toSave));
    } catch (e) {
      // Ignore storage errors
    }
  },

  // --- Keyboard navigation ---

  moveSelection(delta) {
    const results = this.filteredResults;
    if (results.length === 0) return;
    let newIndex = this.selectedIndex + delta;
    if (newIndex < 0) newIndex = results.length - 1;
    else if (newIndex >= results.length) newIndex = 0;
    this.selectedIndex = newIndex;
  },

  selectCurrent() {
    const results = this.filteredResults;
    if (results.length > 0 && this.selectedIndex < results.length) {
      this.addMention(results[this.selectedIndex]);
    }
  },

  // --- Input detection ---

  handleInput(event) {
    const textarea = event.target;
    const value = textarea.value;
    const cursorPos = textarea.selectionStart;

    if (cursorPos > 0 && value[cursorPos - 1] === "@") {
      const charBefore = cursorPos > 1 ? value[cursorPos - 2] : null;
      const isWordBoundary =
        charBefore === null ||
        charBefore === " " ||
        charBefore === "\n" ||
        charBefore === "\t";

      if (isWordBoundary) {
        this._atPosition = cursorPos - 1;
        this.openDropdown();
      }
    }

    // Live file search when on Files tab and dropdown is open
    if (this.isOpen && this.activeTab === "files") {
      // Debounced search handled via searchQuery watcher in dropdown
    }
  },

  removeAtFromInput() {
    if (this._atPosition < 0) return;
    const textarea = document.getElementById("chat-input");
    if (!textarea) return;

    const value = textarea.value;
    const before = value.substring(0, this._atPosition);
    const after = value.substring(this._atPosition + 1);

    textarea.value = before + after;
    textarea.selectionStart = textarea.selectionEnd = this._atPosition;
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
    this._atPosition = -1;
  },

  // --- Helpers for backward compat ---

  // Returns mentions in the old repo_mentions format (for backward compat during migration)
  getRepoMentions() {
    return this.mentions
      .filter((m) => m.type === "repo")
      .map((m) => ({ owner: m.owner, repo: m.repo, full_name: m.full_name }));
  },
};

const store = createStore("mentions", model);

export { store };
