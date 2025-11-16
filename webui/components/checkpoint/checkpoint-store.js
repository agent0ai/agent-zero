import { createStore } from "/js/AlpineStore.js";
import { getContext, justToast } from "/index.js";

const model = {
  // State
  loading: false,
  contexts: [],  // Array of {context_id, context_name, is_active, checkpoints[]}
  totalCheckpoints: 0,
  viewMode: 'all',  // 'current' or 'all'
  _initialized: false,

  // Lifecycle
  init() {
    // Initialization if needed
    this._initialized = false;
  },

  onOpen() {
    // Called when modal opens via x-create
    // Reset state on each open
    this.loading = false;
    this.contexts = [];
    this.totalCheckpoints = 0;
    this.viewMode = 'all';
    this._initialized = true;

    // Load checkpoints
    this.loadAllCheckpoints();
  },

  async loadAllCheckpoints() {
    this.loading = true;
    try {
      const response = await fetch('/api_checkpoint_list?all=true', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        this.contexts = data.contexts || [];
        this.totalCheckpoints = data.total_checkpoints || 0;
      } else {
        console.error('Failed to load checkpoints:', response.statusText);
        this.contexts = [];
        this.totalCheckpoints = 0;
      }
    } catch (error) {
      console.error('Error loading checkpoints:', error);
      this.contexts = [];
      this.totalCheckpoints = 0;
    } finally {
      this.loading = false;
    }
  },

  async loadCurrentCheckpoints() {
    const contextId = getContext();
    if (!contextId) {
      this.contexts = [];
      this.totalCheckpoints = 0;
      return;
    }

    this.loading = true;
    try {
      const response = await fetch(`/api_checkpoint_list?context_id=${encodeURIComponent(contextId)}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        const checkpoints = data.checkpoints || [];

        // Structure as single context for consistency
        if (checkpoints.length > 0) {
          this.contexts = [{
            context_id: contextId,
            context_name: 'Current Chat',
            is_active: true,
            checkpoints: checkpoints
          }];
          this.totalCheckpoints = checkpoints.length;
        } else {
          this.contexts = [];
          this.totalCheckpoints = 0;
        }
      } else {
        console.error('Failed to load checkpoints:', response.statusText);
        this.contexts = [];
        this.totalCheckpoints = 0;
      }
    } catch (error) {
      console.error('Error loading checkpoints:', error);
      this.contexts = [];
      this.totalCheckpoints = 0;
    } finally {
      this.loading = false;
    }
  },

  toggleViewMode() {
    this.viewMode = this.viewMode === 'all' ? 'current' : 'all';
    if (this.viewMode === 'all') {
      this.loadAllCheckpoints();
    } else {
      this.loadCurrentCheckpoints();
    }
  },

  async createCheckpoint() {
    const contextId = getContext();
    if (!contextId) {
      this.showNotification('No active chat context', 'error');
      return;
    }

    try {
      const response = await fetch('/api_checkpoint_create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context_id: contextId })
      });

      if (response.ok) {
        // Reload checkpoints based on current view mode
        if (this.viewMode === 'all') {
          await this.loadAllCheckpoints();
        } else {
          await this.loadCurrentCheckpoints();
        }
        this.showNotification('Checkpoint created successfully');
      } else {
        this.showNotification('Failed to create checkpoint', 'error');
      }
    } catch (error) {
      console.error('Error creating checkpoint:', error);
      this.showNotification('Error creating checkpoint', 'error');
    }
  },

  async restore(checkpointId) {
    if (!confirm('Restore this checkpoint? Current state will be replaced.')) {
      return;
    }

    try {
      const response = await fetch('/api_checkpoint_restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ checkpoint_id: checkpointId })
      });

      if (response.ok) {
        this.showNotification('Checkpoint restored successfully');
        // Close modal using Agent Zero's modal system
        if (window.closeModal) window.closeModal();
        // Reload page to reflect restored state
        setTimeout(() => window.location.reload(), 1000);
      } else {
        this.showNotification('Failed to restore checkpoint', 'error');
      }
    } catch (error) {
      console.error('Error restoring checkpoint:', error);
      this.showNotification('Error restoring checkpoint', 'error');
    }
  },

  async delete(checkpointId) {
    if (!confirm('Delete this checkpoint? This cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch('/api_checkpoint_delete', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ checkpoint_id: checkpointId })
      });

      if (response.ok) {
        // Reload checkpoints based on current view mode
        if (this.viewMode === 'all') {
          await this.loadAllCheckpoints();
        } else {
          await this.loadCurrentCheckpoints();
        }
        this.showNotification('Checkpoint deleted');
      } else {
        this.showNotification('Failed to delete checkpoint', 'error');
      }
    } catch (error) {
      console.error('Error deleting checkpoint:', error);
      this.showNotification('Error deleting checkpoint', 'error');
    }
  },

  async cleanup() {
    const contextId = getContext();
    if (!contextId) {
      this.showNotification('No active chat context', 'error');
      return;
    }

    await this.cleanupContext(contextId);
  },

  async cleanupContext(contextId) {
    if (!contextId) {
      this.showNotification('No context ID provided', 'error');
      return;
    }

    if (!confirm('Remove old checkpoints? Only the most recent ones will be kept.')) {
      return;
    }

    try {
      const response = await fetch('/api_checkpoint_cleanup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context_id: contextId })
      });

      if (response.ok) {
        // Reload checkpoints based on current view mode
        if (this.viewMode === 'all') {
          await this.loadAllCheckpoints();
        } else {
          await this.loadCurrentCheckpoints();
        }
        const data = await response.json();
        this.showNotification(`Cleaned up ${data.deleted || 0} old checkpoints`);
      } else {
        this.showNotification('Failed to cleanup checkpoints', 'error');
      }
    } catch (error) {
      console.error('Error cleaning up checkpoints:', error);
      this.showNotification('Error cleaning up checkpoints', 'error');
    }
  },

  // Helpers
  formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  },

  showNotification(message, type = 'success') {
    // Use Agent Zero's justToast notification system
    justToast(message, type, 3000);
  }
};

export const store = createStore("checkpointStore", model);
