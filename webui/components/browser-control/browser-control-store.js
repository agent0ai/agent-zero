import { createStore } from "/js/AlpineStore.js";

const model = {
    isVisible: false,
    isMinimized: false,
    isMaximized: false,
    vncUrl: '',
    vncReady: false,
    _checkInterval: null,

    init() {
        this.checkVncAvailability();
        // Poll for VNC availability every 3 seconds
        this._checkInterval = setInterval(() => this.checkVncAvailability(), 3000);
    },

    async checkVncAvailability() {
        try {
            const response = await fetch('/browser_control?action=info');
            const data = await response.json();
            this.vncReady = data.vnc_ready;

            if (data.vnc_ready && data.novnc_url) {
                this.vncUrl = data.novnc_url;
            }
        } catch (error) {
            console.log('VNC not available:', error);
            this.vncReady = false;
        }
    },

    show(url = null) {
        if (url) {
            this.vncUrl = url;
        }
        this.isVisible = true;
        this.isMinimized = false;
    },

    hide() {
        this.isVisible = false;
    },

    cleanup() {
        if (this._checkInterval) {
            clearInterval(this._checkInterval);
            this._checkInterval = null;
        }
    },

    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        if (this.isMinimized) {
            this.isMaximized = false;
        }
    },

    toggleMaximize() {
        this.isMaximized = !this.isMaximized;
    }
};

// Create and export the store
const store = createStore("browserControl", model);
export { store };
