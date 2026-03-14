/**
 * Tile Row Store - Alpine.js store for dashboard tile management
 * Manages expandable tiles below the chat area for quick access to dashboards
 */

const tileRowModel = {
    // State
    expandedTile: null,  // Currently expanded tile ID (null = all collapsed)
    // 4 monitoring tiles - Portfolio moved to sidebar dashboard, Scheduler stays in Settings
    tiles: [
        {
            id: 'workflows',
            icon: 'workflow',
            label: 'Workflows',
            component: 'components/panels/workflow-panel.html',
            badge: 0,
            badgeType: 'info'  // info, warning, success
        },
        {
            id: 'ralph',
            icon: 'ralph',
            label: 'Ralph Loops',
            component: 'components/panels/ralph-panel.html',
            badge: 0,
            badgeType: 'info'
        },
        {
            id: 'observability',
            icon: 'observability',
            label: 'Observability',
            component: 'components/panels/observability-panel.html',
            badge: 0,
            badgeType: 'info'
        },
        {
            id: 'cowork',
            icon: 'cowork',
            label: 'Cowork',
            component: 'components/panels/cowork-panel.html',
            badge: 0,
            badgeType: 'warning'
        }
    ],
    panelContent: '',
    loading: false,
    pollingInterval: null,

    // Initialization
    init() {
        this.loadBadges();
        this.startPolling();
    },

    // Cleanup
    cleanup() {
        this.stopPolling();
    },

    // Tile actions
    toggleTile(tileId) {
        if (this.expandedTile === tileId) {
            this.collapseTile();
        } else {
            this.expandTile(tileId);
        }
    },

    async expandTile(tileId) {
        const tile = this.tiles.find(t => t.id === tileId);
        if (!tile) return;

        this.loading = true;
        this.expandedTile = tileId;

        try {
            // Load the panel component
            const response = await fetch(tile.component);
            if (response.ok) {
                this.panelContent = await response.text();
            } else {
                this.panelContent = `<div class="panel-error">Failed to load ${tile.label} panel</div>`;
            }
        } catch (error) {
            console.error(`Error loading panel for ${tileId}:`, error);
            this.panelContent = `<div class="panel-error">Error loading panel: ${error.message}</div>`;
        } finally {
            this.loading = false;
        }
    },

    collapseTile() {
        this.expandedTile = null;
        this.panelContent = '';
    },

    // Badge management
    async loadBadges() {
        try {
            // Load badges from various APIs (4 tiles only)
            await Promise.all([
                this.loadWorkflowBadge(),
                this.loadRalphBadge(),
                this.loadCoworkBadge()
            ]);
        } catch (error) {
            console.error('Error loading badges:', error);
        }
    },

    async loadWorkflowBadge() {
        try {
            const resp = await this.apiCall('/workflow_dashboard', {});
            if (resp.stats) {
                const activeCount = resp.stats.active_executions || 0;
                this.updateTileBadge('workflows', activeCount, activeCount > 0 ? 'info' : null);
            }
        } catch (e) {
            // Silently fail - dashboard may not be available
        }
    },

    async loadRalphBadge() {
        try {
            const resp = await this.apiCall('/ralph_loop_dashboard', {});
            if (resp.stats || resp.active_loops) {
                const activeCount = Array.isArray(resp.active_loops)
                    ? resp.active_loops.length
                    : (resp.stats?.active_loops || 0);
                this.updateTileBadge('ralph', activeCount, activeCount > 0 ? 'warning' : null);
            }
        } catch (e) {
            // Silently fail
        }
    },

    async loadCoworkBadge() {
        try {
            const resp = await this.apiCall('/cowork_approvals_list', {});
            if (resp.approvals) {
                const pendingCount = resp.approvals.filter(a => a.status === 'pending').length;
                this.updateTileBadge('cowork', pendingCount, pendingCount > 0 ? 'warning' : null);
            }
        } catch (e) {
            // Silently fail
        }
    },

    updateTileBadge(tileId, count, type) {
        const tile = this.tiles.find(t => t.id === tileId);
        if (tile) {
            tile.badge = count;
            tile.badgeType = type || 'info';
        }
    },

    // API helper
    async apiCall(endpoint, data) {
        const token = Alpine.store('csrfStore')?.token || '';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': token
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    },

    // Polling for badge updates
    startPolling() {
        if (this.pollingInterval) return;
        this.pollingInterval = setInterval(() => {
            this.loadBadges();
        }, 30000);  // Every 30 seconds
    },

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    },

    // Icon mapping (4 tiles only)
    getIconSvg(iconName) {
        const icons = {
            workflow: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>
                <path d="M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
            </svg>`,
            ralph: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-9-9"/>
                <polyline points="21 3 21 9 15 9"/>
            </svg>`,
            observability: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 3v18h18"/>
                <path d="M18 17V9"/>
                <path d="M13 17V5"/>
                <path d="M8 17v-3"/>
            </svg>`,
            cowork: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                <path d="M16 3.13a4 4 0 010 7.75"/>
            </svg>`
        };
        return icons[iconName] || icons.workflow;
    },

    // Check if tile is active
    isExpanded(tileId) {
        return this.expandedTile === tileId;
    }
};

// Register the store when Alpine loads
document.addEventListener('alpine:init', () => {
    Alpine.store('tileRowStore', tileRowModel);
});
