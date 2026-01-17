document.addEventListener('alpine:init', () => {
    Alpine.store('platformInfo', {
        content: '',
        isLoading: false,
        error: null,
        lastUpdated: null,

        async fetchDocumentation() {
            this.isLoading = true;
            this.error = null;
            try {
                const response = await fetch('/platform_documentation_get', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                const data = await response.json();
                if (data.success) {
                    this.content = data.content;
                    this.lastUpdated = new Date(data.last_updated * 1000).toLocaleString();
                } else {
                    this.error = data.error;
                }
            } catch (err) {
                this.error = "Failed to load documentation.";
                console.error(err);
            } finally {
                this.isLoading = false;
            }
        },

        renderMarkdown(markdown) {
            // Simple markdown renderer for the hub documentation
            if (!markdown) return '';
            
            let html = markdown
                .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/^\* (.*$)/gim, '<li>$1</li>')
                .replace(/^\- (.*$)/gim, '<li>$1</li>')
                .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
                .replace(/\*(.*)\*/gim, '<em>$1</em>')
                .replace(/`(.*?)`/gim, '<code>$1</code>')
                .replace(/\n/g, '<br>');
            
            return html;
        }
    });

    // Initial fetch when the store is initialized or tab is switched
    // We can trigger this from the component
});
