
export const store = {
    accounts: [],
    loading: false,
    showAddForm: false,
    newAccountName: '',
    credentialsJson: '',
    credentialsEditor: null,
    aceReady: false,

    async initialize() {
        await this.fetchAccounts();
        this.initCredentialsEditor();
    },

    async fetchAccounts() {
        this.loading = true;
        try {
            const response = await fetch('/gmail_accounts_list', {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': window.csrfToken || ''
                }
            });
            if (response.ok) {
                const data = await response.json();
                this.accounts = data.accounts || [];
            }
        } catch (error) {
            console.error('Error fetching Gmail accounts:', error);
        } finally {
            this.loading = false;
        }
    },

    toggleAddForm() {
        this.showAddForm = !this.showAddForm;
        if (this.showAddForm) {
            this.initCredentialsEditor();
            if (this.credentialsEditor) {
                setTimeout(() => this.credentialsEditor.resize(), 0);
            }
        }
    },

    initCredentialsEditor() {
        if (this.credentialsEditor) return;
        const container = document.getElementById('gmail-credentials-editor');
        if (!container || typeof ace === 'undefined') {
            this.aceReady = false;
            return;
        }

        const editor = ace.edit('gmail-credentials-editor');
        const dark = localStorage.getItem('darkMode');
        if (dark != 'false') {
            editor.setTheme('ace/theme/github_dark');
        } else {
            editor.setTheme('ace/theme/tomorrow');
        }

        editor.session.setMode('ace/mode/json');
        editor.setValue(this.credentialsJson || '');
        editor.clearSelection();
        editor.session.on('change', () => {
            this.credentialsJson = editor.getValue();
        });

        this.credentialsEditor = editor;
        this.aceReady = true;
    },

    getCredentialsJson() {
        if (this.credentialsEditor) {
            return this.credentialsEditor.getValue();
        }
        return this.credentialsJson;
    },

    formatCredentialsJson() {
        const content = this.getCredentialsJson();
        if (!content) {
            return;
        }
        try {
            const parsed = JSON.parse(content);
            const formatted = JSON.stringify(parsed, null, 2);
            if (this.credentialsEditor) {
                this.credentialsEditor.setValue(formatted);
                this.credentialsEditor.clearSelection();
                this.credentialsEditor.navigateFileStart();
            } else {
                this.credentialsJson = formatted;
            }
        } catch (error) {
            alert(`Invalid JSON: ${error.message}`);
        }
    },

    clearCredentials() {
        if (this.credentialsEditor) {
            this.credentialsEditor.setValue('');
            this.credentialsEditor.clearSelection();
        }
        this.credentialsJson = '';
    },

    loadCredentialsFromFile(event) {
        const file = event.target.files && event.target.files[0];
        if (!file) {
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            const text = String(reader.result || '');
            if (this.credentialsEditor) {
                this.credentialsEditor.setValue(text);
                this.credentialsEditor.clearSelection();
            }
            this.credentialsJson = text;
        };
        reader.readAsText(file);
        event.target.value = '';
    },

    async removeAccount(accountName) {
        if (!confirm(`Are you sure you want to remove account "${accountName}"?`)) return;

        try {
            const response = await fetch('/gmail_account_remove', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.csrfToken || ''
                },
                body: JSON.stringify({ account_name: accountName })
            });

            if (response.ok) {
                await this.fetchAccounts();
                if (window.Alpine && window.Alpine.store('notificationStore')) {
                    window.Alpine.store('notificationStore').frontendInfo(`Account "${accountName}" removed.`, 'Gmail Manager');
                }
            } else {
                const error = await response.json();
                alert(`Error: ${error.error}`);
            }
        } catch (error) {
            console.error('Error removing account:', error);
        }
    },

    async startOAuth() {
        if (!this.newAccountName) {
            alert('Please enter an account name.');
            return;
        }
        const credentialsJson = this.getCredentialsJson();
        if (!credentialsJson) {
            alert('Please paste the content of your credentials.json file.');
            return;
        }
        try {
            JSON.parse(credentialsJson);
        } catch (error) {
            alert(`Invalid credentials JSON: ${error.message}`);
            return;
        }

        try {
            const response = await fetch('/gmail_oauth_start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.csrfToken || ''
                },
                body: JSON.stringify({
                    account_name: this.newAccountName,
                    credentials_json: credentialsJson
                })
            });

            if (response.ok) {
                const data = await response.json();
                const authUrl = data.authorization_url || data.auth_url;
                if (authUrl) {
                    // Open OAuth URL in a new window
                    window.open(authUrl, 'gmail_auth', 'width=600,height=700');
                    
                    // Close the "Add" form and wait for the user to complete auth
                    this.showAddForm = false;
                    this.newAccountName = '';
                    this.clearCredentials();
                    
                    if (window.Alpine && window.Alpine.store('notificationStore')) {
                        window.Alpine.store('notificationStore').frontendInfo('OAuth process started. Please complete authentication in the popup window.', 'Gmail Manager');
                    }
                    
                    // Start polling for account refresh
                    this.pollForNewAccount();
                }
            } else {
                const error = await response.json();
                alert(`Error: ${error.error}`);
            }
        } catch (error) {
            console.error('Error starting OAuth:', error);
        }
    },

    pollForNewAccount() {
        let attempts = 0;
        const interval = setInterval(async () => {
            attempts++;
            await this.fetchAccounts();
            
            // If we have more than 60 attempts (5 minutes), stop polling
            if (attempts > 60) {
                clearInterval(interval);
            }
        }, 5000);
        
        // Stop polling if the window is closed (how to detect?)
        // For now just poll for a while.
    },

    onClose() {
        // Cleanup if needed
        if (this.credentialsEditor) {
            this.credentialsEditor.destroy();
            this.credentialsEditor = null;
        }
        this.aceReady = false;
    }
};

// Register the store with Alpine
if (window.Alpine) {
    window.Alpine.store('gmailAccountManagerStore', store);
}
