// Browser Control Modal - VNC-based browser interaction
// Note: This uses the global api object from api.js

const browserControlModalProxy = {
    isOpen: false,
    isLoading: false,
    title: 'Browser Control',
    vncUrl: '',
    sessionInfo: null,
    connectionStatus: 'disconnected', // disconnected, connecting, connected, error
    errorMessage: '',

    async openModal(contextId = null) {
        try {
            console.log('Opening browser control modal...');
            this.isLoading = true;
            this.isOpen = true;
            this.connectionStatus = 'connecting';
            this.errorMessage = '';

            // Start browser control session
            console.log('Starting VNC session...');
            const response = await api.callJsonApi('/browser_control', {
                action: 'start_vnc_session',
                context: contextId || (globalThis.getContext ? globalThis.getContext() : null)
            });

            console.log('VNC session response:', response);

            if (response.success) {
                this.vncUrl = response.vnc_url;
                this.sessionInfo = response.session_info;
                this.connectionStatus = 'connected';
                
                console.log('VNC session started, URL:', this.vncUrl);
                
                // Initialize noVNC client
                this.initializeVNCClient();
            } else {
                this.connectionStatus = 'error';
                this.errorMessage = response.error || 'Failed to start VNC session';
                console.error('VNC session failed:', this.errorMessage);
            }
        } catch (error) {
            console.error('Error opening browser control modal:', error);
            this.connectionStatus = 'error';
            this.errorMessage = error.message || 'Unknown error occurred';
        } finally {
            this.isLoading = false;
        }
    },

    async handleClose() {
        try {
            // Clean up VNC connection
            if (this.connectionStatus === 'connected' && this.sessionInfo) {
                await api.callJsonApi('/browser_control', {
                    action: 'release_vnc_session',
                    session_id: this.sessionInfo.session_id
                });
            }
        } catch (error) {
            console.error('Error cleaning up VNC session:', error);
        } finally {
            this.isOpen = false;
            this.vncUrl = '';
            this.sessionInfo = null;
            this.connectionStatus = 'disconnected';
            this.errorMessage = '';
        }
    },

    initializeVNCClient() {
        // This will be called after the modal iframe is ready
        setTimeout(() => {
            const iframe = document.getElementById('vnc-iframe');
            if (iframe && this.vncUrl) {
                // Set iframe source to noVNC client with our VNC session
                iframe.src = this.vncUrl;
                
                iframe.onload = () => {
                    console.log('VNC client loaded successfully');
                    this.connectionStatus = 'connected';
                };
                
                iframe.onerror = () => {
                    console.error('Failed to load VNC client');
                    this.connectionStatus = 'error';
                    this.errorMessage = 'Failed to load VNC client';
                };
            }
        }, 100);
    },

    async takeControlOfBrowser() {
        try {
            const response = await api.callJsonApi('/browser_control', {
                action: 'request_human_control',
                context: globalThis.getContext ? globalThis.getContext() : null
            });

            if (response.success) {
                console.log('Browser control requested successfully');
                // Modal is already open, just update status
                return true;
            } else {
                throw new Error(response.error || 'Failed to request browser control');
            }
        } catch (error) {
            console.error('Error requesting browser control:', error);
            this.errorMessage = error.message;
            return false;
        }
    },

    async releaseControlOfBrowser() {
        try {
            const response = await api.callJsonApi('/browser_control', {
                action: 'release_human_control', 
                context: globalThis.getContext ? globalThis.getContext() : null
            });

            if (response.success) {
                console.log('Browser control released successfully');
                return true;
            } else {
                throw new Error(response.error || 'Failed to release browser control');
            }
        } catch (error) {
            console.error('Error releasing browser control:', error);
            this.errorMessage = error.message;
            return false;
        }
    },

    getStatusMessage() {
        switch (this.connectionStatus) {
            case 'connecting':
                return 'Connecting to browser...';
            case 'connected':
                return 'Connected - You can now interact with the browser';
            case 'error':
                return this.errorMessage || 'Connection error';
            case 'disconnected':
            default:
                return 'Disconnected';
        }
    },

    getStatusClass() {
        switch (this.connectionStatus) {
            case 'connecting':
                return 'status-connecting';
            case 'connected':
                return 'status-connected';
            case 'error':
                return 'status-error';
            case 'disconnected':
            default:
                return 'status-disconnected';
        }
    }
};

// Register with Alpine.js
document.addEventListener('alpine:init', () => {
    Alpine.data('browserControlModalProxy', () => ({
        ...browserControlModalProxy,
        init() {
            // Initialize default values
            this.isOpen = false;
            this.isLoading = false;
            this.vncUrl = '';
            this.sessionInfo = null;
            this.connectionStatus = 'disconnected';
            this.errorMessage = '';
        }
    }));
});

// Global access for backward compatibility and easy calling
window.browserControlModal = browserControlModalProxy;

// Export for module usage (commented out since loaded as regular script)
// export { browserControlModalProxy };

// Global functions for easy access from browser control buttons
window.openBrowserControlModal = function(contextId = null) {
    browserControlModalProxy.openModal(contextId);
};

window.closeBrowserControlModal = function() {
    browserControlModalProxy.handleClose();
};