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

  // Get icon for step type (Material Symbols)
  getStepIcon(type) {
    const icons = {
      'agent': 'neurology',
      'tool': 'build',
      'code_exe': 'terminal',
      'browser': 'language',
      'info': 'info',
      'hint': 'lightbulb',
      'util': 'settings',
      'warning': 'warning',
      'error': 'error',
      'mcp': 'api',
      'memory': 'memory',
      'done': 'check_circle',
      'subagent': 'group'
    };
    return icons[type] || 'circle';
  },

  // Get 3-letter status code for step type
  getStepCode(type) {
    const codes = {
      'agent': 'GEN',
      'tool': 'MCP',
      'code_exe': 'EXE',
      'browser': 'EXE',
      'info': 'INF',
      'hint': 'INF',
      'util': 'UTL',
      'warning': 'WRN',
      'error': 'ERR',
      'mcp': 'MCP',
      'memory': 'MEM',
      'done': 'END',
      'response': 'END',
      'subagent': 'SUB'
    };
    return codes[type] || 'GEN';
  },

  // Get color class for status code
  getStatusColorClass(type) {
    const colors = {
      'agent': 'status-gen',
      'tool': 'status-mcp',
      'code_exe': 'status-exe',
      'browser': 'status-exe',
      'info': 'status-inf',
      'hint': 'status-inf',
      'util': 'status-utl',
      'warning': 'status-wrn',
      'error': 'status-err',
      'mcp': 'status-mcp',
      'memory': 'status-mem',
      'done': 'status-end',
      'response': 'status-end',
      'subagent': 'status-sub'
    };
    return colors[type] || 'status-gen';
  },

  // Get icon for badge display (Material Symbols)
  getStepBadgeIcon(type) {
    const icons = {
      'agent': 'public',         // Globe for GEN (network intelligence)
      'tool': 'build',           // Wrench for MCP
      'code_exe': 'terminal',    // Terminal for EXE
      'browser': 'language',     // Globe for browser
      'info': 'info',
      'hint': 'lightbulb',
      'util': 'settings',
      'warning': 'warning',
      'error': 'error',
      'mcp': 'build',            // Wrench for MCP
      'memory': 'memory',
      'done': 'check_circle',
      'response': 'check_circle',
      'subagent': 'group'
    };
    return icons[type] || 'circle';
  },

  // Get label for step type (longer description)
  getStepLabel(type) {
    const labels = {
      'agent': 'Generating',
      'tool': 'MCP Call',
      'code_exe': 'Executing',
      'browser': 'Browser',
      'info': 'Info',
      'hint': 'Hint',
      'util': 'Utility',
      'warning': 'Warning',
      'error': 'Error',
      'mcp': 'MCP',
      'memory': 'Memory',
      'done': 'Done',
      'response': 'Response',
      'subagent': 'Subagent'
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
