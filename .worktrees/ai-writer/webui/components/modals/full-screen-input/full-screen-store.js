import { createStore } from "/js/AlpineStore.js";

// Store model for the Full-Screen Input Modal
const model = {
  // State
  isOpen: false,
  inputText: "",
  wordWrap: true,
  undoStack: [],
  redoStack: [],
  maxStackSize: 100,
  lastSavedState: "",

  // Lifecycle
  init() {
    // No-op for now; kept for parity and future side-effects
  },

  // Open modal with current chat input content
  openModal() {
    const chatInput = document.getElementById("chat-input");
    this.inputText = chatInput ? chatInput.value : this.inputText;
    this.lastSavedState = this.inputText;
    this.isOpen = true;
    this.undoStack = [];
    this.redoStack = [];

    // Focus the full screen input after rendering
    setTimeout(() => {
      const fullScreenInput = document.getElementById("full-screen-input");
      if (fullScreenInput) fullScreenInput.focus();
    }, 50);
  },

  // Close modal and write value back into main chat input
  handleClose() {
    const chatInput = document.getElementById("chat-input");
    if (chatInput) {
      chatInput.value = this.inputText;
      chatInput.dispatchEvent(new Event("input")); // trigger auto-resize
    }
    this.isOpen = false;
  },

  // History management
  updateHistory() {
    if (this.lastSavedState === this.inputText) return; // no change
    this.undoStack.push(this.lastSavedState);
    if (this.undoStack.length > this.maxStackSize) this.undoStack.shift();
    this.redoStack = [];
    this.lastSavedState = this.inputText;
  },

  undo() {
    if (!this.canUndo) return;
    this.redoStack.push(this.inputText);
    this.inputText = this.undoStack.pop();
    this.lastSavedState = this.inputText;
  },

  redo() {
    if (!this.canRedo) return;
    this.undoStack.push(this.inputText);
    this.inputText = this.redoStack.pop();
    this.lastSavedState = this.inputText;
  },

  clearText() {
    if (!this.inputText) return;
    this.updateHistory();
    this.inputText = "";
    this.lastSavedState = "";
  },

  toggleWrap() {
    this.wordWrap = !this.wordWrap;
  },

  // Computed
  get canUndo() {
    return this.undoStack.length > 0;
  },

  get canRedo() {
    return this.redoStack.length > 0;
  },
};

export const store = createStore("fullScreenInputModal", model);


