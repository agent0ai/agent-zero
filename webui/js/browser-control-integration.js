/**
 * Browser Control Integration
 *
 * Automatically shows the browser control panel when the agent sends
 * a message containing a VNC URL (typically when pause_for_user is called).
 */

// Wait for Alpine to be ready
document.addEventListener('alpine:initialized', () => {
    console.log('Browser Control Integration initialized');

    // Watch for new messages being added to the DOM
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    // Check if the new message contains a VNC URL
                    const messageText = node.textContent || '';

                    // Look for VNC URL pattern (Control Browser link)
                    const vncUrlMatch = messageText.match(/Control Browser.*?(http:\/\/localhost:56080[^\s<"]+)/i) ||
                                       messageText.match(/(http:\/\/localhost:56080\/vnc\.html[^\s<"]+)/i);

                    if (vncUrlMatch) {
                        const vncUrl = vncUrlMatch[1] || vncUrlMatch[0];
                        console.log('VNC URL detected in message, showing browser control:', vncUrl);

                        // Show the browser control panel
                        if (Alpine.store('browserControl')) {
                            // Small delay to ensure the message is fully rendered
                            setTimeout(() => {
                                Alpine.store('browserControl').show(vncUrl);
                            }, 500);
                        }
                    }
                }
            });
        });
    });

    // Observe the chat history container for new messages
    const chatHistory = document.getElementById('chat-history');
    if (chatHistory) {
        observer.observe(chatHistory, {
            childList: true,
            subtree: true
        });
        console.log('Watching for VNC URLs in chat messages');
    } else {
        console.warn('Chat history element not found');
    }
});

// Global function to manually show/hide browser control
// Can be called from anywhere in the app
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
