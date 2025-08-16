// Browser Control Modal - For manual browser interaction via Chrome DevTools
import { callJsonApi } from '/js/api.js';

const browserControlModalProxy = {
    isOpen: false,
    isLoading: false,
    isConnected: false,
    title: 'Manual Browser Control',
    description: 'Take control of the browser using Chrome DevTools to handle captchas, logins, and other interactive elements',
    devtoolsUrl: '',
    browserStatus: null,
    
    async openModal() {
        const modalEl = document.getElementById('browserControlModal');
        
        // If modal doesn't exist, create it
        if (!modalEl) {
            await this.createModal();
        }
        
        const modalAD = Alpine.$data(document.getElementById('browserControlModal'));
        
        modalAD.isOpen = true;
        modalAD.isLoading = true;
        modalAD.title = this.title;
        modalAD.description = this.description;
        
        // Check browser status first
        try {
            const statusResponse = await callJsonApi('/browser_control_status', {});
            this.browserStatus = statusResponse;
            
            if (!this.browserStatus.browser.is_running) {
                // Start browser session
                const startResponse = await callJsonApi('/browser_control_start', {
                    mode: 'devtools',
                    headless: false
                });
                
                if (startResponse && startResponse.browser) {
                    this.devtoolsUrl = startResponse.browser.devtools_url;
                }
            } else {
                // Browser already running, get DevTools URL
                this.devtoolsUrl = this.browserStatus.browser.devtools_url;
            }
            
            // Load DevTools interface in iframe
            if (this.devtoolsUrl) {
                modalAD.html = `
                    <div class="browser-control-container" style="width: 100%; height: 700px; position: relative;">
                        <div class="browser-control-header" style="background: #2c3e50; color: white; padding: 10px; border-radius: 8px 8px 0 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: bold;">Chrome DevTools - Manual Browser Control</span>
                                <div>
                                    <button onclick="document.querySelector('.browser-control-iframe').src = '${this.devtoolsUrl}'" 
                                            style="background: #3498db; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; margin-right: 8px;">
                                        Refresh
                                    </button>
                                    <span style="font-size: 12px; opacity: 0.8;">Use DevTools to control the browser manually</span>
                                </div>
                            </div>
                        </div>
                        <iframe 
                            class="browser-control-iframe"
                            src="${this.devtoolsUrl}" 
                            style="width: 100%; height: calc(100% - 50px); border: none; border-radius: 0 0 8px 8px;"
                            allow="camera; microphone; clipboard-read; clipboard-write; cross-origin-isolated"
                            sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation"
                        ></iframe>
                    </div>
                `;
                modalAD.isConnected = true;
            } else {
                modalAD.html = `
                    <div class="browser-control-error" style="text-align: center; padding: 40px;">
                        <span class="material-symbols-outlined" style="font-size: 48px; color: #f44336;">error</span>
                        <p style="margin-top: 16px; color: #666;">Failed to start browser control session</p>
                        <p style="margin-top: 8px; color: #999; font-size: 14px;">Make sure Chrome/Chromium is installed</p>
                        <button onclick="browserControlModalProxy.retryConnection()" class="btn-primary" style="margin-top: 20px;">
                            Retry Connection
                        </button>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('Failed to start browser control:', error);
            modalAD.html = `
                <div class="browser-control-error" style="text-align: center; padding: 40px;">
                    <span class="material-symbols-outlined" style="font-size: 48px; color: #f44336;">error</span>
                    <p style="margin-top: 16px; color: #666;">Error: ${error.message || 'Failed to connect'}</p>
                    <p style="margin-top: 8px; color: #999; font-size: 14px;">
                        ${error.message && error.message.includes('Chrome') ? 
                          'Please install Google Chrome or Chromium browser' : 
                          'Check that the browser control feature is enabled in settings'}
                    </p>
                    <button onclick="browserControlModalProxy.retryConnection()" class="btn-primary" style="margin-top: 20px;">
                        Retry Connection
                    </button>
                </div>
            `;
        } finally {
            modalAD.isLoading = false;
        }
    },
    
    async retryConnection() {
        this.openModal();
    },
    
    async handleClose() {
        this.isOpen = false;
        this.isConnected = false;
        this.devtoolsUrl = '';
        
        // Keep browser session running for continued agent use
        // Browser session will be stopped automatically when Agent Zero shuts down
    },
    
    async createModal() {
        // Create modal HTML structure
        const modalHtml = `
            <div id="browserControlModal" x-data="browserControlModalProxy" x-show="isOpen" 
                 class="fixed inset-0 z-50 overflow-y-auto" style="display: none;"
                 x-cloak>
                <div class="flex items-center justify-center min-h-screen px-4">
                    <!-- Backdrop -->
                    <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
                         @click="handleClose()"></div>
                    
                    <!-- Modal -->
                    <div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full mx-auto z-50">
                        <!-- Header -->
                        <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
                            <div>
                                <h3 class="text-lg font-semibold" x-text="title"></h3>
                                <p class="text-sm text-gray-500 dark:text-gray-400" x-text="description"></p>
                            </div>
                            <button @click="handleClose()" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                                <span class="material-symbols-outlined">close</span>
                            </button>
                        </div>
                        
                        <!-- Content -->
                        <div class="p-4" style="min-height: 400px;">
                            <div x-show="isLoading" class="flex items-center justify-center h-96">
                                <div class="spinner"></div>
                            </div>
                            <div x-show="!isLoading" x-html="html"></div>
                        </div>
                        
                        <!-- Footer -->
                        <div class="flex justify-between items-center p-4 border-t dark:border-gray-700">
                            <div class="text-sm text-gray-500">
                                <span x-show="isConnected" class="flex items-center">
                                    <span class="material-symbols-outlined text-green-500" style="font-size: 16px; margin-right: 4px;">check_circle</span>
                                    Connected
                                </span>
                            </div>
                            <button @click="handleClose()" class="px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
};

// Wait for Alpine to be ready
document.addEventListener('alpine:init', () => {
    Alpine.data('browserControlModalProxy', () => ({
        // Initialize with default values
        isOpen: false,
        isLoading: false,
        isConnected: false,
        title: 'Manual Browser Control',
        description: 'Take control of the browser using Chrome DevTools',
        html: '',
        
        init() {
            Object.assign(this, browserControlModalProxy);
        },
        
        handleClose() {
            this.isOpen = false;
            this.html = '';
        }
    }));
});

// Global assignment for access from other modules
window.browserControlModalProxy = browserControlModalProxy;

export { browserControlModalProxy };