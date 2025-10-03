import { createStore } from "/js/AlpineStore.js";

// This store manages the visibility and state of the main sidebar panel.
const model = {
  isOpen: true,
  _initialized: false,

  // Initialize the store by setting up a resize listener
  // Guard ensures this runs only once, even if called from multiple components
  init() {
    if (this._initialized) return;
    this._initialized = true;

    this.handleResize();
    this.resizeHandler = () => this.handleResize();
    window.addEventListener("resize", this.resizeHandler);
  },

  // Cleanup method for lifecycle management
  destroy() {
    if (this.resizeHandler) {
      window.removeEventListener("resize", this.resizeHandler);
      this.resizeHandler = null;
    }
    this._initialized = false;
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
