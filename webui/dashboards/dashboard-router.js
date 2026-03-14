/**
 * Dashboard Router Store - Alpine.js store for managing dashboard page navigation
 * Handles showing/hiding dashboard pages accessed via sidebar icons
 */

const dashboardRouterModel = {
    // State
    activeDashboard: null,  // null = show chat, 'portfolio' | 'workflows' = show dashboard
    loading: false,
    dashboardContent: '',

    // Available dashboards
    dashboards: {
        portfolio: {
            id: 'portfolio',
            label: 'Portfolio & Customers',
            icon: 'portfolio',
            component: 'dashboards/portfolio/portfolio-dashboard.html'
        },
        workflows: {
            id: 'workflows',
            label: 'Workflows & Training',
            icon: 'workflow',
            component: 'dashboards/workflows/workflow-dashboard.html'
        },
        mos: {
            id: 'mos',
            label: 'MOS Integration',
            icon: 'mos',
            component: 'dashboards/mos/mos-dashboard.html'
        }
    },

    // Navigation
    async showDashboard(dashboardId) {
        if (this.activeDashboard === dashboardId) {
            // Toggle off - return to chat
            this.closeDashboard();
            return;
        }

        const dashboard = this.dashboards[dashboardId];
        if (!dashboard) {
            console.error(`Unknown dashboard: ${dashboardId}`);
            return;
        }

        this.loading = true;
        this.activeDashboard = dashboardId;

        try {
            const storeLoader = {
                portfolio: () => import('/dashboards/portfolio/portfolio-store.js'),
                workflows: () => import('/dashboards/workflows/workflow-store.js'),
                mos: () => import('/dashboards/mos/mos-store.js')
            }[dashboardId];
            if (storeLoader) {
                await storeLoader();
            }
            const response = await fetch(dashboard.component);
            if (response.ok) {
                this.dashboardContent = await response.text();
            } else {
                this.dashboardContent = `<div class="dashboard-error">Failed to load ${dashboard.label}</div>`;
            }
        } catch (error) {
            console.error(`Error loading dashboard ${dashboardId}:`, error);
            this.dashboardContent = `<div class="dashboard-error">Error loading dashboard: ${error.message}</div>`;
        } finally {
            this.loading = false;
        }
    },

    closeDashboard() {
        this.activeDashboard = null;
        this.dashboardContent = '';
    },

    isDashboardActive(dashboardId) {
        return this.activeDashboard === dashboardId;
    },

    // Check if any dashboard is open
    isAnyDashboardOpen() {
        return this.activeDashboard !== null;
    },

    // Icon helpers
    getIconSvg(iconName) {
        const icons = {
            portfolio: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/>
            </svg>`,
            workflow: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>
                <path d="M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
            </svg>`,
            mos: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
            </svg>`
        };
        return icons[iconName] || icons.portfolio;
    }
};

// Register the store when Alpine loads
document.addEventListener('alpine:init', () => {
    Alpine.store('dashboardRouter', dashboardRouterModel);
});
