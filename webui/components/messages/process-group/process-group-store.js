import { createStore } from "/js/AlpineStore.js";

// Process Group Store - manages collapsible process groups in chat
const model = {
  // Track which process groups are expanded (by group ID)
  expandedGroups: {},
  
  // Track which individual steps are expanded within a group
  expandedSteps: {},
  
  // Default collapsed state for new process groups
  defaultCollapsed: true,

  init() {
    try {
      // Load persisted state
      const stored = localStorage.getItem("processGroupState");
      if (stored) {
        const parsed = JSON.parse(stored);
        this.expandedGroups = parsed.expandedGroups || {};
        this.expandedSteps = parsed.expandedSteps || {};
        this.defaultCollapsed = parsed.defaultCollapsed ?? true;
      }
    } catch (e) {
      console.error("Failed to load process group state", e);
    }
  },

  _persist() {
    try {
      localStorage.setItem("processGroupState", JSON.stringify({
        expandedGroups: this.expandedGroups,
        expandedSteps: this.expandedSteps,
        defaultCollapsed: this.defaultCollapsed
      }));
    } catch (e) {
      console.error("Failed to persist process group state", e);
    }
  },

  // Check if a process group is expanded
  isGroupExpanded(groupId) {
    if (groupId in this.expandedGroups) {
      return this.expandedGroups[groupId];
    }
    return !this.defaultCollapsed;
  },

  // Toggle process group expansion
  toggleGroup(groupId) {
    const current = this.isGroupExpanded(groupId);
    this.expandedGroups[groupId] = !current;
    this._persist();
  },

  // Expand a specific group
  expandGroup(groupId) {
    this.expandedGroups[groupId] = true;
    this._persist();
  },

  // Collapse a specific group
  collapseGroup(groupId) {
    this.expandedGroups[groupId] = false;
    this._persist();
  },

  // Check if a step within a group is expanded
  isStepExpanded(groupId, stepId) {
    const key = `${groupId}:${stepId}`;
    return this.expandedSteps[key] || false;
  },

  // Toggle step expansion
  toggleStep(groupId, stepId) {
    const key = `${groupId}:${stepId}`;
    this.expandedSteps[key] = !this.expandedSteps[key];
    this._persist();
  },

  // Get icon for step type
  getStepIcon(type) {
    const icons = {
      'agent': 'psychology',
      'tool': 'build',
      'code_exe': 'terminal',
      'browser': 'language',
      'info': 'info',
      'hint': 'lightbulb',
      'util': 'settings',
      'warning': 'warning',
      'error': 'error'
    };
    return icons[type] || 'circle';
  },

  // Get label for step type
  getStepLabel(type) {
    const labels = {
      'agent': 'Thinking',
      'tool': 'Tool',
      'code_exe': 'Code',
      'browser': 'Browser',
      'info': 'Info',
      'hint': 'Hint',
      'util': 'Utility',
      'warning': 'Warning',
      'error': 'Error'
    };
    return labels[type] || 'Process';
  },

  // Clear state for a specific context (when chat is reset)
  clearContext(contextPrefix) {
    // Clear groups matching the context
    for (const key of Object.keys(this.expandedGroups)) {
      if (key.startsWith(contextPrefix)) {
        delete this.expandedGroups[key];
      }
    }
    // Clear steps matching the context
    for (const key of Object.keys(this.expandedSteps)) {
      if (key.startsWith(contextPrefix)) {
        delete this.expandedSteps[key];
      }
    }
    this._persist();
  }
};

export const store = createStore("processGroup", model);
