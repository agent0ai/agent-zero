import { callJsonApi } from "/js/api.js";

const model = {
    auditLogs: [],
    loading: false,
    enforced: false,
    
    async init() {
        await this.loadLogs();
        // Check current enforcement status if possible
    },

    async loadLogs() {
        this.loading = true;
        try {
            const resp = await callJsonApi("/security_ops", { action: "get_audit_logs", limit: 30 });
            if (resp.success) {
                this.auditLogs = resp.logs;
            }
        } catch (err) {
            console.error("Failed to load security logs", err);
        } finally {
            this.loading = false;
        }
    },

    async triggerPanicLock() {
        if (!confirm("🚨 PANIC LOCK: This will immediately revoke all authorized sessions. You will need to re-verify your identity via Passkey for all high-risk tools. Proceed?")) {
            return;
        }

        try {
            const resp = await callJsonApi("/security_ops", { action: "panic_lock" });
            if (resp.success) {
                if (window.toast) toast("PANIC LOCK ACTIVATED: All sessions revoked.", "error");
                // Refresh logs to show the panic event
                await this.loadLogs();
            }
        } catch (err) {
            console.error("Panic lock failed", err);
        }
    },

    formatTime(timestamp) {
        if (!timestamp) return "";
        const date = new Date(timestamp + "Z"); // Assume UTC
        return date.toLocaleTimeString() + ' ' + date.toLocaleDateString();
    },

    getEventIcon(type) {
        const icons = {
            'session_authorized': 'verified_user',
            'unauthorized_tool_attempt': 'block',
            'panic_lock_triggered': 'report_problem',
            'profile_sync': 'sync',
            'passkey_reg_verify': 'app_registration',
            'rate_limit_exceeded': 'speed'
        };
        return icons[type] || 'security';
    },

    getEventColor(status) {
        if (status === 'success') return 'text-success';
        if (status === 'blocked' || status === 'warning') return 'text-danger';
        return 'text-warning';
    }
};

export default model;
