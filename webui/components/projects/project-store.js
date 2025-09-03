import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";

// define the model object holding data and functions
const model = {
    isOpen: false,
    projects: [],
    activeProject: null,
    isLoading: false,
    loadingText: "Loading projects...",
    
    // New project form data
    newProject: {
        name: "",
        description: "",
        instructions: ""
    },
    
    // Edit project form data
    editProject: {
        name: "",
        description: "",
        instructions: ""
    },
    
    // UI state
    currentView: "list", // "list", "create", "edit"
    editingProjectName: null,
    error: null,

    // gets called when the store is created
    init() {
        console.log("Project store initialized");
        this.loadProjects();
    },

    async openModal() {
        console.log("Opening project modal");
        this.isOpen = true;
        this.currentView = "list";
        this.error = null;
        await this.loadProjects();
    },

    closeModal() {
        console.log("Closing project modal");
        this.isOpen = false;
        this.currentView = "list";
        this.resetForms();
        this.error = null;
    },

    async loadProjects() {
        this.isLoading = true;
        this.loadingText = "Loading projects...";
        this.error = null;
        
        try {
            const rawResponse = await fetchApi('/project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'list' })
            });
            
            const response = await rawResponse.json();
            
            if (response.success) {
                this.projects = response.projects || [];
                console.log("Projects loaded:", this.projects);
                console.log("First project structure:", this.projects[0]);
                
                // Load active project
                await this.loadActiveProject();
            } else {
                this.error = response.error || "Failed to load projects";
                console.error("Failed to load projects:", response.error);
            }
        } catch (error) {
            this.error = "Network error while loading projects";
            console.error("Error loading projects:", error);
        } finally {
            this.isLoading = false;
        }
    },

    async loadActiveProject() {
        try {
            const rawResponse = await fetchApi('/project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    action: 'get_active',
                    context: window.getContext()
                })
            });
            
            const response = await rawResponse.json();
            
            if (response.success) {
                this.activeProject = response.active_project;
                console.log("Active project loaded:", this.activeProject);
            }
        } catch (error) {
            console.error("Error loading active project:", error);
        }
    },

    async createProject() {
        if (!this.validateNewProject()) {
            return;
        }

        this.isLoading = true;
        this.loadingText = "Creating project...";
        this.error = null;
        
        try {
            const rawResponse = await fetchApi('/project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'create',
                    ...this.newProject
                })
            });
            
            const response = await rawResponse.json();
            console.log("Create project response:", response);
            
            if (response.success) {
                console.log("Project created successfully");
                await this.loadProjects();
                this.resetForms();
                this.currentView = "list";
                
                // Show success message
                if (window.toast) {
                    window.toast("Project created successfully", "success");
                }
            } else {
                this.error = response.error || "Failed to create project";
                console.error("Failed to create project:", response.error);
            }
        } catch (error) {
            this.error = "Network error while creating project";
            console.error("Error creating project:", error);
        } finally {
            this.isLoading = false;
        }
    },

    async activateProject(projectName) {
        console.log("Activating project with name:", projectName, "Type:", typeof projectName);
        
        if (!projectName || typeof projectName !== 'string' || projectName.trim() === '') {
            this.error = "Invalid project name provided";
            console.error("Invalid project name:", projectName);
            return;
        }
        
        this.isLoading = true;
        this.loadingText = `Activating project ${projectName}...`;
        this.error = null;
        
        try {
            const payload = {
                action: 'activate',
                name: projectName,
                context: window.getContext()
            };
            console.log("Sending activate payload:", payload);
            
            const rawResponse = await fetchApi('/project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const response = await rawResponse.json();
            
            if (response.success) {
                console.log(`Project ${projectName} activated successfully`);
                this.activeProject = response.project;
                
                // Show success message
                if (window.toast) {
                    window.toast(`Project "${projectName}" activated`, "success");
                }
            } else {
                this.error = response.error || `Failed to activate project ${projectName}`;
                console.error("Failed to activate project:", response.error);
            }
        } catch (error) {
            this.error = "Network error while activating project";
            console.error("Error activating project:", error);
        } finally {
            this.isLoading = false;
        }
    },

    async deactivateProject() {
        this.isLoading = true;
        this.loadingText = "Deactivating project...";
        this.error = null;
        
        try {
            const rawResponse = await fetchApi('/project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    action: 'deactivate',
                    context: window.getContext()
                })
            });
            
            const response = await rawResponse.json();
            
            if (response.success) {
                console.log("Project deactivated successfully");
                this.activeProject = null;
                
                // Show success message
                if (window.toast) {
                    window.toast("Project deactivated", "success");
                }
            } else {
                this.error = response.error || "Failed to deactivate project";
                console.error("Failed to deactivate project:", response.error);
            }
        } catch (error) {
            this.error = "Network error while deactivating project";
            console.error("Error deactivating project:", error);
        } finally {
            this.isLoading = false;
        }
    },

    async updateProject() {
        if (!this.validateEditProject()) {
            return;
        }

        this.isLoading = true;
        this.loadingText = "Updating project...";
        this.error = null;
        
        try {
            const rawResponse = await fetchApi('/project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'update',
                    name: this.editingProjectName,
                    description: this.editProject.description,
                    instructions: this.editProject.instructions
                })
            });
            
            const response = await rawResponse.json();
            
            if (response.success) {
                console.log("Project updated successfully");
                await this.loadProjects();
                this.resetForms();
                this.currentView = "list";
                
                // Show success message
                if (window.toast) {
                    window.toast("Project updated successfully", "success");
                }
            } else {
                this.error = response.error || "Failed to update project";
                console.error("Failed to update project:", response.error);
            }
        } catch (error) {
            this.error = "Network error while updating project";
            console.error("Error updating project:", error);
        } finally {
            this.isLoading = false;
        }
    },

    // UI actions
    showCreateForm() {
        this.currentView = "create";
        this.resetForms();
        this.error = null;
    },

    showEditForm(project) {
        this.currentView = "edit";
        this.editingProjectName = project.name;
        this.editProject = {
            name: project.name,
            description: project.description || "",
            instructions: project.instructions || ""
        };
        this.error = null;
    },

    showList() {
        this.currentView = "list";
        this.resetForms();
        this.error = null;
    },

    resetForms() {
        this.newProject = {
            name: "",
            description: "",
            instructions: ""
        };
        
        this.editProject = {
            name: "",
            description: "",
            instructions: ""
        };
        
        this.editingProjectName = null;
    },

    validateNewProject() {
        if (!this.newProject.name.trim()) {
            this.error = "Project name is required";
            return false;
        }
        
        if (!this.newProject.description.trim()) {
            this.error = "Project description is required";
            return false;
        }
        
        // Check for duplicate project names
        if (this.projects.some(p => p.name.toLowerCase() === this.newProject.name.toLowerCase())) {
            this.error = "A project with this name already exists";
            return false;
        }
        
        return true;
    },

    validateEditProject() {
        if (!this.editProject.name.trim()) {
            this.error = "Project name is required";
            return false;
        }
        
        if (!this.editProject.description.trim()) {
            this.error = "Project description is required";
            return false;
        }
        
        // Check for duplicate project names (excluding current project)
        if (this.editProject.name.toLowerCase() !== this.editingProjectName.toLowerCase()) {
            if (this.projects.some(p => p.name.toLowerCase() === this.editProject.name.toLowerCase())) {
                this.error = "A project with this name already exists";
                return false;
            }
        }
        
        return true;
    },

    // Utility methods
    isProjectActive(projectName) {
        return this.activeProject && this.activeProject.name === projectName;
    },

    getProjectCount() {
        return this.projects.length;
    },

    hasActiveProject() {
        return this.activeProject !== null;
    },

    // Event handlers
    handleEscapeKey(event) {
        if (event.key === 'Escape') {
            if (this.currentView !== "list") {
                this.showList();
            } else {
                this.closeModal();
            }
        }
    }
};

// convert it to alpine store
const store = createStore("projectStore", model);

// export for use in other files
export { store };