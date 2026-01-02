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

  // Fallback icon for step type when backend doesn't provide one (Material Symbols)
  // Maps backend log types to appropriate icons
  getStepIcon(type) {
    const icons = {
      'agent': 'network_intelligence',
      'response': 'chat',
      'tool': 'construction',
      'mcp': 'api',
      'subagent': 'communication',
      'code_exe': 'terminal',
      'browser': 'captive_portal',
      'progress': 'timer',
      'info': 'info',
      'hint': 'lightbulb',
      'warning': 'warning',
      'error': 'error',
      'util': 'memory',
      'done': 'done_all'
    };
    return icons[type] || 'circle';
  },

  // Status code (3-4 letter) for backend log types
  getStepCode(type) {
    const codes = {
      'agent': 'GEN',
      'response': 'END',
      'tool': 'TOOL',
      'mcp': 'MCP',
      'subagent': 'SUB',
      'code_exe': 'EXE',
      'browser': 'BRW',
      'progress': 'WAIT',
      'info': 'INF',
      'hint': 'HNT',
      'warning': 'WRN',
      'error': 'ERR',
      'util': 'UTL',
      'done': 'END'
    };
    return codes[type] || type?.toUpperCase()?.slice(0, 4) || 'GEN';
  },

  // CSS color class for backend log types
  getStatusColorClass(type) {
    const colors = {
      'agent': 'status-gen',
      'response': 'status-end',
      'tool': 'status-tool',
      'mcp': 'status-mcp',
      'subagent': 'status-sub',
      'code_exe': 'status-exe',
      'browser': 'status-brw',
      'progress': 'status-wait',
      'info': 'status-inf',
      'hint': 'status-hnt',
      'warning': 'status-wrn',
      'error': 'status-err',
      'util': 'status-utl',
      'done': 'status-end'
    };
    return colors[type] || 'status-gen';
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
