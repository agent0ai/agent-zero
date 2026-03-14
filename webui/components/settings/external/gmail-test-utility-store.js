import * as API from "/js/api.js";

export const store = {
    accounts: [],
    loadingAccounts: false,
    oauthLoading: false,
    sendLoading: false,
    errorMessage: "",
    statusMessage: "",
    errorContext: "",
    accountName: "",
    selectedAccount: "",
    testTo: "",
    testSubject: "Agent Jumbo Gmail Test",
    testBody: "This is a test email from Agent Jumbo Gmail UI.",
    lastSendResult: null,
    credentialsJson: "",
    credentialsEditor: null,
    aceReady: false,

    async initialize() {
        await this.fetchAccounts();
        this.initCredentialsEditor();
    },

    setError(message, context) {
        this.errorMessage = message;
        this.errorContext = context || "";
    },

    setStatus(message) {
        this.statusMessage = message;
        this.errorMessage = "";
        this.errorContext = "";
    },

    initCredentialsEditor() {
        if (this.credentialsEditor) return;
        const container = document.getElementById("gmail-test-credentials-editor");
        if (!container || typeof ace === "undefined") {
            this.aceReady = false;
            return;
        }

        const editor = ace.edit("gmail-test-credentials-editor");
        const dark = localStorage.getItem("darkMode");
        if (dark != "false") {
            editor.setTheme("ace/theme/github_dark");
        } else {
            editor.setTheme("ace/theme/tomorrow");
        }

        editor.session.setMode("ace/mode/json");
        editor.setValue(this.credentialsJson || "");
        editor.clearSelection();
        editor.session.on("change", () => {
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
            this.setError(`Invalid JSON: ${error.message}`, "oauth");
        }
    },

    clearCredentials() {
        if (this.credentialsEditor) {
            this.credentialsEditor.setValue("");
            this.credentialsEditor.clearSelection();
        }
        this.credentialsJson = "";
    },

    loadCredentialsFromFile(event) {
        const file = event.target.files && event.target.files[0];
        if (!file) {
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            const text = String(reader.result || "");
            if (this.credentialsEditor) {
                this.credentialsEditor.setValue(text);
                this.credentialsEditor.clearSelection();
            }
            this.credentialsJson = text;
        };
        reader.readAsText(file);
        event.target.value = "";
    },

    async fetchAccounts() {
        this.loadingAccounts = true;
        try {
            const response = await API.fetchApi("/gmail_accounts_list", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            });
            if (response && response.ok) {
                const data = await response.json();
                this.accounts = data.accounts || [];
                if (!this.selectedAccount && this.accounts.length === 1) {
                    this.selectedAccount = this.accounts[0].name;
                }
                const selected = this.accounts.find((account) => account.name === this.selectedAccount);
                if (selected && !this.testTo && selected.email) {
                    this.testTo = selected.email;
                }
                this.setStatus("Account list refreshed.");
            } else {
                const error = response ? await response.text() : "Failed to fetch accounts";
                this.setError(error, "accounts");
            }
        } catch (error) {
            this.setError(`Failed to fetch accounts: ${error.message}`, "accounts");
        } finally {
            this.loadingAccounts = false;
        }
    },

    async startOAuth() {
        const accountName = this.accountName.trim();
        if (!accountName) {
            this.setError("Account name is required.", "oauth");
            return;
        }
        const credentialsJson = this.getCredentialsJson();
        if (!credentialsJson) {
            this.setError("Paste or upload credentials.json content first.", "oauth");
            return;
        }
        try {
            JSON.parse(credentialsJson);
        } catch (error) {
            this.setError(`Invalid credentials JSON: ${error.message}`, "oauth");
            return;
        }

        this.oauthLoading = true;
        try {
            const response = await API.fetchApi("/gmail_oauth_start", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    account_name: accountName,
                    credentials_json: credentialsJson
                })
            });

            if (response && response.ok) {
                const data = await response.json();
                const authUrl = data.authorization_url || data.auth_url;
                if (!authUrl) {
                    this.setError("OAuth start succeeded but no authorization URL returned.", "oauth");
                    return;
                }
                window.open(authUrl, "gmail_auth", "width=600,height=700");
                this.accountName = "";
                this.clearCredentials();
                this.setStatus("OAuth started. Complete the consent flow in the popup.");
                this.pollForNewAccount();
            } else {
                const error = response ? await response.text() : "OAuth start failed";
                this.setError(error, "oauth");
            }
        } catch (error) {
            this.setError(`OAuth start failed: ${error.message}`, "oauth");
        } finally {
            this.oauthLoading = false;
        }
    },

    pollForNewAccount() {
        let attempts = 0;
        const interval = setInterval(async () => {
            attempts++;
            await this.fetchAccounts();
            if (attempts > 60) {
                clearInterval(interval);
            }
        }, 5000);
    },

    async sendTestEmail() {
        if (!this.selectedAccount) {
            this.setError("Select an account to send the test email.", "send");
            return;
        }
        if (!this.testTo) {
            this.setError("Recipient email is required.", "send");
            return;
        }

        this.sendLoading = true;
        try {
            const data = await API.callJsonApi("/gmail_test_send", {
                account_name: this.selectedAccount,
                to: this.testTo,
                subject: this.testSubject,
                body: this.testBody
            });
            if (data && data.success) {
                this.lastSendResult = data;
                this.setStatus("Test email sent successfully.");
            } else {
                this.setError(data.error || "Failed to send test email.", "send");
            }
        } catch (error) {
            this.setError(`Failed to send test email: ${error.message}`, "send");
        } finally {
            this.sendLoading = false;
        }
    },

    onAccountSelect() {
        const selected = this.accounts.find((account) => account.name === this.selectedAccount);
        if (selected && selected.email) {
            this.testTo = selected.email;
        }
    },

    onClose() {
        if (this.credentialsEditor) {
            this.credentialsEditor.destroy();
            this.credentialsEditor = null;
        }
        this.aceReady = false;
    }
};

if (window.Alpine) {
    window.Alpine.store("gmailTestUtilityStore", store);
}
