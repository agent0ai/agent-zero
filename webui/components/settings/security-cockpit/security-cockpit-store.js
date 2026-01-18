document.addEventListener('alpine:init', () => {
    Alpine.store('securityCockpit', {
        logs: [],
        isLoading: false,
        error: null,
        refreshInterval: null,

        async init() {
            await this.fetchLogs();
            // Auto-refresh every 30 seconds
            this.refreshInterval = setInterval(() => this.fetchLogs(), 30000);
        },

        async fetchLogs() {
            this.isLoading = true;
            try {
                const response = await fetch('/security_audit_get', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ limit: 50 })
                });
                const data = await response.json();
                if (data.success) {
                    this.logs = data.logs;
                    this.error = null;
                } else {
                    this.error = data.error;
                }
            } catch (err) {
                this.error = "Failed to connect to security API";
            } finally {
                this.isLoading = false;
            }
        },

        formatDate(timestamp) {
            if (!timestamp) return 'n/a';
            return new Date(timestamp).toLocaleString();
        },

        getStatusClass(status) {
            if (status === 'success') return 'security-status-success';
            if (status === 'warning' || status === 'fail') return 'security-status-danger';
            return 'security-status-neutral';
        }
    });
});
