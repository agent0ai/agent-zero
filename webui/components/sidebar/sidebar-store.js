import { createStore } from "/js/AlpineStore.js";

// This store manages the visibility and state of the main sidebar panel.
const model = {
  isOpen: true,
  versionNo: "",
  commitTime: "",

  get versionLabel() {
    return this.versionNo && this.commitTime
      ? `Version ${this.versionNo} ${this.commitTime}`
      : "";
  },

  // Initialize the store by setting up a resize listener
  init() {
    this.handleResize();
    this.resizeHandler = () => this.handleResize();
    window.addEventListener("resize", this.resizeHandler);
    
    // Load version info from global scope
    const gi = (globalThis && globalThis.gitinfo) ? globalThis.gitinfo : null;
    if (gi && gi.version && gi.commit_time) {
      this.versionNo = gi.version;
      this.commitTime = gi.commit_time;
    }
  },

  // Cleanup method for lifecycle management
  destroy() {
    if (this.resizeHandler) {
      window.removeEventListener("resize", this.resizeHandler);
      this.resizeHandler = null;
    }
  },

  // Toggle the sidebar's visibility
  toggle() {
    this.isOpen = !this.isOpen;
  },

  // Close the sidebar, e.g., on overlay click on mobile
  close() {
    if (this.isMobile()) {
      this.isOpen = false;
    }
  },

  // Handle browser resize to show/hide sidebar based on viewport width
  handleResize() {
    this.isOpen = !this.isMobile();
  },

  // Check if the current viewport is mobile
  isMobile() {
    return window.innerWidth <= 768;
  },
};

export const store = createStore("sidebar", model);
