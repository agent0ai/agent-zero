/**
 * Project Modal JavaScript for Agent Zero
 * 
 * This module handles the project management modal interface,
 * including creating, listing, editing, and activating projects.
 * Follows Alpine.js patterns used throughout the Agent Zero UI.
 */

const projectModalProxy = {
    isOpen: false,
    isLoading: false,
    error: '',
    success: '',
    
    // Modal states
    currentView: 'list', // 'list', 'create', 'edit'
    
    // Project list data
    projects: [],
    activeProject: null,
    
    // Form data
    formData: {
        name: '',
        description: '',
        instructions: ''
    },
    
    // Edit mode data
    editingProject: null,

    /**
     * Open the project modal
     */
    async openModal() {
        this.isOpen = true;
        this.error = '';
        this.success = '';
        this.currentView = 'list';
        
        // Force update the Alpine component
        const modal = document.getElementById('projectModal');
        if (modal && window.Alpine) {
            const alpineData = window.Alpine.$data(modal);
            if (alpineData) {
                alpineData.isOpen = true;
                alpineData.error = this.error;
                alpineData.success = this.success;
                alpineData.currentView = this.currentView;
                alpineData.activeProject = this.activeProject;
                alpineData.projects = this.projects;
            } else {
                // Fallback: directly show the modal element
                modal.style.display = 'block';
            }
        }
        
        await this.loadProjects();
        await this.loadActiveProject();
    },

    /**
     * Close the modal and reset state
     */
    handleClose() {
        this.isOpen = false;
        this.error = '';
        this.success = '';
        this.currentView = 'list';
        this.resetForm();
        this.editingProject = null;
    },

    /**
     * Load all available projects from the API
     */
    async loadProjects() {
        this.isLoading = true;
        this.error = '';
        
        try {
            const response = await window.fetchApi('/project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'list'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.projects = data.projects || [];
                
                // Also update the Alpine component if it exists
                if (this._alpineComponent) {
                    this._alpineComponent.projects = this.projects;
                    this._alpineComponent.error = this.error;
                    this._alpineComponent.success = this.success;
                    this._alpineComponent.isLoading = this.isLoading;
                    this._alpineComponent.activeProject = this.activeProject;
                }
                
                // Update the header project indicator
                this.updateHeaderIndicator();
            } else {
                this.error = data.error || 'Failed to load projects';
                this.projects = [];
            }
        } catch (error) {
            this.error = 'Network error while loading projects';
            console.error('Project loading error:', error);
            if (window.toastFetchError) {
                window.toastFetchError('Error loading projects', error);
            }
            this.projects = [];
            
            // Update Alpine component for error case too
            if (this._alpineComponent) {
                this._alpineComponent.error = this.error;
                this._alpineComponent.projects = this.projects;
            }
        } finally {
            this.isLoading = false;
            
            // Update Alpine component for loading state
            if (this._alpineComponent) {
                this._alpineComponent.isLoading = this.isLoading;
            }
        }
    },

    /**
     * Load the currently active project
     */
    async loadActiveProject() {
        try {
            const response = await window.fetchApi('/project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'get_active',
                    context: this.getCurrentContext()
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.active_project) {
                this.activeProject = data.active_project;
            } else {
                this.activeProject = null;
            }
            
            // Also update the Alpine component
            if (this._alpineComponent) {
                this._alpineComponent.activeProject = this.activeProject;
            }
            
            // Update the header project indicator
            this.updateHeaderIndicator();
        } catch (error) {
            console.error('Error loading active project:', error);
            if (window.toastFetchError) {
                window.toastFetchError('Error loading active project', error);
            }
            this.activeProject = null;
        }
    },

    /**
     * Show the create project form
     */
    showCreateForm() {
        this.currentView = 'create';
        this.resetForm();
        this.error = '';
        this.success = '';
    },

    /**
     * Show the edit project form
     */
    showEditForm(project) {
        this.currentView = 'edit';
        this.editingProject = project;
        this.formData = {
            name: project.name,
            description: project.description,
            instructions: project.instructions
        };
        this.error = '';
        this.success = '';
    },

    /**
     * Go back to the project list view
     */
    showListView() {
        this.currentView = 'list';
        this.resetForm();
        this.editingProject = null;
        this.error = '';
        this.success = '';
    },

    /**
     * Reset the form data
     */
    resetForm() {
        this.formData = {
            name: '',
            description: '',
            instructions: ''
        };
    },

    /**
     * Create a new project
     */
    async createProject() {
        if (!this.formData.name.trim()) {
            this.error = 'Project name is required';
            return;
        }

        this.isLoading = true;
        this.error = '';
        this.success = '';

        try {
            const response = await window.fetchApi('/project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'create',
                    name: this.formData.name.trim(),
                    description: this.formData.description.trim(),
                    instructions: this.formData.instructions.trim()
                })
            });

            const data = await response.json();

            if (data.success) {
                this.success = `Project '${data.project.name}' created successfully!`;
                this.resetForm();
                await this.loadProjects();
                
                // Optionally switch back to list view after a delay
                setTimeout(() => {
                    this.showListView();
                }, 2000);
            } else {
                this.error = data.error || 'Failed to create project';
            }
        } catch (error) {
            this.error = 'Network error while creating project';
            console.error('Project creation error:', error);
            if (window.toastFetchError) {
                window.toastFetchError('Error creating project', error);
            }
        } finally {
            this.isLoading = false;
        }
    },

    /**
     * Update an existing project
     */
    async updateProject() {
        if (!this.editingProject) {
            this.error = 'No project selected for editing';
            return;
        }

        this.isLoading = true;
        this.error = '';
        this.success = '';

        try {
            const response = await window.fetchApi('/project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'update',
                    name: this.editingProject.name,
                    description: this.formData.description.trim(),
                    instructions: this.formData.instructions.trim()
                })
            });

            const data = await response.json();

            if (data.success) {
                this.success = `Project '${this.editingProject.name}' updated successfully!`;
                await this.loadProjects();
                
                // Update active project if it was the one being edited
                if (this.activeProject && this.activeProject.name === this.editingProject.name) {
                    await this.loadActiveProject();
                }
                
                // Switch back to list view after a delay
                setTimeout(() => {
                    this.showListView();
                }, 2000);
            } else {
                this.error = data.error || 'Failed to update project';
            }
        } catch (error) {
            this.error = 'Network error while updating project';
            console.error('Project update error:', error);
            if (window.toastFetchError) {
                window.toastFetchError('Error updating project', error);
            }
        } finally {
            this.isLoading = false;
        }
    },

    /**
     * Activate a project
     */
    async activateProject(projectName) {
        this.isLoading = true;
        this.error = '';
        this.success = '';

        try {
            const response = await window.fetchApi('/project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'activate',
                    name: projectName,
                    context: this.getCurrentContext()
                })
            });

            const data = await response.json();

            if (data.success) {
                this.success = data.message || `Project '${projectName}' activated!`;
                await this.loadActiveProject();
                
                // Refresh the page to update the UI with the new project context
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                this.error = data.error || 'Failed to activate project';
            }
        } catch (error) {
            this.error = 'Network error while activating project';
            console.error('Project activation error:', error);
            if (window.toastFetchError) {
                window.toastFetchError('Error activating project', error);
            }
        } finally {
            this.isLoading = false;
        }
    },

    /**
     * Deactivate the current project
     */
    async deactivateProject() {
        this.isLoading = true;
        this.error = '';
        this.success = '';

        try {
            const response = await window.fetchApi('/project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'deactivate',
                    context: this.getCurrentContext()
                })
            });

            const data = await response.json();

            if (data.success) {
                this.success = data.message || 'Project deactivated!';
                await this.loadActiveProject();
                
                // Refresh the page to update the UI
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                this.error = data.error || 'Failed to deactivate project';
            }
        } catch (error) {
            this.error = 'Network error while deactivating project';
            console.error('Project deactivation error:', error);
            if (window.toastFetchError) {
                window.toastFetchError('Error deactivating project', error);
            }
        } finally {
            this.isLoading = false;
        }
    },

    /**
     * Get the current agent context ID
     */
    getCurrentContext() {
        // Try to get context from index.js module if it's available
        if (window.getContext && typeof window.getContext === 'function') {
            return window.getContext();
        }
        
        // Try to get from Alpine store
        if (window.Alpine && window.Alpine.store('root')) {
            const store = window.Alpine.store('root');
            if (store.context) {
                return store.context;
            }
        }
        
        // Try to get from chats section (current selected chat)
        const chatsSection = document.getElementById('chats-section');
        if (chatsSection && window.Alpine) {
            const chatsAD = window.Alpine.$data(chatsSection);
            if (chatsAD && chatsAD.selected) {
                return chatsAD.selected;
            }
        }
        
        // Fallback to empty string (server will use current session context)
        return '';
    },

    /**
     * Format instructions for display (truncate if too long)
     */
    formatInstructions(instructions, maxLength = 150) {
        if (!instructions) return 'No instructions provided';
        if (instructions.length <= maxLength) return instructions;
        return instructions.substring(0, maxLength) + '...';
    },

    /**
     * Get display status for a project
     */
    getProjectStatus(project) {
        if (this.activeProject && this.activeProject.name === project.name) {
            return 'ACTIVE';
        }
        return '';
    },
    
    /**
     * Update the header project indicator
     */
    updateHeaderIndicator() {
        const indicator = document.getElementById('active-project-indicator');
        if (indicator && window.Alpine) {
            const alpineData = window.Alpine.$data(indicator);
            if (alpineData) {
                alpineData.activeProject = this.activeProject;
            }
        }
    }
};

// Wait for Alpine to be ready
document.addEventListener('alpine:init', () => {
    Alpine.data('projectModalProxy', () => ({
        init() {
            Object.assign(this, projectModalProxy);
            
            // Create a reference so we can update this component from the global object
            projectModalProxy._alpineComponent = this;
        }
    }));
});

// Keep the global assignment for backward compatibility
window.projectModalProxy = projectModalProxy;

// Export a simple function to open the modal
window.openProjectModal = function() {
    return projectModalProxy.openModal();
};

// Initialize the header indicator after a short delay
setTimeout(() => {
    if (window.projectModalProxy) {
        window.projectModalProxy.loadActiveProject();
    }
}, 1000);