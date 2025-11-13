/**
 * Browser Control Integration
 *
 * Provides global helper functions for browser control.
 * Users can manually open the panel by clicking the browser control icon.
 */

// Wait for Alpine to be ready
document.addEventListener('alpine:initialized', () => {
    console.log('Browser Control Integration initialized');
});

// Global helper functions - can be called from anywhere in the app or console
window.showBrowserControl = function(url) {
    if (Alpine.store('browserControl')) {
        Alpine.store('browserControl').show(url);
    }
};

window.hideBrowserControl = function() {
    if (Alpine.store('browserControl')) {
        Alpine.store('browserControl').hide();
    }
};

window.toggleBrowserControl = function() {
    if (Alpine.store('browserControl')) {
        const store = Alpine.store('browserControl');
        if (store.isVisible) {
            store.hide();
        } else {
            store.show();
        }
    }
};
