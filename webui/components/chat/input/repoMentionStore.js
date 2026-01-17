import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
  // State
  repos: [],
  mentions: [],
  showDropdown: false,
  filterText: "",
  selectedIndex: 0,
  loading: false,
  _initialized: false,
  _atPosition: -1, // Track where @ was typed for removal

  // Computed: filter repos by filterText (fuzzy match on full_name and description)
  get filteredRepos() {
    if (!this.filterText) {
      return this.repos;
    }
    const search = this.filterText.toLowerCase();
    return this.repos.filter((repo) => {
      const fullName = (repo.full_name || "").toLowerCase();
      const description = (repo.description || "").toLowerCase();
      return fullName.includes(search) || description.includes(search);
    });
  },

  // Computed: true if repos loaded or loading
  get isConnected() {
    return this.loading || this.repos.length > 0;
  },

  // Initialize store (guarded)
  init() {
    if (this._initialized) return;
    this._initialized = true;
    // No additional initialization needed
  },

  // Fetch repos from API and cache results
  async fetchRepos() {
    if (this.loading) return;
    this.loading = true;

    try {
      const data = await callJsonApi("/github_repos", {
        page: 1,
        per_page: 100,
        type: "all",
        sort: "updated",
      });

      if (data.error) {
        console.error("[repoMention] Failed to fetch repos:", data.error);
        return;
      }

      this.repos = (data.repositories || []).map((repo) => ({
        owner: repo.owner?.login || repo.owner,
        repo: repo.name,
        full_name: repo.full_name,
        description: repo.description || "",
      }));
    } catch (e) {
      console.error("[repoMention] Error fetching repos:", e);
    } finally {
      this.loading = false;
    }
  },

  // Open dropdown and trigger fetch if needed
  openDropdown() {
    this.showDropdown = true;
    this.selectedIndex = 0;
    if (this.repos.length === 0 && !this.loading) {
      this.fetchRepos();
    }
  },

  // Close dropdown and reset filter
  closeDropdown() {
    this.showDropdown = false;
    this.filterText = "";
    this.selectedIndex = 0;
    this._atPosition = -1; // Reset @ position
  },

  // Add repo to mentions (dedupe by full_name)
  addMention(repo) {
    const exists = this.mentions.some((m) => m.full_name === repo.full_name);
    if (!exists) {
      this.mentions.push({
        owner: repo.owner,
        repo: repo.repo,
        full_name: repo.full_name,
      });
    }
    this.removeAtFromInput(); // Remove the @ that triggered the dropdown
    this.closeDropdown();
  },

  // Remove mention by index
  removeMention(index) {
    if (index >= 0 && index < this.mentions.length) {
      this.mentions.splice(index, 1);
    }
  },

  // Clear all mentions
  clearMentions() {
    this.mentions = [];
  },

  // Move selection for keyboard navigation
  moveSelection(delta) {
    const filtered = this.filteredRepos;
    if (filtered.length === 0) return;

    let newIndex = this.selectedIndex + delta;
    if (newIndex < 0) {
      newIndex = filtered.length - 1;
    } else if (newIndex >= filtered.length) {
      newIndex = 0;
    }
    this.selectedIndex = newIndex;
  },

  // Select the currently highlighted repo
  selectCurrent() {
    const filtered = this.filteredRepos;
    if (filtered.length > 0 && this.selectedIndex < filtered.length) {
      this.addMention(filtered[this.selectedIndex]);
    }
  },

  // Handle input event from textarea to detect @ mentions
  handleInput(event) {
    const textarea = event.target;
    const value = textarea.value;
    const cursorPos = textarea.selectionStart;

    // Check if the character just typed was @
    if (cursorPos > 0 && value[cursorPos - 1] === "@") {
      // Check if @ is at a word boundary (start, after space, or after newline)
      const charBefore = cursorPos > 1 ? value[cursorPos - 2] : null;
      const isWordBoundary =
        charBefore === null ||
        charBefore === " " ||
        charBefore === "\n" ||
        charBefore === "\t";

      if (isWordBoundary) {
        this._atPosition = cursorPos - 1; // Store position of @
        this.openDropdown();
      }
    }
  },

  // Remove the @ character from textarea when a repo is selected
  removeAtFromInput() {
    if (this._atPosition < 0) return;

    const textarea = document.getElementById("chat-input");
    if (!textarea) return;

    const value = textarea.value;
    const before = value.substring(0, this._atPosition);
    const after = value.substring(this._atPosition + 1); // Skip the @

    textarea.value = before + after;
    textarea.selectionStart = textarea.selectionEnd = this._atPosition;

    // Trigger input event to adjust height
    textarea.dispatchEvent(new Event("input", { bubbles: true }));

    this._atPosition = -1;
  },
};

const store = createStore("repoMention", model);

export { store };
