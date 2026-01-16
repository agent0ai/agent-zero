/**
 * Hot-Reload DevTools Panel
 *
 * Displays hot-reload status and statistics in the WebUI
 */

class HotReloadPanel {
    constructor() {
        this.statusElement = null;
        this.statsElement = null;
        this.updateInterval = null;
        this.updateIntervalMs = 5000; // 5 seconds
    }

    /**
     * Initialize the hot-reload panel
     */
    init() {
        this.createPanel();
        this.startAutoUpdate();
    }

    /**
     * Create the hot-reload panel UI
     */
    createPanel() {
        // Check if panel already exists
        if (document.getElementById('hot-reload-panel')) {
            return;
        }

        // Create panel container
        const panel = document.createElement('div');
        panel.id = 'hot-reload-panel';
        panel.className = 'hot-reload-panel';
        panel.innerHTML = `
            <div class="hot-reload-header">
                <span class="hot-reload-title">🔥 Hot-Reload</span>
                <button class="hot-reload-toggle" onclick="hotReloadPanel.toggle()">−</button>
            </div>
            <div class="hot-reload-content">
                <div class="hot-reload-status" id="hot-reload-status">
                    <div class="status-indicator">
                        <span class="status-dot"></span>
                        <span class="status-text">Loading...</span>
                    </div>
                </div>
                <div class="hot-reload-stats" id="hot-reload-stats">
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-label">Reloads</span>
                            <span class="stat-value" id="stat-reloads">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Success</span>
                            <span class="stat-value success" id="stat-successes">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Failures</span>
                            <span class="stat-value error" id="stat-failures">0</span>
                        </div>
                    </div>
                    <div class="cache-stats">
                        <div class="stat-item">
                            <span class="stat-label">Cached Modules</span>
                            <span class="stat-value" id="stat-modules">0</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add styles
        this.addStyles();

        // Append to body
        document.body.appendChild(panel);

        this.statusElement = document.getElementById('hot-reload-status');
        this.statsElement = document.getElementById('hot-reload-stats');

        // Initial update
        this.updateStatus();
    }

    /**
     * Add CSS styles for the panel
     */
    addStyles() {
        if (document.getElementById('hot-reload-styles')) {
            return;
        }

        const style = document.createElement('style');
        style.id = 'hot-reload-styles';
        style.textContent = `
            .hot-reload-panel {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 300px;
                background: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 165, 0, 0.3);
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                z-index: 10000;
                backdrop-filter: blur(10px);
            }

            .hot-reload-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 16px;
                background: rgba(255, 165, 0, 0.1);
                border-bottom: 1px solid rgba(255, 165, 0, 0.2);
                border-radius: 8px 8px 0 0;
            }

            .hot-reload-title {
                font-weight: bold;
                color: #FFA500;
                font-size: 14px;
            }

            .hot-reload-toggle {
                background: none;
                border: none;
                color: #FFA500;
                font-size: 20px;
                cursor: pointer;
                padding: 0;
                width: 24px;
                height: 24px;
                line-height: 24px;
                text-align: center;
            }

            .hot-reload-toggle:hover {
                opacity: 0.7;
            }

            .hot-reload-content {
                padding: 16px;
            }

            .hot-reload-content.collapsed {
                display: none;
            }

            .status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 16px;
            }

            .status-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #888;
            }

            .status-dot.running {
                background: #4CAF50;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .status-dot.stopped {
                background: #F44336;
            }

            .status-text {
                color: #fff;
                font-size: 13px;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-bottom: 12px;
            }

            .cache-stats {
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }

            .stat-item {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }

            .stat-label {
                font-size: 11px;
                color: #999;
                text-transform: uppercase;
            }

            .stat-value {
                font-size: 18px;
                font-weight: bold;
                color: #fff;
            }

            .stat-value.success {
                color: #4CAF50;
            }

            .stat-value.error {
                color: #F44336;
            }
        `;

        document.head.appendChild(style);
    }

    /**
     * Toggle panel visibility
     */
    toggle() {
        const content = document.querySelector('.hot-reload-content');
        const toggle = document.querySelector('.hot-reload-toggle');

        if (content) {
            content.classList.toggle('collapsed');
            toggle.textContent = content.classList.contains('collapsed') ? '+' : '−';
        }
    }

    /**
     * Update status from API
     */
    async updateStatus() {
        try {
            // Fetch status
            const statusResponse = await fetch('/hot_reload_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: 'status' })
            });

            if (!statusResponse.ok) {
                this.showError('Failed to fetch status');
                return;
            }

            const statusData = await statusResponse.json();

            // Fetch stats
            const statsResponse = await fetch('/hot_reload_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: 'stats' })
            });

            if (!statsResponse.ok) {
                this.showError('Failed to fetch stats');
                return;
            }

            const statsData = await statsResponse.json();

            // Update UI
            this.updateStatusUI(statusData);
            this.updateStatsUI(statsData.stats);

        } catch (error) {
            console.error('Hot-reload panel error:', error);
            this.showError('Connection error');
        }
    }

    /**
     * Update status UI
     */
    updateStatusUI(data) {
        const dot = document.querySelector('.status-dot');
        const text = document.querySelector('.status-text');

        if (dot && text) {
            dot.className = `status-dot ${data.enabled ? 'running' : 'stopped'}`;
            text.textContent = data.status === 'running' ? 'Active' : 'Inactive';
        }
    }

    /**
     * Update stats UI
     */
    updateStatsUI(stats) {
        if (!stats) return;

        const elements = {
            'stat-reloads': stats.reloads || 0,
            'stat-successes': stats.successes || 0,
            'stat-failures': stats.failures || 0,
            'stat-modules': stats.cache_stats?.total_modules || 0,
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const dot = document.querySelector('.status-dot');
        const text = document.querySelector('.status-text');

        if (dot && text) {
            dot.className = 'status-dot stopped';
            text.textContent = message;
        }
    }

    /**
     * Start auto-update
     */
    startAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateInterval = setInterval(() => {
            this.updateStatus();
        }, this.updateIntervalMs);
    }

    /**
     * Stop auto-update
     */
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    /**
     * Destroy the panel
     */
    destroy() {
        this.stopAutoUpdate();

        const panel = document.getElementById('hot-reload-panel');
        if (panel) {
            panel.remove();
        }

        const styles = document.getElementById('hot-reload-styles');
        if (styles) {
            styles.remove();
        }
    }
}

// Global instance
const hotReloadPanel = new HotReloadPanel();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        hotReloadPanel.init();
    });
} else {
    hotReloadPanel.init();
}
