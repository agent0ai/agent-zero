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
  
  // Image dimensions
  naturalWidth: 0,
  naturalHeight: 0,
  baseScale: 1,
  
  // Pan state
  panX: 0,
  panY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  dragStartPanX: 0,
  dragStartPanY: 0,
  activePointerId: null,
  windowDragMoveHandler: null,
  windowDragUpHandler: null,

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
    this.naturalWidth = 0;
    this.naturalHeight = 0;
    this.baseScale = 1;
    this.panX = 0;
    this.panY = 0;
    this.isDragging = false;
    this.activePointerId = null;
    this.removeWindowDragListeners();
  },

  onImageLoad(event) {
    const img = event.target;
    this.naturalWidth = img.naturalWidth;
    this.naturalHeight = img.naturalHeight;
    this.imageLoaded = true;
    this.zoomLevel = 1;
    this.panX = 0;
    this.panY = 0;
    // Reset any previous transform
    img.classList.remove('zoomed');
    img.style.width = '';
    img.style.height = '';
    img.style.transform = '';
  },

  // Drag/pan methods
  startDrag(event) {
    // Pointer events: mouse (button 0) or touch/pen (button can be -1/undefined)
    if (typeof event.button === 'number' && event.button !== 0) return;
    event.preventDefault();

    this.isDragging = true;
    this.activePointerId = typeof event.pointerId === 'number' ? event.pointerId : null;
    this.dragStartX = event.clientX;
    this.dragStartY = event.clientY;
    this.dragStartPanX = this.panX;
    this.dragStartPanY = this.panY;

    const canvas = document.querySelector('.image-canvas');
    if (canvas && this.activePointerId !== null && typeof canvas.setPointerCapture === 'function') {
      try {
        canvas.setPointerCapture(this.activePointerId);
      } catch (e) {
        // ignore
      }
    }

    this.addWindowDragListeners();
  },

  onDrag(event) {
    if (!this.isDragging) return;
    if (this.activePointerId !== null && typeof event.pointerId === 'number' && event.pointerId !== this.activePointerId) {
      return;
    }
    event.preventDefault();
    const dx = event.clientX - this.dragStartX;
    const dy = event.clientY - this.dragStartY;
    this.panX = this.dragStartPanX + dx;
    this.panY = this.dragStartPanY + dy;
    this.updateImageTransform();
  },

  onWheel(event) {
    // Trackpad scrolling on macOS reports both deltaX and deltaY.
    // Prevent the modal/page from scrolling and instead pan the image.
    if (!event) return;

    // Avoid fighting with an active drag.
    if (this.isDragging) {
      event.preventDefault();
      return;
    }

    // If image isn't ready, ignore.
    if (!this.currentImageUrl || !this.naturalWidth || !this.naturalHeight) return;

    event.preventDefault();

    // deltaMode: 0=pixels, 1=lines, 2=pages
    // Convert non-pixel deltas to an approximate pixel value.
    let dx = event.deltaX || 0;
    let dy = event.deltaY || 0;
    if (event.deltaMode === 1) {
      dx *= 16;
      dy *= 16;
    } else if (event.deltaMode === 2) {
      dx *= 800;
      dy *= 800;
    }

    // Pan in the direction of scrolling.
    this.panX -= dx;
    this.panY -= dy;
    this.updateImageTransform();
  },

  endDrag() {
    if (!this.isDragging) return;
    this.isDragging = false;
    this.activePointerId = null;
    this.removeWindowDragListeners();
  },

  addWindowDragListeners() {
    this.removeWindowDragListeners();

    this.windowDragMoveHandler = (e) => this.onDrag(e);
    this.windowDragUpHandler = () => this.endDrag();

    window.addEventListener('pointermove', this.windowDragMoveHandler, { passive: false });
    window.addEventListener('pointerup', this.windowDragUpHandler, { passive: false });
    window.addEventListener('pointercancel', this.windowDragUpHandler, { passive: false });
  },

  removeWindowDragListeners() {
    if (this.windowDragMoveHandler) {
      window.removeEventListener('pointermove', this.windowDragMoveHandler);
      this.windowDragMoveHandler = null;
    }
    if (this.windowDragUpHandler) {
      window.removeEventListener('pointerup', this.windowDragUpHandler);
      window.removeEventListener('pointercancel', this.windowDragUpHandler);
      this.windowDragUpHandler = null;
    }
  },

  clampPan(containerWidth, containerHeight, displayWidth, displayHeight) {
    const margin = 25;

    const limitX = Math.max(0, (containerWidth + displayWidth) / 2 - margin);
    const limitY = Math.max(0, (containerHeight + displayHeight) / 2 - margin);

    this.panX = Math.max(-limitX, Math.min(limitX, this.panX));
    this.panY = Math.max(-limitY, Math.min(limitY, this.panY));
  },

  getDisplaySize(containerWidth, containerHeight) {
    // Fit in both dimensions without upscaling
    const scaleX = containerWidth / this.naturalWidth;
    const scaleY = containerHeight / this.naturalHeight;
    const fitScale = Math.min(scaleX, scaleY, 1);
    const scale = fitScale * this.zoomLevel;

    return {
      width: this.naturalWidth * scale,
      height: this.naturalHeight * scale,
    };
  },

  // Zoom controls
  zoomIn() {
    this.zoomLevel = Math.min(this.zoomLevel * 1.25, 10);
    this.updateImageTransform();
  },

  zoomOut() {
    this.zoomLevel = Math.max(this.zoomLevel / 1.25, 0.1);
    this.updateImageTransform();
  },

  resetZoom() {
    this.zoomLevel = 1;
    this.panX = 0;
    this.panY = 0;
    const img = document.querySelector('.modal-image');
    if (img) {
      img.classList.remove('zoomed');
      img.style.width = '';
      img.style.height = '';
      img.style.transform = '';
    }
  },

  updateImageTransform() {
    const img = document.querySelector('.modal-image');
    const wrapper = document.querySelector('.image-canvas');
    if (!img || !wrapper || !this.naturalWidth || !this.naturalHeight) return;

    const containerWidth = wrapper.clientWidth;
    const containerHeight = wrapper.clientHeight;

    const displaySize = this.getDisplaySize(containerWidth, containerHeight);
    this.clampPan(containerWidth, containerHeight, displaySize.width, displaySize.height);

    img.classList.add('zoomed');
    img.style.width = `${displaySize.width}px`;
    img.style.height = `${displaySize.height}px`;
    img.style.transform = `translate(${this.panX}px, ${this.panY}px)`;
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

