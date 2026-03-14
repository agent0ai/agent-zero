/**
 * MOS Dashboard Store - Alpine.js store for MOS (Linear/Motion/Notion) Dashboard
 * Fetches data from /mos_dashboard and /mos_sync_status API endpoints
 */

const mosDashboardModel = {
    // State
    loading: false,
    error: null,

    // Data
    linear: {},
    motion: {},
    pipeline: {},
    syncs: {},

    // Computed stats
    get totalLinearIssues() {
        const data = this.linear?.dashboard_data || this.linear;
        return data?.total_issues || data?.issue_count || 0;
    },

    get motionTaskCount() {
        return this.motion?.task_count || 0;
    },

    get pipelineLeads() {
        const p = this.pipeline;
        return p?.total_leads || p?.lead_count || 0;
    },

    get issuesByState() {
        const data = this.linear?.dashboard_data || this.linear;
        return data?.by_state || data?.issues_by_state || {};
    },

    get issuesByPriority() {
        const data = this.linear?.dashboard_data || this.linear;
        return data?.by_priority || data?.issues_by_priority || {};
    },

    // Lifecycle
    async init() {
        await Promise.all([this.loadDashboard(), this.loadSyncStatus()]);
    },

    // API methods
    async loadDashboard() {
        this.loading = true;
        this.error = null;
        try {
            const token = Alpine.store('csrfStore')?.token || '';
            const resp = await fetch('/mos_dashboard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': token
                },
                body: JSON.stringify({
                    include_linear: true,
                    include_motion: true,
                    include_pipeline: true
                })
            });
            const data = await resp.json();
            if (data.success) {
                this.linear = data.linear || {};
                this.motion = data.motion || {};
                this.pipeline = data.pipeline || {};
            } else {
                this.error = data.error || 'Failed to load MOS dashboard';
            }
        } catch (e) {
            console.error('Error loading MOS dashboard:', e);
            this.error = e.message;
        } finally {
            this.loading = false;
        }
    },

    async loadSyncStatus() {
        try {
            const token = Alpine.store('csrfStore')?.token || '';
            const resp = await fetch('/mos_sync_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': token
                },
                body: JSON.stringify({})
            });
            const data = await resp.json();
            if (data.success) {
                this.syncs = data.syncs || {};
            }
        } catch (e) {
            console.error('Error loading sync status:', e);
        }
    },

    async triggerSync(integration) {
        this.loading = true;
        try {
            const token = Alpine.store('csrfStore')?.token || '';
            const resp = await fetch('/mos_sync_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': token
                },
                body: JSON.stringify({ trigger_sync: integration })
            });
            const data = await resp.json();
            if (data.success) {
                // Reload both after sync
                await Promise.all([this.loadDashboard(), this.loadSyncStatus()]);
            }
        } catch (e) {
            console.error('Error triggering sync:', e);
            this.error = `Sync failed: ${e.message}`;
        } finally {
            this.loading = false;
        }
    },

    // Helpers
    formatDate(dateStr) {
        if (!dateStr) return 'Never';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    },

    getSyncStatusClass(sync) {
        if (!sync || sync.error) return 'sync-error';
        const last = sync.last_sync;
        if (!last) return 'sync-none';
        return last.status === 'success' ? 'sync-ok' : 'sync-error';
    },

    getSyncStatusText(sync) {
        if (!sync) return 'Not configured';
        if (sync.error) return 'Error';
        const last = sync.last_sync;
        if (!last) return 'No syncs yet';
        return last.status === 'success' ? 'OK' : 'Failed';
    },

    getStateColor(state) {
        const colors = {
            'backlog': '#718096',
            'todo': '#4299e1',
            'in_progress': '#ed8936',
            'in_review': '#805ad5',
            'done': '#48bb78',
            'cancelled': '#e53e3e',
            'triage': '#a0aec0'
        };
        return colors[state?.toLowerCase()] || '#718096';
    },

    getPriorityColor(priority) {
        const colors = {
            'urgent': '#e53e3e',
            'high': '#ed8936',
            'medium': '#ecc94b',
            'low': '#48bb78',
            'no_priority': '#718096'
        };
        return colors[priority?.toLowerCase()] || '#718096';
    }
};

// Register the store when Alpine is ready
const registerMosStore = () => {
    Alpine.store('mosDashboard', mosDashboardModel);
};

if (globalThis.Alpine) {
    registerMosStore();
} else {
    document.addEventListener('alpine:init', registerMosStore);
}
