import { createStore } from "/js/AlpineStore.js";

const model = {
  // State
  currentImageUrl: null,
  currentImageName: null,
  baseImageUrl: null,
  imageLoaded: false,
  imageError: false,
  zoomLevel: 1,
  refreshInterval: 0,
  activeIntervalId: null,
  closePromise: null,

  /**
   * Open image viewer modal
   * @param {string} imageUrl - URL of the image to display
   * @param {number|object} refreshOrOptions - Either:
   *   - number: refresh interval in ms (legacy compat)
   *   - object: { refreshInterval?: number, name?: string }
   */
  async open(imageUrl, refreshOrOptions) {
    // Parse options (backward compatibility)
    const options = typeof refreshOrOptions === 'number' 
      ? { refreshInterval: refreshOrOptions, name: null }
      : refreshOrOptions || {};

    // Reset state
    this.baseImageUrl = imageUrl;
    this.refreshInterval = options.refreshInterval || 0;
    this.currentImageName = options.name || this.extractImageName(imageUrl);
    this.imageLoaded = false;
    this.imageError = false;
    this.zoomLevel = 1;

    // Add timestamp for cache-busting if refreshing
    this.currentImageUrl = this.refreshInterval > 0 
      ? this.addTimestamp(imageUrl) 
      : imageUrl;

    try {
      // Open modal and track close promise for cleanup
      this.closePromise = window.openModal('modals/image-viewer/image-viewer.html');
      
      // Setup cleanup on modal close
      if (this.closePromise && typeof this.closePromise.finally === 'function') {
        this.closePromise.finally(() => {
          this.stopRefresh();
          this.resetState();
        });
      }

      // Start refresh loop if needed
      if (this.refreshInterval > 0) {
        this.setupAutoRefresh();
      }
    } catch (error) {
      console.error("Image viewer error:", error);
      this.imageError = true;
    }
  },

  setupAutoRefresh() {
    // Clear any existing interval
    this.stopRefresh();

    this.activeIntervalId = setInterval(() => {
      if (!this.isModalVisible()) {
        this.stopRefresh();
        return;
      }
      this.preloadNextImage();
    }, this.refreshInterval);
  },

  async preloadNextImage() {
    const nextSrc = this.addTimestamp(this.baseImageUrl);
    
    // Create a promise that resolves when the image is loaded
    const preloadPromise = new Promise((resolve, reject) => {
      const tempImg = new Image();
      tempImg.onload = () => resolve(nextSrc);
      tempImg.onerror = reject;
      tempImg.src = nextSrc;
    });

    try {
      // Wait for preload to complete
      const loadedSrc = await preloadPromise;
      
      // Check if modal is still visible before updating
      if (this.isModalVisible()) {
        this.currentImageUrl = loadedSrc;
        this.imageLoaded = false; // Trigger reload animation
      }
    } catch (err) {
      console.error('Failed to preload image:', err);
    }
  },

  isModalVisible() {
    const container = document.querySelector('#image-viewer-wrapper');
    if (!container) return false;
    
    // Check if element or any parent is hidden
    let element = container;
    while (element) {
      const styles = window.getComputedStyle(element);
      if (styles.display === 'none' || styles.visibility === 'hidden') {
        return false;
      }
      element = element.parentElement;
    }
    return true;
  },

  stopRefresh() {
    if (this.activeIntervalId !== null) {
      clearInterval(this.activeIntervalId);
      this.activeIntervalId = null;
    }
  },

  resetState() {
    this.currentImageUrl = null;
    this.currentImageName = null;
    this.baseImageUrl = null;
    this.imageLoaded = false;
    this.imageError = false;
    this.zoomLevel = 1;
    this.refreshInterval = 0;
  },

  // Zoom controls
  zoomIn() {
    this.zoomLevel = Math.min(this.zoomLevel * 1.2, 5); // Max 5x zoom
    this.updateImageZoom();
  },

  zoomOut() {
    this.zoomLevel = Math.max(this.zoomLevel / 1.2, 0.1); // Min 0.1x zoom
    this.updateImageZoom();
  },

  resetZoom() {
    this.zoomLevel = 1;
    this.updateImageZoom();
  },

  updateImageZoom() {
    const img = document.querySelector(".modal-image");
    if (img) {
      img.style.transform = `scale(${this.zoomLevel})`;
    }
  },

  // Utility methods
  addTimestamp(url) {
    try {
      const urlObj = new URL(url, window.location.origin);
      urlObj.searchParams.set("t", Date.now().toString());
      return urlObj.toString();
    } catch (e) {
      // Fallback for invalid URLs
      const separator = url.includes('?') ? '&' : '?';
      return `${url}${separator}t=${Date.now()}`;
    }
  },

  extractImageName(url) {
    try {
      const urlObj = new URL(url, window.location.origin);
      const pathname = urlObj.pathname;
      return pathname.split("/").pop() || "Image";
    } catch (e) {
      return url.split("/").pop() || "Image";
    }
  },

  // Optional: cleanup on store destruction
  destroy() {
    this.stopRefresh();
    this.resetState();
  },
};

export const store = createStore("imageViewer", model);

