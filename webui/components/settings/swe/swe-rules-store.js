/**
 * Store for SWE Agent Rules Generator
 */
// Note: Not using imports to ensure compatibility with Alpine.js registration

class SweRulesStore {
    constructor() {
        this.loading = false;
        this.error = null;
        this.success = null;
        this.generated = false;
        this.editing = false;
        this.loadingMessage = '';
        
        // Form fields
        this.projectDescription = '';
        this.techStack = '';
        this.codingStandards = '';
        this.testingApproach = '';
        
        // Generated content
        this.generatedContent = '';
        this.originalContent = '';
    }

    init() {
        console.log('SWE Rules Store initialized');
        this.clearMessages();
    }

    onClose() {
        // Cleanup when component is destroyed
        this.clearForm();
        this.clearMessages();
    }

    clearForm() {
        this.projectDescription = '';
        this.techStack = '';
        this.codingStandards = '';
        this.testingApproach = '';
        this.generated = false;
        this.editing = false;
        this.generatedContent = '';
        this.originalContent = '';
        this.clearMessages();
    }

    clearMessages() {
        this.error = null;
        this.success = null;
    }

    async generateAgentsMd() {
        if (!this.projectDescription.trim()) {
            this.error = 'Project description is required';
            return;
        }

        this.loading = true;
        this.loadingMessage = 'Analyzing your project and generating rules...';
        this.clearMessages();

        try {
            // Get CSRF token
            const csrfToken = await this.getCsrfToken();
            
            const response = await fetch('/swe_generate_agents_md', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({
                    project_description: this.projectDescription,
                    tech_stack: this.techStack,
                    coding_standards: this.codingStandards,
                    testing_approach: this.testingApproach
                })
            });

            const result = await response.json();

            if (result.success) {
                this.generatedContent = result.agents_md_content;
                this.originalContent = result.agents_md_content;
                this.generated = true;
                this.success = 'AGENTS.md generated successfully! You can now copy and use it with SWE agents.';
            } else {
                this.error = `Generation failed: ${result.error}`;
            }

        } catch (error) {
            console.error('Generation error:', error);
            this.error = `Generation failed: ${error.message}`;
        } finally {
            this.loading = false;
            this.loadingMessage = '';
        }
    }

    async getCsrfToken() {
        try {
            const response = await fetch('/csrf_token', {
                method: 'GET',
                credentials: 'same-origin'
            });
            const data = await response.json();
            return data.token;
        } catch (error) {
            console.error('Failed to get CSRF token:', error);
            throw new Error('Authentication failed');
        }
    }

    editRules() {
        this.editing = true;
        this.clearMessages();
    }

    saveEdit() {
        this.originalContent = this.generatedContent;
        this.editing = false;
        this.success = 'Rules updated successfully!';
    }

    cancelEdit() {
        this.generatedContent = this.originalContent;
        this.editing = false;
        this.clearMessages();
    }

    async copyToClipboard() {
        try {
            await navigator.clipboard.writeText(this.generatedContent);
            this.success = 'AGENTS.md content copied to clipboard!';
        } catch (error) {
            console.error('Copy failed:', error);
            this.error = 'Failed to copy to clipboard. Please select and copy manually.';
        }
    }

    downloadFile() {
        try {
            const blob = new Blob([this.generatedContent], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'AGENTS.md';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            this.success = 'AGENTS.md file downloaded successfully!';
        } catch (error) {
            console.error('Download failed:', error);
            this.error = 'Failed to download file.';
        }
    }

    generateNew() {
        this.generated = false;
        this.editing = false;
        this.generatedContent = '';
        this.originalContent = '';
        this.clearMessages();
    }

    // Helper method to validate form
    isFormValid() {
        return this.projectDescription.trim().length > 0;
    }

    // Method to get form data for API
    getFormData() {
        return {
            project_description: this.projectDescription.trim(),
            tech_stack: this.techStack.trim(),
            coding_standards: this.codingStandards.trim(),
            testing_approach: this.testingApproach.trim()
        };
    }
}

// Create and make the store available globally for Alpine.js registration
window.sweRulesStore = new SweRulesStore();