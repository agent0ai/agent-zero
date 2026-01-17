import { createStore } from "/js/AlpineStore.js";
import { getContext } from "/index.js";
import * as API from "/js/api.js";
import { openModal, closeModal } from "/js/modals.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

// Helper function for toasts
function justToast(text, type = "info", timeout = 5000) {
  notificationStore.addFrontendToastOnly(type, text, "", timeout / 1000);
}

// Memory Dashboard Store
const memoryDashboardStore = {
  // Data
  memories: [],
  currentPage: 1,
  itemsPerPage: 10,

  // State
  loading: false,
  loadingSubdirs: false,
  initializingMemory: false,
  error: null,
  message: null,

  // Memory subdirectories
  memorySubdirs: [],
  selectedMemorySubdir: "default",
  memoryInitialized: {}, // Track which subdirs have been initialized

  // Search and filters
  searchQuery: "",
  areaFilter: "",
  threshold: parseFloat(
    localStorage.getItem("memoryDashboard_threshold") || "0.6"
  ),
  limit: parseInt(localStorage.getItem("memoryDashboard_limit") || "1000"),

  // Stats
  totalCount: 0,
  totalDbCount: 0,
  knowledgeCount: 0,
  conversationCount: 0,
  areasCount: {},

  // Memory detail modal (standard modal approach)
  detailMemory: null,
  editMode: false,
  editMemoryBackup: null,

  // Polling
  pollingInterval: null,
  pollingEnabled: false,

  async openModal() {
    await openModal("settings/memory/memory-dashboard.html");
  },

  init() {
    this.initialize();
  },

  async onOpen() {
    await this.getCurrentMemorySubdir();
    await this.loadMemorySubdirs();
    await this.searchMemories();
    // Start polling for live updates as soon as dashboard is open
    this.startPolling();
  },

  async initialize() {
    // Reset state when opening (but keep directory from context)
    this.currentPage = 1;
    this.searchQuery = "";
    this.areaFilter = "";

    // // Get current memory subdirectory from application context
    // await this.getCurrentMemorySubdir();

    // await this.loadMemorySubdirs();

    // // Automatically search with selected subdirectory
    // if (this.selectedMemorySubdir) {
    //   await this.searchMemories();
    // }

    // // Start polling for live updates as soon as dashboard is open
    // this.startPolling();
  },

  async getCurrentMemorySubdir() {
    try {
      // Try to get current memory subdirectory from the backend
      const response = await API.callJsonApi("memory_dashboard", {
        action: "get_current_memory_subdir",
        context_id: getContext(),
      });

      if (response.success && response.memory_subdir) {
        this.selectedMemorySubdir = response.memory_subdir;
      } else {
        // Fallback to default
        this.selectedMemorySubdir = "default";
      }
    } catch (error) {
      console.error("Failed to get current memory subdirectory:", error);
      this.selectedMemorySubdir = "default";
    }
  },

  async loadMemorySubdirs() {
    this.loadingSubdirs = true;
    this.error = null;

    try {
      const response = await API.callJsonApi("memory_dashboard", {
        action: "get_memory_subdirs",
      });

      if (response.success) {
        let subdirs = response.subdirs || ["default"];

        // Sort alphabetically but ensure "default" is always first
        subdirs = subdirs.filter((dir) => dir !== "default").sort();
        if (response.subdirs && response.subdirs.includes("default")) {
          subdirs.unshift("default");
        } else {
          subdirs.unshift("default");
        }

        this.memorySubdirs = subdirs;

        // Ensure the currently selected subdirectory exists in the list
        if (!this.memorySubdirs.includes(this.selectedMemorySubdir)) {
          this.selectedMemorySubdir = "default";
        }
      } else {
        this.error = response.error || "Failed to load memory subdirectories";
        this.memorySubdirs = ["default"];
        this.selectedMemorySubdir = "default";
      }
    } catch (error) {
      this.error = error.message || "Failed to load memory subdirectories";
      this.memorySubdirs = ["default"];
      // Only fallback to default if current selection is not available
      if (!this.memorySubdirs.includes(this.selectedMemorySubdir)) {
        this.selectedMemorySubdir = "default";
      }
      console.error("Memory subdirectory loading error:", error);
    } finally {
      this.loadingSubdirs = false;
    }
  },

  async searchMemories(silent = false) {
    // Save limit to localStorage for persistence
    localStorage.setItem("memoryDashboard_limit", this.limit.toString());
    localStorage.setItem(
      "memoryDashboard_threshold",
      this.threshold.toString()
    );

    if (!silent) {
      this.loading = true;
      this.error = null;
      this.message = null;

      // Check if this memory subdirectory needs initialization
      if (!this.memoryInitialized[this.selectedMemorySubdir]) {
        this.initializingMemory = true;
      }
    }

    try {
      const response = await API.callJsonApi("memory_dashboard", {
        action: "search",
        memory_subdir: this.selectedMemorySubdir,
        area: this.areaFilter,
        search: this.searchQuery,
        limit: this.limit,
        threshold: this.threshold,
      });

      if (response.success) {
        // Preserve existing selections when updating memories during polling
        const existingSelections = {};
        if (silent && this.memories) {
          // Build a map of existing selections by memory ID
          this.memories.forEach((memory) => {
            if (memory.selected) {
              existingSelections[memory.id] = true;
            }
          });
        }

        // Add selected property to each memory item for mass selection
        this.memories = (response.memories || []).map((memory) => ({
          ...memory,
          selected: existingSelections[memory.id] || false,
        }));
        this.totalCount = response.total_count || 0;
        this.totalDbCount = response.total_db_count || 0;
        this.knowledgeCount = response.knowledge_count || 0;
        this.conversationCount = response.conversation_count || 0;

        if (!silent) {
          this.message = response.message || null;
          this.currentPage = 1; // Reset to first page when loading new data
        } else {
          // For silent updates, adjust current page if it exceeds available pages
          if (this.currentPage > this.totalPages && this.totalPages > 0) {
            this.currentPage = this.totalPages;
          }
        }

        // Mark this subdirectory as initialized
        this.memoryInitialized[this.selectedMemorySubdir] = true;
      } else {
        if (!silent) {
          this.error = response.error || "Failed to search memories";
          this.memories = [];
          this.message = null;
        } else {
          // For silent updates, just log the error but don't break the UI
          console.warn("Memory dashboard polling failed:", response.error);
        }
      }
    } catch (error) {
      if (!silent) {
        this.error = error.message || "Failed to search memories";
        this.memories = [];
        this.message = null;
        console.error("Memory search error:", error);
      } else {
        // For silent updates, just log the error but don't break the UI
        console.warn("Memory dashboard polling error:", error);
      }
    } finally {
      if (!silent) {
        this.loading = false;
        this.initializingMemory = false;
      }
    }
  },

  async clearSearch() {
    this.areaFilter = "";
    this.searchQuery = "";
    this.currentPage = 1;

    // Immediately trigger a new search with cleared filters
    await this.searchMemories();
  },

  async onMemorySubdirChange() {
    // Clear current results when subdirectory changes
    await this.clearSearch(); // Polling continues with new subdirectory
  },

  // Pagination
  get totalPages() {
    return Math.ceil(this.memories.length / this.itemsPerPage);
  },

  get paginatedMemories() {
    const start = (this.currentPage - 1) * this.itemsPerPage;
    const end = start + this.itemsPerPage;
    return this.memories.slice(start, end);
  },

  goToPage(page) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
    }
  },

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
    }
  },

  prevPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
    }
  },

  // Mass selection
  get selectedMemories() {
    return this.memories.filter((memory) => memory.selected);
  },

  get selectedCount() {
    return this.selectedMemories.length;
  },

  get allSelected() {
    return (
      this.memories.length > 0 &&
      this.memories.every((memory) => memory.selected)
    );
  },

  get someSelected() {
    return this.memories.some((memory) => memory.selected);
  },

  toggleSelectAll() {
    const shouldSelectAll = !this.allSelected;
    this.memories.forEach((memory) => {
      memory.selected = shouldSelectAll;
    });
  },

  clearSelection() {
    this.memories.forEach((memory) => {
      memory.selected = false;
    });
  },

  // Bulk operations
  async bulkDeleteMemories() {
    const selectedMemories = this.selectedMemories;
    if (selectedMemories.length === 0) return;

    const confirmMessage = `Are you sure you want to delete ${selectedMemories.length} selected memories? This cannot be undone.`;
    if (!confirm(confirmMessage)) return;

    try {
      this.loading = true;
      const response = await API.callJsonApi("memory_dashboard", {
        action: "bulk_delete",
        memory_subdir: this.selectedMemorySubdir,
        memory_ids: selectedMemories.map((memory) => memory.id),
      });

      if (response.success) {
        justToast(
          `Successfully deleted ${selectedMemories.length} memories`,
          "success"
        );

        // Let polling refresh the data instead of manual manipulation
        // Trigger an immediate refresh to get updated state from backend
        await this.searchMemories(true); // silent refresh
      } else {
        justToast(
          response.error || "Failed to delete selected memories",
          "error"
        );
      }
    } catch (error) {
      justToast(error.message || "Failed to delete selected memories", "error");
    } finally {
      this.loading = false;
    }
  },

  // Helper method to format a complete memory with all metadata
  formatMemoryForCopy(memory) {
    let formatted = `=== Memory ID: ${memory.id} ===
Area: ${memory.area}
Timestamp: ${this.formatTimestamp(memory.timestamp)}
Source: ${memory.knowledge_source ? "Knowledge" : "Conversation"}
${memory.source_file ? `File: ${memory.source_file}` : ""}
${
  memory.tags && memory.tags.length > 0 ? `Tags: ${memory.tags.join(", ")}` : ""
}`;

    // Add custom metadata if present
    if (
      memory.metadata &&
      typeof memory.metadata === "object" &&
      Object.keys(memory.metadata).length > 0
    ) {
      formatted += "\n\nMetadata:";
      for (const [key, value] of Object.entries(memory.metadata)) {
        const displayValue =
          typeof value === "object" ? JSON.stringify(value, null, 2) : value;
        formatted += `\n${key}: ${displayValue}`;
      }
    }

    formatted += `\n\nContent:
${memory.content_full}

`;
    return formatted;
  },

  bulkCopyMemories() {
    const selectedMemories = this.selectedMemories;
    if (selectedMemories.length === 0) return;

    const content = selectedMemories
      .map((memory) => this.formatMemoryForCopy(memory))
      .join("\n");

    this.copyToClipboard(content, false);
    justToast(
      `Copied ${selectedMemories.length} memories with metadata to clipboard`,
      "success"
    );
  },

  bulkExportMemories() {
    const selectedMemories = this.selectedMemories;
    if (selectedMemories.length === 0) return;

    const exportData = {
      export_timestamp: new Date().toISOString(),
      memory_subdir: this.selectedMemorySubdir,
      total_memories: selectedMemories.length,
      memories: selectedMemories.map((memory) => ({
        id: memory.id,
        area: memory.area,
        timestamp: memory.timestamp,
        content: memory.content_full,
        tags: memory.tags || [],
        knowledge_source: memory.knowledge_source,
        source_file: memory.source_file || null,
        metadata: memory.metadata || {},
      })),
    };

    const jsonString = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const timestamp = new Date().toISOString().split("T")[0];
    const filename = `memories_${this.selectedMemorySubdir}_selected_${selectedMemories.length}_${timestamp}.json`;

    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    justToast(
      `Exported ${selectedMemories.length} selected memories to ${filename}`,
      "success"
    );
  },

  // Memory detail modal (standard approach)
  showMemoryDetails(memory) {
    this.detailMemory = memory;
    this.editMode = false;
    this.editMemoryBackup = null;
    // Use global modal system
    openModal("settings/memory/memory-detail-modal.html");
  },

  closeMemoryDetails() {
    this.detailMemory = null;
  },

  // Utilities
  formatTimestamp(timestamp, compact = false) {
    if (!timestamp || timestamp === "unknown") {
      return "Unknown";
    }

    const date = new Date(timestamp);
    if (isNaN(date.getTime())) {
      return "Invalid Date";
    }

    if (compact) {
      // For table display: MM/DD HH:mm
      return (
        date.toLocaleDateString("en-US", {
          month: "2-digit",
          day: "2-digit",
        }) +
        " " +
        date.toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
        })
      );
    } else {
      // For details: Full format
      return (
        date.toLocaleDateString("en-US", {
          year: "numeric",
          month: "long",
          day: "numeric",
        }) +
        " at " +
        date.toLocaleTimeString("en-US", {
          hour12: true,
          hour: "numeric",
          minute: "2-digit",
        })
      );
    }
  },

  formatTags(tags) {
    if (!Array.isArray(tags) || tags.length === 0) return "None";
    return tags.join(", ");
  },

  getAreaColor(area) {
    const colors = {
      main: "#3b82f6",
      fragments: "#10b981",
      solutions: "#8b5cf6",
      instruments: "#f59e0b",
    };
    return colors[area] || "#6c757d";
  },

  copyToClipboard(text, toastSuccess = true) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard
        .writeText(text)
        .then(() => {
          if(toastSuccess)
            justToast("Copied to clipboard!", "success");
        })
        .catch((err) => {
          console.error("Clipboard copy failed:", err);
          this.fallbackCopyToClipboard(text, toastSuccess);
        });
    } else {
      this.fallbackCopyToClipboard(text, toastSuccess);
    }
  },

  fallbackCopyToClipboard(text, toastSuccess = true) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand("copy");
      if(toastSuccess)
        justToast("Copied to clipboard!", "success");
    } catch (err) {
      console.error("Fallback clipboard copy failed:", err);
      justToast("Failed to copy to clipboard", "error");
    }
    document.body.removeChild(textArea);
  },

  async deleteMemory(memory) {
    if (
      !confirm(
        `Are you sure you want to delete this memory from ${memory.area}?`
      )
    ) {
      return;
    }

    try {
      // Check if this is the memory currently being viewed in detail modal
      const isViewingThisMemory =
        this.detailMemory && this.detailMemory.id === memory.id;

      const response = await API.callJsonApi("memory_dashboard", {
        action: "delete",
        memory_subdir: this.selectedMemorySubdir,
        memory_id: memory.id,
      });

      if (response.success) {
        justToast("Memory deleted successfully", "success");

        // If we were viewing this memory in detail modal, close it
        if (isViewingThisMemory) {
          this.detailMemory = null;
          closeModal(); // Close the detail modal
        }

        // Let polling refresh the data instead of manual manipulation
        // Trigger an immediate refresh to get updated state from backend
        await this.searchMemories(true); // silent refresh
      } else {
        justToast(`Failed to delete memory: ${response.error}`, "error");
      }
    } catch (error) {
      console.error("Memory deletion error:", error);
      justToast("Failed to delete memory", "error");
    }
  },

  exportMemories() {
    if (this.memories.length === 0) {
      justToast("No memories to export", "warning");
      return;
    }

    try {
      const exportData = {
        memory_subdir: this.selectedMemorySubdir,
        export_timestamp: new Date().toISOString(),
        total_memories: this.memories.length,
        search_query: this.searchQuery,
        area_filter: this.areaFilter,
        memories: this.memories.map((memory) => ({
          id: memory.id,
          area: memory.area,
          timestamp: memory.timestamp,
          content: memory.content_full,
          metadata: memory.metadata,
        })),
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `memory-export-${this.selectedMemorySubdir}-${
        new Date().toISOString().split("T")[0]
      }.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      justToast("Memory export completed", "success");
    } catch (error) {
      console.error("Memory export error:", error);
      justToast("Failed to export memories", "error");
    }
  },

  startPolling() {
    if (!this.pollingEnabled || this.pollingInterval) {
      return; // Already polling or disabled
    }

    this.pollingInterval = setInterval(async () => {
      // Silently refresh using existing search logic
      await this.searchMemories(true); // silent = true
    }, 2000); // Poll every 3 seconds - reasonable for active user interactions
  },

  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  },

  // Call this when the dialog/component is closed or destroyed
  cleanup() {
    this.stopPolling();
    // Clear data without triggering a new search (component is being destroyed)
    this.areaFilter = "";
    this.searchQuery = "";
    this.memories = [];
    this.totalCount = 0;
    this.totalDbCount = 0;
    this.knowledgeCount = 0;
    this.conversationCount = 0;
    this.areasCount = {};
    this.message = null;
    this.currentPage = 1;
    this.editMemoryBackup;
  },

  enableEditMode() {
    this.editMode = true;
    this.editMemoryBackup = JSON.stringify(this.detailMemory); // store backup
  },

  cancelEditMode() {
    this.editMode = false;
    this.detailMemory = JSON.parse(this.editMemoryBackup); // restore backup
  },

  async confirmEditMode() {
    try {

      const response = await API.callJsonApi("memory_dashboard", {
        action: "update",
        memory_subdir: this.selectedMemorySubdir,
        original: JSON.parse(this.editMemoryBackup),
        edited: this.detailMemory,
      });

      if(response.success){
        justToast("Memory updated successfully", "success");
        await this.searchMemories(true); // silent refresh
      }else{
        justToast(`Failed to update memory: ${response.error}`, "error");
      }

      this.editMode = false;
      this.editMemoryBackup = null; // discard backup
    } catch (error) {
      console.error("Error confirming edit mode:", error);
      justToast("Failed to save memory changes.", "error");
    }
  },
};

const store = createStore("memoryDashboardStore", memoryDashboardStore);

export { store };
