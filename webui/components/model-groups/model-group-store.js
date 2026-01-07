import { createStore } from "/js/AlpineStore.js";

const model = {
    // State
    groups: [],                     // All model groups
    activeGroupId: "",              // Currently active model group ID
    dropdownOpen: false,            // Dropdown menu open state
    managerOpen: false,             // Manager modal open state
    editorOpen: false,              // Editor modal open state
    editingGroup: null,             // Currently editing model group
    isCreating: false,              // Whether creating a new model group
    loading: false,                 // Loading state
    saveDialogOpen: false,          // Save dialog open state
    saveDialogName: "",             // Save dialog name input
    saveDialogDesc: "",             // Save dialog description input
    
    // Provider lists
    chatProviders: [],
    embedProviders: [],
    
    // Computed properties
    get activeGroupName() {
        if (!this.activeGroupId) return null;
        const group = this.groups.find(g => g.id === this.activeGroupId);
        return group?.name || null;
    },
    
    get activeGroup() {
        if (!this.activeGroupId) return null;
        return this.groups.find(g => g.id === this.activeGroupId) || null;
    },
    
    // Get current chat model provider
    get currentChatProvider() {
        const group = this.activeGroup;
        return group?.chat_model_provider || "";
    },
    
    // Get provider icon (SVG) based on chat model provider
    getProviderIcon(provider = null) {
        const providerName = (provider || this.currentChatProvider || "").toLowerCase();
        
        const icons = {
            'openai': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.516 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.896zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/></svg>',
            'github': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .3a12 12 0 0 0-3.8 23.38c.6.12.83-.26.83-.57L9 21.07c-3.34.72-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.08-.74.09-.73.09-.73 1.2.09 1.83 1.24 1.83 1.24 1.07 1.83 2.81 1.3 3.5 1 .1-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.14-.3-.54-1.52.1-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.28-1.55 3.29-1.23 3.29-1.23.64 1.66.24 2.88.12 3.18a4.65 4.65 0 0 1 1.23 3.22c0 4.61-2.8 5.63-5.48 5.92.42.36.81 1.1.81 2.22 0 1.6-.01 2.89-.01 3.29 0 .31.2.69.82.57A12 12 0 0 0 12 .3Z"/></svg>',
            'anthropic': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M13.827 3.52h3.603L24 20h-3.603l-6.57-16.48zm-7.258 0h3.767L16.906 20h-3.674l-1.343-3.461H5.017L3.635 20H0l6.569-16.48zm2.327 10.018l-2.26-5.887-2.26 5.887h4.52z"/></svg>',
            'google': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/></svg>',
            'mistral': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3.428 3.4h3.429v3.428h3.429v3.429h-.002 3.431V6.828h3.427V3.4h3.43v13.714H24v3.429H13.714v-3.428h-3.428v-3.429h-3.43v3.428h3.43v3.429H0v-3.429h3.428V3.4zm10.286 13.715h3.428v-3.429h-3.427v3.429z"/></svg>',
            'ollama': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M7.905 1.09c.216.085.411.225.588.41.295.306.544.744.734 1.263.191.522.315 1.1.362 1.68a5.054 5.054 0 012.049-.636l.051-.004c.87-.07 1.73.087 2.48.474.101.053.2.11.297.17.05-.569.172-1.134.36-1.644.19-.52.439-.957.733-1.264a1.67 1.67 0 01.589-.41c.257-.1.53-.118.796-.042.401.114.745.368 1.016.737.248.337.434.769.561 1.287.23.934.27 2.163.115 3.645l.053.04.026.019c.757.576 1.284 1.397 1.563 2.35.435 1.487.216 3.155-.534 4.088l-.018.021.002.003c.417.762.67 1.567.724 2.4l.002.03c.064 1.065-.2 2.137-.814 3.19l-.007.01.01.024c.472 1.157.62 2.322.438 3.486l-.006.039a.651.651 0 01-.747.536.648.648 0 01-.54-.742c.167-1.033.01-2.069-.48-3.123a.643.643 0 01.04-.617l.004-.006c.604-.924.854-1.83.8-2.72-.046-.779-.325-1.544-.8-2.273a.644.644 0 01.18-.886l.009-.006c.243-.159.467-.565.58-1.12a4.229 4.229 0 00-.095-1.974c-.205-.7-.58-1.284-1.105-1.683-.595-.454-1.383-.673-2.38-.61a.653.653 0 01-.632-.371c-.314-.665-.772-1.141-1.343-1.436a3.288 3.288 0 00-1.772-.332c-1.245.099-2.343.801-2.67 1.686a.652.652 0 01-.61.425c-1.067.002-1.893.252-2.497.703-.522.39-.878.935-1.066 1.588a4.07 4.07 0 00-.068 1.886c.112.558.331 1.02.582 1.269l.008.007c.212.207.257.53.109.785-.36.622-.629 1.549-.673 2.44-.05 1.018.186 1.902.719 2.536l.016.019a.643.643 0 01.095.69c-.576 1.236-.753 2.252-.562 3.052a.652.652 0 01-1.269.298c-.243-1.018-.078-2.184.473-3.498l.014-.035-.008-.012a4.339 4.339 0 01-.598-1.309l-.005-.019a5.764 5.764 0 01-.177-1.785c.044-.91.278-1.842.622-2.59l.012-.026-.002-.002c-.293-.418-.51-.953-.63-1.545l-.005-.024a5.352 5.352 0 01.093-2.49c.262-.915.777-1.701 1.536-2.269.06-.045.123-.09.186-.132-.159-1.493-.119-2.73.112-3.67.127-.518.314-.95.562-1.287.27-.368.614-.622 1.015-.737.266-.076.54-.059.797.042zm4.116 9.09c.936 0 1.8.313 2.446.855.63.527 1.005 1.235 1.005 1.94 0 .888-.406 1.58-1.133 2.022-.62.375-1.451.557-2.403.557-1.009 0-1.871-.259-2.493-.734-.617-.47-.963-1.13-.963-1.845 0-.707.398-1.417 1.056-1.946.668-.537 1.55-.849 2.485-.849zm0 .896a3.07 3.07 0 00-1.916.65c-.461.37-.722.835-.722 1.25 0 .428.21.829.61 1.134.455.347 1.124.548 1.943.548.799 0 1.473-.147 1.932-.426.463-.28.7-.686.7-1.257 0-.423-.246-.89-.683-1.256-.484-.405-1.14-.643-1.864-.643zm.662 1.21l.004.004c.12.151.095.37-.056.49l-.292.23v.446a.375.375 0 01-.376.373.375.375 0 01-.376-.373v-.46l-.271-.218a.347.347 0 01-.052-.49.353.353 0 01.494-.051l.215.172.22-.174a.353.353 0 01.49.051zm-5.04-1.919c.478 0 .867.39.867.871a.87.87 0 01-.868.871.87.87 0 01-.867-.87.87.87 0 01.867-.872zm8.706 0c.48 0 .868.39.868.871a.87.87 0 01-.868.871.87.87 0 01-.867-.87.87.87 0 01.867-.872zM7.44 2.3l-.003.002a.659.659 0 00-.285.238l-.005.006c-.138.189-.258.467-.348.832-.17.692-.216 1.631-.124 2.782.43-.128.899-.208 1.404-.237l.01-.001.019-.034c.046-.082.095-.161.148-.239.123-.771.022-1.692-.253-2.444-.134-.364-.297-.65-.453-.813a.628.628 0 00-.107-.09L7.44 2.3zm9.174.04l-.002.001a.628.628 0 00-.107.09c-.156.163-.32.45-.453.814-.29.794-.387 1.776-.23 2.572l.058.097.008.014h.03a5.184 5.184 0 011.466.212c.086-1.124.038-2.043-.128-2.722-.09-.365-.21-.643-.349-.832l-.004-.006a.659.659 0 00-.285-.239h-.004z"></path></svg>',
            'groq': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12.036 2c-3.853-.035-7 3-7.036 6.781-.035 3.782 3.055 6.872 6.908 6.907h2.42v-2.566h-2.292c-2.407.028-4.38-1.866-4.408-4.23-.029-2.362 1.901-4.298 4.308-4.326h.1c2.407 0 4.358 1.915 4.365 4.278v6.305c0 2.342-1.944 4.25-4.323 4.279a4.375 4.375 0 01-3.033-1.252l-1.851 1.818A7 7 0 0012.029 22h.092c3.803-.056 6.858-3.083 6.879-6.816V8.872C18.964 5.046 15.889 2.035 12.036 2z"/></svg>',
            'openrouter': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M16.804 1.957l7.22 4.105v.087L16.73 10.21l.017-2.117-.821-.03c-1.059-.028-1.611.002-2.268.11-1.064.175-2.038.577-3.147 1.352L8.345 11.03c-.284.195-.495.336-.68.455l-.515.322-.397.234.385.23.53.338c.476.314 1.17.796 2.701 1.866 1.11.775 2.083 1.177 3.147 1.352l.3.045c.694.091 1.375.094 2.825.033l.022-2.159 7.22 4.105v.087L16.589 22l.014-1.862-.635.022c-1.386.042-2.137.002-3.045-.113-1.393-.176-2.604-.676-3.917-1.59l-1.91-1.329c-.457-.315-.814-.56-1.156-.78l-.777-.487c-.428-.266-.882-.548-1.312-.806-.65-.39-1.382-.791-1.819-1.051-.495-.294-.884-.6-1.222-.916-.544-.51-.918-1.05-1.206-1.673-.433-1.155-.376-2.418.166-3.527.358-.727.908-1.329 1.61-1.865.463-.355.977-.636 1.509-.88.351-.16.714-.305 1.069-.445l.793-.308.802-.323c.346-.148.694-.295 1.068-.458l1.889-1.314c1.313-.915 2.524-1.415 3.917-1.59.908-.115 1.659-.155 3.045-.113l.635.022-.014-1.862L16.804 1.957z"/></svg>',
            'azure': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M16.233 0c.713 0 1.345.551 1.572 1.329.227.778 1.555 5.59 1.555 5.59v9.562h-4.813L14.645 0h1.588z" fill-opacity=".5"/><path d="M23.298 7.47c0-.34-.275-.6-.6-.6h-2.835a3.617 3.617 0 00-3.614 3.615v5.996h3.436a3.617 3.617 0 003.613-3.614V7.47z"/><path d="M16.233 0a.982.982 0 00-.989.989l-.097 18.198A4.814 4.814 0 0110.334 24H1.6a.597.597 0 01-.567-.794l7-19.981A4.819 4.819 0 0112.57 0h3.679-.016z"/></svg>',
        };
        
        // Check for provider match
        for (const [key, icon] of Object.entries(icons)) {
            if (providerName.includes(key)) return icon;
        }
        
        // Default icon (grid view)
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect></svg>';
    },
    
    // Get provider icon for a specific group
    getProviderIconForGroup(group) {
        return this.getProviderIcon(group?.chat_model_provider || "");
    },
    
    // Initialize - wait for backend connection before loading
    async init() {
        // Try initial load
        await this.loadGroups();
        await this.loadProviders();
        
        // If groups not loaded and backend might not be connected yet, retry after delay
        if (this.groups.length === 0) {
            setTimeout(async () => {
                await this.loadGroups();
                await this.loadProviders();
            }, 1500);
        }
    },
    
    // Load model groups list
    async loadGroups() {
        try {
            const response = await globalThis.sendJsonData("/model_groups_list", {});
            if (response.ok) {
                this.groups = response.groups || [];
                this.activeGroupId = response.active_group_id || "";
            }
        } catch (e) {
            console.error("Error loading model groups:", e);
        }
    },
    
    // Load providers list
    async loadProviders() {
        try {
            const response = await globalThis.sendJsonData("/model_groups_providers", {});
            if (response.ok) {
                this.chatProviders = response.chat_providers || [];
                this.embedProviders = response.embed_providers || [];
            }
        } catch (e) {
            console.error("Error loading providers:", e);
        }
    },
    
    // Toggle dropdown
    toggleDropdown() {
        this.dropdownOpen = !this.dropdownOpen;
    },

    closeDropdown() {
        this.dropdownOpen = false;
    },
    
    // Switch model group
    async switchGroup(groupId) {
        this.loading = true;
        try {
            const response = await globalThis.sendJsonData("/model_groups_switch", { 
                group_id: groupId 
            });
            
            if (response.ok) {
                this.activeGroupId = groupId || "";
                
                // Get group name for notification
                let groupName = 'Default';
                if (groupId) {
                    const group = this.groups.find(g => g.id === groupId);
                    groupName = group?.name || 'Unknown';
                }
                
                this.closeDropdown();
                
                // Show notification with group name
                if (globalThis.Alpine?.store && globalThis.Alpine.store('notificationStore')) {
                    const notifStore = globalThis.Alpine.store('notificationStore');
                    notifStore.frontendSuccess(
                        `Switched to "${groupName}"`,
                        'Model Group',
                        3,
                        '',
                        10
                    );
                }
            } else {
                throw new Error(response.error || "Failed to switch model group");
            }
        } catch (e) {
            console.error("Error switching model group:", e);
            if (globalThis.toastFetchError) {
                globalThis.toastFetchError("Error switching model group", e);
            }
        } finally {
            this.loading = false;
        }
    },
    
    // Open save dialog
    openSaveDialog() {
        this.saveDialogName = "";
        this.saveDialogDesc = "";
        this.saveDialogOpen = true;
        this.closeDropdown();
    },
    
    // Close save dialog
    closeSaveDialog() {
        this.saveDialogOpen = false;
        this.saveDialogName = "";
        this.saveDialogDesc = "";
    },
    
    // Save current config as new model group
    async saveCurrentAsNew() {
        this.openSaveDialog();
    },
    
    // Confirm save dialog
    async confirmSave() {
        const name = this.saveDialogName?.trim();
        if (!name) return;
        
        this.loading = true;
        try {
            const response = await globalThis.sendJsonData("/model_groups_save", { 
                name: name,
                description: this.saveDialogDesc?.trim() || ""
            });
            
            if (response.ok) {
                await this.loadGroups();
                this.closeSaveDialog();
                
                const notifStore = globalThis.Alpine?.store('notificationStore');
                if (notifStore) {
                    notifStore.frontendSuccess(
                        "Current configuration saved as new model group",
                        "Model Group",
                        2
                    );
                }
            } else {
                throw new Error(response.error || "Failed to save model group");
            }
        } catch (e) {
            console.error("Error saving model group:", e);
            if (globalThis.toastFetchError) {
                globalThis.toastFetchError("Error saving model group", e);
            }
        } finally {
            this.loading = false;
        }
    },
    
    // Open manager modal
    openManager() {
        this.managerOpen = true;
        this.closeDropdown();
    },
    
    closeManager() {
        this.managerOpen = false;
    },
    
    // Create new model group
    createNew() {
        const store = globalThis.Alpine?.store('modelGroups');
        if (store) {
            store.isCreating = true;
            store.editingGroup = {
                name: "",
                description: "",
                chat_model_provider: "",
                chat_model_name: "",
                chat_model_api_base: "",
                util_model_provider: "",
                util_model_name: "",
                util_model_api_base: "",
                browser_model_provider: "",
                browser_model_name: "",
                browser_model_api_base: "",
                embed_model_provider: "huggingface",
                embed_model_name: "sentence-transformers/all-MiniLM-L6-v2",
                embed_model_api_base: "",
            };
            store.editorOpen = true;
        }
    },
    
    // Edit model group
    edit(groupId) {
        const store = globalThis.Alpine?.store('modelGroups');
        const group = this.groups.find(g => g.id === groupId);
        if (!group || !store) return;
        
        store.isCreating = false;
        
        // Set editingGroup first with deep copy
        store.editingGroup = JSON.parse(JSON.stringify(group));
        
        // Then open editor after data is set, with double nextTick to ensure DOM and Alpine bindings are ready
        if (globalThis.Alpine) {
            globalThis.Alpine.nextTick(() => {
                globalThis.Alpine.nextTick(() => {
                    store.editorOpen = true;
                });
            });
        } else {
            store.editorOpen = true;
        }
    },
    
    closeEditor() {
        const store = globalThis.Alpine?.store('modelGroups');
        if (store) {
            store.editorOpen = false;
            store.editingGroup = null;
            store.isCreating = false;
        }
    },
    
    // Save edit
    async saveEdit() {
        if (!this.editingGroup) return;
        
        const name = this.editingGroup.name?.trim();
        if (!name) {
            alert("Name is required");
            return;
        }
        
        this.loading = true;
        try {
            let response;
            if (this.isCreating) {
                response = await globalThis.sendJsonData("/model_groups_create", this.editingGroup);
            } else {
                response = await globalThis.sendJsonData("/model_groups_update", {
                    group_id: this.editingGroup.id,
                    ...this.editingGroup
                });
            }
            
            if (response.ok) {
                await this.loadGroups();
                this.closeEditor();
                
                const notifStore = globalThis.Alpine?.store('notificationStore');
                if (notifStore) {
                    notifStore.frontendSuccess(
                        this.isCreating ? "Model group created" : "Model group updated",
                        "Model Group",
                        2
                    );
                }
            } else {
                throw new Error(response.error || "Failed to save model group");
            }
        } catch (e) {
            console.error("Error saving model group:", e);
            if (globalThis.toastFetchError) {
                globalThis.toastFetchError("Error saving model group", e);
            }
        } finally {
            this.loading = false;
        }
    },
    
    // Duplicate model group
    async duplicate(groupId) {
        this.loading = true;
        try {
            const response = await globalThis.sendJsonData("/model_groups_duplicate", { 
                group_id: groupId 
            });
            
            if (response.ok) {
                await this.loadGroups();
                
                const notifStore = globalThis.Alpine?.store('notificationStore');
                if (notifStore) {
                    notifStore.frontendSuccess(
                        "Model group duplicated",
                        "Model Group",
                        2
                    );
                }
            } else {
                throw new Error(response.error || "Failed to duplicate model group");
            }
        } catch (e) {
            console.error("Error duplicating model group:", e);
            if (globalThis.toastFetchError) {
                globalThis.toastFetchError("Error duplicating model group", e);
            }
        } finally {
            this.loading = false;
        }
    },
    
    // Delete model group
    async deleteGroup(groupId) {
        const group = this.groups.find(g => g.id === groupId);
        if (!group) return;
        
        this.loading = true;
        try {
            const response = await globalThis.sendJsonData("/model_groups_delete", { 
                group_id: groupId 
            });
            
            if (response.ok) {
                await this.loadGroups();
                
                const notifStore = globalThis.Alpine?.store('notificationStore');
                if (notifStore) {
                    notifStore.frontendSuccess(
                        "Model group deleted",
                        "Model Group",
                        2
                    );
                }
            } else {
                throw new Error(response.error || "Failed to delete model group");
            }
        } catch (e) {
            console.error("Error deleting model group:", e);
            if (globalThis.toastFetchError) {
                globalThis.toastFetchError("Error deleting model group", e);
            }
        } finally {
            this.loading = false;
        }
    },
    
    // Export model group
    async exportGroup(groupId) {
        const group = this.groups.find(g => g.id === groupId);
        if (!group) return;
        
        // Create export data (remove id)
        const exportData = { ...group };
        delete exportData.id;
        delete exportData.created_at;
        
        // Download as JSON file
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `model-group-${group.name.replace(/[^a-z0-9]/gi, "_")}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },
    
    // Import model group
    async importGroup() {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".json";
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                const text = await file.text();
                const data = JSON.parse(text);
                
                this.loading = true;
                const response = await globalThis.sendJsonData("/model_groups_create", data);
                
                if (response.ok) {
                    await this.loadGroups();
                    
                    const notifStore = globalThis.Alpine?.store('notificationStore');
                    if (notifStore) {
                        notifStore.frontendSuccess(
                            "Model group imported",
                            "Model Group",
                            2
                        );
                    }
                } else {
                    throw new Error(response.error || "Failed to import model group");
                }
            } catch (e) {
                console.error("Error importing model group:", e);
                if (globalThis.toastFetchError) {
                    globalThis.toastFetchError("Error importing model group", e);
                }
            } finally {
                this.loading = false;
            }
        };
        
        input.click();
    }
};

export const store = createStore("modelGroups", model);