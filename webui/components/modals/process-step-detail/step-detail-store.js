import { createStore } from "/js/AlpineStore.js";
import { createActionButton, copyToClipboard } from "/components/messages/action-buttons/simple-action-buttons.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

// Step Detail Store - manages the step detail modal

const model = {
  // Selected step for detail modal view
  selectedStepForDetail: null,

  // ACE editor instance for raw JSON view
  _rawEditor: null,

  // Show step detail modal
  showStepDetail(stepData) {
    if (!stepData) return;
    this.selectedStepForDetail = stepData;
    window.openModal("modals/process-step-detail/process-step-detail.html");
  },

  // render copy buttons for each segment (called via x-init)
  renderSegmentButtons() {
    const step = this.selectedStepForDetail;

    [
      { segment: "heading", value: this.cleanHeading(step?.heading) },
      { segment: "content", value: step?.content ?? "" }
    ].forEach(({ segment, value }) => {
      document.querySelector(`[data-segment="${segment}"]`)?.replaceChildren(
        createActionButton("copy", "", () => copyToClipboard(value))
      );
    });
  },

  // render copy buttons for individual kvp boxes
  renderKvpCopyButton(container, key, value) {
    const copyText = this.formatFlatValue(value);
    container?.replaceChildren(
      createActionButton("copy", "", () => copyToClipboard(copyText))
    );
  },

  // Close step detail modal
  closeStepDetail() {
    this.selectedStepForDetail = null;
    window.closeModal();
  },

  // Copy text to clipboard with toast feedback
  copyToClipboard(text) {
    navigator.clipboard.writeText(text)
      .then(() => notificationStore.addFrontendToastOnly("success", "Copied to clipboard!", "", 3))
      .catch((err) => console.error("Clipboard copy failed:", err));
  },

  // Format step data for full copy (all metadata + content)
  formatStepForCopy(step) {
    if (!step) return "";
    const lines = [];
    lines.push(`Type: ${step.type || "unknown"}`);
    const heading = this.cleanHeading(step.heading);
    if (heading) lines.push(`Heading: ${heading}`);
    if (step.timestamp) {
      const date = new Date(parseFloat(step.timestamp) * 1000);
      lines.push(`Timestamp: ${date.toISOString()}`);
    }
    if (step.durationMs) lines.push(`Duration: ${step.durationMs}ms`);
    if (step.kvps) {
      lines.push("");
      lines.push("--- Data ---");
      const flattenedKvps = this.flattenKvps(step.kvps);
      for (const [key, value] of Object.entries(flattenedKvps)) {
        lines.push(this.buildKvpCopyText(key, value));
      }
    }
    if (step.content) {
      lines.push("");
      lines.push("--- Content ---");
      lines.push(step.content);
    }
    return lines.join("\n");
  },

  // Get primary content for a step (type-aware)
  // For "Copy Content" button - returns the main content, not metadata
  getStepPrimaryContent(step) {
    if (!step) return "";
    if (step.type === "code_exe") {
      return step.content || "";
    }
    if (step.type === "agent") {
      // Raw LLM response is in content field - this is the primary content
      return step.content || "";
    }
    if ((step.type === "tool" || step.type === "mcp") && step.kvps) {
      return step.kvps.result || step.content || "";
    }
    return step.content || "";
  },

  // Initialize ACE editor for raw JSON view
  initRawEditor() {
    const container = document.getElementById("step-detail-raw-editor");
    if (!container) return;

    this.destroyRawEditor();

    if (!window.ace?.edit) {
      console.warn("ACE editor not available");
      return;
    }

    const stepData = this.selectedStepForDetail;
    if (!stepData) return;

    const editorInstance = window.ace.edit("step-detail-raw-editor");
    if (!editorInstance) return;

    this._rawEditor = editorInstance;

    const darkMode = window.localStorage?.getItem("darkMode");
    const theme = darkMode !== "false" ? "ace/theme/github_dark" : "ace/theme/tomorrow";

    this._rawEditor.setTheme(theme);
    this._rawEditor.session.setMode("ace/mode/json");
    this._rawEditor.setValue(JSON.stringify(stepData, null, 2), -1);
    this._rawEditor.setReadOnly(true);
    this._rawEditor.clearSelection();
    this._rawEditor.setOptions({
      showPrintMargin: false,
      highlightActiveLine: false,
      highlightGutterLine: false
    });
  },

  // Destroy ACE editor instance
  destroyRawEditor() {
    if (this._rawEditor?.destroy) {
      this._rawEditor.destroy();
      this._rawEditor = null;
    }
  },

  // Format step type for display
  formatStepType(type) {
    const typeMap = {
      'agent': 'Generation',
      'code_exe': 'Code Execution',
      'tool': 'Tool Call',
      'mcp': 'MCP Tool',
      'browser': 'Browser',
      'response': 'Response',
      'info': 'Info',
      'hint': 'Hint',
      'warning': 'Warning',
      'error': 'Error',
      'util': 'Utility',
      'progress': 'Progress'
    };
    return typeMap[type] || (type ? type.charAt(0).toUpperCase() + type.slice(1) : 'Unknown');
  },

  // Format timestamp for display
  formatTimestamp(timestamp) {
    if (!timestamp) return '';
    const date = new Date(parseFloat(timestamp) * 1000);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  },

  // Format duration for display
  formatDuration(ms) {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  },

  // Format value for display (handles objects)
  formatValue(value) {
    return value == null
      ? ''
      : (typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value));
  },

  // Format key for display (title case)
  formatKey(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  },

  // flatten nested kvps into top-level entries
  flattenKvps(kvps, parentKey = "") {
    const isPlainObject = value => value && typeof value === "object" && !Array.isArray(value);
    return Object.entries(kvps || {}).reduce((acc, [key, value]) => {
      const fullKey = [parentKey, this.formatKey(key)].filter(Boolean).join(" / ");
      return {
        ...acc,
        ...(isPlainObject(value) ? this.flattenKvps(value, fullKey) : { [fullKey]: value })
      };
    }, {});
  },

  // format values
  formatFlatValue(value) {
    return Array.isArray(value)
      ? value
        .map(item => this.formatValue(item))
        .filter(item => item.trim())
        .join('\n')
      : this.formatValue(value);
  },

  // build copy text
  buildKvpCopyText(key, value) {
    const formattedValue = this.formatFlatValue(value);
    const separator = formattedValue.includes("\n") ? ":\n" : ": ";
    return `${key}${separator}${formattedValue}`;
  },

  // Clean heading by removing icon:// prefixes
  cleanHeading(text) {
    if (!text) return "";
    return String(text)
      .replace(/icon:\/\/[a-zA-Z0-9_]+\s*/g, "")
      .trim();
  }
};

export const store = createStore("stepDetail", model);
