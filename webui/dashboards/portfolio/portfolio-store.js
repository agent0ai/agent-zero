/**
 * Portfolio Dashboard Store - Alpine.js store for Portfolio Dashboard
 * Manages customers, projects, and unified CRM view
 */

const portfolioDashboardModel = {
    // State
    loading: false,
    activeTab: 'dashboard',  // dashboard, customers, projects
    error: null,

    // Data
    stats: {
        total_customers: 0,
        active_customers: 0,
        total_projects: 0,
        active_projects: 0,
        pipeline_value: 0,
        health_avg: 0
    },
    customers: [],
    projects: [],

    // Filters
    customerStageFilter: 'all',
    customerSearch: '',
    projectStatusFilter: 'all',
    projectSearch: '',

    // Selection
    selectedCustomer: null,
    selectedProject: null,

    // Customer stages for filtering
    customerStages: [
        { value: 'all', label: 'All Stages' },
        { value: 'lead', label: 'Lead' },
        { value: 'discovery', label: 'Discovery' },
        { value: 'requirements', label: 'Requirements' },
        { value: 'proposal', label: 'Proposal' },
        { value: 'negotiation', label: 'Negotiation' },
        { value: 'implementation', label: 'Implementation' },
        { value: 'active', label: 'Active' },
        { value: 'churned', label: 'Churned' }
    ],

    // Project statuses for filtering
    projectStatuses: [
        { value: 'all', label: 'All Statuses' },
        { value: 'active', label: 'Active' },
        { value: 'in_development', label: 'In Development' },
        { value: 'maintenance', label: 'Maintenance' },
        { value: 'archived', label: 'Archived' }
    ],

    // Computed - filtered customers
    get filteredCustomers() {
        let result = [...this.customers];

        if (this.customerStageFilter && this.customerStageFilter !== 'all') {
            result = result.filter(c => c.stage === this.customerStageFilter);
        }

        if (this.customerSearch) {
            const search = this.customerSearch.toLowerCase();
            result = result.filter(c =>
                (c.name || '').toLowerCase().includes(search) ||
                (c.company || '').toLowerCase().includes(search) ||
                (c.email || '').toLowerCase().includes(search)
            );
        }

        return result;
    },

    // Computed - filtered projects
    get filteredProjects() {
        let result = [...this.projects];

        if (this.projectStatusFilter && this.projectStatusFilter !== 'all') {
            result = result.filter(p => p.status === this.projectStatusFilter);
        }

        if (this.projectSearch) {
            const search = this.projectSearch.toLowerCase();
            result = result.filter(p =>
                (p.name || '').toLowerCase().includes(search) ||
                (p.description || '').toLowerCase().includes(search)
            );
        }

        return result;
    },

    // Lifecycle
    async init() {
        await this.loadDashboard();
    },

    // Tab switching
    setTab(tab) {
        this.activeTab = tab;
        this.selectedCustomer = null;
        this.selectedProject = null;
    },

    // API methods
    async loadDashboard() {
        this.loading = true;
        this.error = null;
        try {
            const token = Alpine.store('csrfStore')?.token || '';
            const resp = await fetch('/portfolio_dashboard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': token
                },
                body: JSON.stringify({
                    include_customers: true,
                    include_projects: true
                })
            });
            const data = await resp.json();
            if (data.success) {
                this.stats = data.stats || this.stats;
                this.customers = data.customers || [];
                this.projects = data.projects || [];
            } else {
                this.error = data.error || 'Failed to load dashboard';
            }
        } catch (e) {
            console.error('Error loading portfolio dashboard:', e);
            this.error = e.message;
        } finally {
            this.loading = false;
        }
    },

    async loadCustomers() {
        this.loading = true;
        try {
            const token = Alpine.store('csrfStore')?.token || '';
            const resp = await fetch('/customer_list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': token
                },
                body: JSON.stringify({
                    stage: this.customerStageFilter,
                    search: this.customerSearch
                })
            });
            const data = await resp.json();
            if (data.success) {
                this.customers = data.customers || [];
            }
        } catch (e) {
            console.error('Error loading customers:', e);
        } finally {
            this.loading = false;
        }
    },

    async loadProjects() {
        this.loading = true;
        try {
            const token = Alpine.store('csrfStore')?.token || '';
            const resp = await fetch('/project_list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': token
                },
                body: JSON.stringify({
                    status: this.projectStatusFilter,
                    search: this.projectSearch
                })
            });
            const data = await resp.json();
            if (data.success) {
                this.projects = data.projects || [];
            }
        } catch (e) {
            console.error('Error loading projects:', e);
        } finally {
            this.loading = false;
        }
    },

    async selectCustomer(customerId) {
        this.loading = true;
        try {
            const token = Alpine.store('csrfStore')?.token || '';
            const resp = await fetch('/customer_detail', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': token
                },
                body: JSON.stringify({ customer_id: customerId })
            });
            const data = await resp.json();
            if (data.success) {
                this.selectedCustomer = data.customer;
            }
        } catch (e) {
            console.error('Error loading customer:', e);
        } finally {
            this.loading = false;
        }
    },

    async selectProject(projectId) {
        this.loading = true;
        try {
            const token = Alpine.store('csrfStore')?.token || '';
            const resp = await fetch('/project_detail', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': token
                },
                body: JSON.stringify({ project_id: projectId })
            });
            const data = await resp.json();
            if (data.success) {
                this.selectedProject = data.project;
            }
        } catch (e) {
            console.error('Error loading project:', e);
        } finally {
            this.loading = false;
        }
    },

    deselectCustomer() {
        this.selectedCustomer = null;
    },

    deselectProject() {
        this.selectedProject = null;
    },

    // Helpers
    formatCurrency(value) {
        if (!value) return '$0';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    },

    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    getStageColor(stage) {
        const colors = {
            'lead': '#718096',
            'discovery': '#4299e1',
            'requirements': '#805ad5',
            'proposal': '#ed8936',
            'negotiation': '#dd6b20',
            'implementation': '#38a169',
            'active': '#48bb78',
            'churned': '#e53e3e'
        };
        return colors[stage] || '#718096';
    },

    getStatusColor(status) {
        const colors = {
            'active': '#48bb78',
            'in_development': '#4299e1',
            'maintenance': '#ed8936',
            'archived': '#718096'
        };
        return colors[status] || '#718096';
    },

    getHealthClass(score) {
        if (score >= 80) return 'health-good';
        if (score >= 60) return 'health-medium';
        return 'health-poor';
    }
};

// Register the store when Alpine is ready
const registerPortfolioStore = () => {
    Alpine.store('portfolioDashboard', portfolioDashboardModel);
};

if (globalThis.Alpine) {
    registerPortfolioStore();
} else {
    document.addEventListener('alpine:init', registerPortfolioStore);
}
