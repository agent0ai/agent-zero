import { createStore } from "/js/AlpineStore.js";

// This store manages the visibility and state of the main sidebar panel.
const model = {
  isOpen: true,
  menuOpen: false,
  rowMenuOpenId: "",
  rowMenuKind: "chat",
  rowMenuStyle: {},
  rowListExtensions: { chat: {}, task: {} },
  _initialized: false,

  // Centralized collapse state for all sidebar sections (persisted in localStorage)
  sectionStates: {
    tasks: false,       // default: collapsed
    chatActions: false, // default: collapsed
    preferences: false  // default: collapsed
  },

  // Initialize the store by setting up a resize listener
  // Guard ensures this runs only once, even if called from multiple components
  init() {
    if (this._initialized) return;
    this._initialized = true;

    this.loadSectionStates();
    this.handleResize();
    this.resizeHandler = () => this.handleResize();
    window.addEventListener("resize", this.resizeHandler);
  },

  // Load section collapse states from localStorage
  loadSectionStates() {
    try {
      const stored = localStorage.getItem('sidebarSections');
      if (stored) {
        this.sectionStates = { ...this.sectionStates, ...JSON.parse(stored) };
      }
    } catch (e) {
      console.error('Failed to load sidebar section states', e);
    }
  },

  // Persist section states to localStorage
  persistSectionStates() {
    try {
      localStorage.setItem('sidebarSections', JSON.stringify(this.sectionStates));
    } catch (e) {
      console.error('Failed to persist section states', e);
    }
  },

  // Check if a section should be open (used by x-init in templates)
  isSectionOpen(name) {
    return this.sectionStates[name] === true;
  },

  // Toggle and persist a section's open state (drives Bootstrap programmatically via components)
  toggleSection(name) {
    if (!(name in this.sectionStates)) return;
    this.sectionStates[name] = !this.sectionStates[name];
    this.persistSectionStates();
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
    if (this.isMobile()) {
      this.isOpen = false;
    }
    this.menuClose();
    this.rowMenuClose();
  },

  // Check if the current viewport is mobile
  isMobile() {
    return window.innerWidth <= 768;
  },

  // Dropdown positioning for quick-actions (fixed position to escape overflow:hidden)
  dropdownStyle: {},

  headOpen() {
    return this.isOpen || this.menuOpen;
  },

  menuToggle(triggerElement) {
    this.menuOpen = !this.menuOpen;
    if (this.menuOpen) {
      this.menuPos(triggerElement);
    }
  },

  menuClose() {
    this.menuOpen = false;
  },

  menuClick(event, panelElement) {
    if (!this.menuOpen || !panelElement) return;
    if (!panelElement.contains(event.target)) {
      this.menuClose();
    }
  },

  menuPos(triggerElement) {
    if (!triggerElement) return;
    const rect = triggerElement.getBoundingClientRect();
    const menuWidth = Math.max(rect.width, 180);
    const viewportPadding = 8;
    const maxLeft = Math.max(
      viewportPadding,
      window.innerWidth - menuWidth - viewportPadding,
    );
    this.dropdownStyle = {
      top: `${rect.bottom + 8}px`,
      left: `${Math.min(Math.max(rect.left, viewportPadding), maxLeft)}px`,
      width: `${menuWidth}px`
    };
  },

  registerRowListExtension(kind, name, extension) {
    if (!this.rowListExtensions[kind] || !name) return;
    this.rowListExtensions = {
      ...this.rowListExtensions,
      [kind]: { ...this.rowListExtensions[kind], [name]: extension },
    };
  },

  hasListView(kind) {
    return Object.values(this.rowListExtensions[kind] || {}).some(
      (extension) => extension.hasView?.(),
    );
  },

  sortRows(kind, rows) {
    return Object.values(this.rowListExtensions[kind] || {}).reduce(
      (result, extension) => extension.sort?.(result) || result,
      [...rows],
    );
  },

  hasRowDividerBefore(kind, item, index, rows) {
    return Object.values(this.rowListExtensions[kind] || {}).some((extension) =>
      extension.dividerBefore?.(item, index, rows),
    );
  },

  rowMenuToggle(id, kind, triggerElement) {
    if (this.rowMenuOpenId === id) {
      this.rowMenuClose();
      return;
    }

    this.rowMenuOpenId = id;
    this.rowMenuKind = kind;
    this.rowMenuStyle = this.rowMenuPos(triggerElement);
  },

  rowMenuClose() {
    this.rowMenuOpenId = "";
    this.rowMenuStyle = {};
  },

  rowMenuClick(event, menuElement) {
    if (!this.rowMenuOpenId || menuElement?.contains(event.target)) return;
    this.rowMenuClose();
  },

  rowMenuPos(triggerElement) {
    if (!triggerElement) return {};

    const rect = triggerElement.getBoundingClientRect();
    const gap = 6;
    const padding = 8;
    const menuWidth = 180;
    const spaceBelow = window.innerHeight - rect.bottom - gap - padding;
    const spaceAbove = rect.top - gap - padding;
    const openUp = spaceAbove > spaceBelow;
    const maxLeft = Math.max(padding, window.innerWidth - menuWidth - padding);
    const left = Math.min(Math.max(rect.right - menuWidth, padding), maxLeft);

    return {
      left: `${Math.round(left)}px`,
      right: "auto",
      top: openUp ? "auto" : `${Math.round(rect.bottom + gap)}px`,
      bottom: openUp ? `${Math.round(window.innerHeight - rect.top + gap)}px` : "auto",
      minWidth: `${menuWidth}px`,
      maxHeight: `${Math.max(0, openUp ? spaceAbove : spaceBelow)}px`,
    };
  },
};

export const store = createStore("sidebar", model);
