import { callJsonApi } from "/js/api.js";

const model = {
    isPasskeySupported: window.PublicKeyCredential !== undefined,
    registeredPasskeys: [],
    loading: false,
    error: null,
    
    async init() {
        await this.loadPasskeys();
        
        // Listen for system-wide auth requests
        window.addEventListener('notification-added', (e) => {
            const notification = e.detail;
            if (notification.type === 'auth_required' || notification.type === 'auth-gate') {
                this.handleAuthGate(notification);
            }
        });
    },
    
    async handleAuthGate(notification) {
        if (confirm(`${notification.title}\n\n${notification.message}\n\nVerify with Mobile Passkey now?`)) {
            await this.authenticate();
        }
    },
    
    async loadPasskeys() {
        // This would list registered passkeys for the user
        // For simplicity, we'll just check if we have any during auth check
    },
    
    async registerPasskey() {
        this.loading = true;
        this.error = null;
        try {
            // 1. Get options from server
            const optionsResp = await callJsonApi("/passkey_auth", { 
                action: "get_registration_options",
                username: "AgentZeroUser"
            });
            
            if (!optionsResp.success) throw new Error(optionsResp.error);
            
            const options = optionsResp.options;
            
            // Convert base64 strings to ArrayBuffers
            options.challenge = this.urlBase64ToBuffer(options.challenge);
            options.user.id = this.urlBase64ToBuffer(options.user.id);
            if (options.excludeCredentials) {
                options.excludeCredentials.forEach(c => c.id = this.urlBase64ToBuffer(c.id));
            }
            
            // 2. Create credential on device (phone)
            const credential = await navigator.credentials.create({ publicKey: options });
            
            // 3. Verify on server
            const response = {
                id: credential.id,
                rawId: this.bufferToUrlBase64(credential.rawId),
                type: credential.type,
                response: {
                    attestationObject: this.bufferToUrlBase64(credential.response.attestationObject),
                    clientDataJSON: this.bufferToUrlBase64(credential.response.clientDataJSON),
                },
            };
            
            const verifyResp = await callJsonApi("/passkey_auth", {
                action: "verify_registration",
                challenge: optionsResp.options.challenge,
                response: response
            });
            
            if (verifyResp.success) {
                alert("Mobile Passkey Registered Successfully!");
                await this.loadPasskeys();
            } else {
                throw new Error(verifyResp.error);
            }
            
        } catch (err) {
            console.error("Passkey Error:", err);
            this.error = err.message;
        } finally {
            this.loading = false;
        }
    },
    
    async authenticate() {
        this.loading = true;
        this.error = null;
        try {
            // 1. Get options from server
            const optionsResp = await callJsonApi("/passkey_auth", { 
                action: "get_authentication_options"
            });
            
            if (!optionsResp.success) throw new Error(optionsResp.error);
            
            const options = optionsResp.options;
            options.challenge = this.urlBase64ToBuffer(options.challenge);
            if (options.allowCredentials) {
                options.allowCredentials.forEach(c => c.id = this.urlBase64ToBuffer(c.id));
            }
            
            // 2. Get assertion from device (phone)
            const assertion = await navigator.credentials.get({ publicKey: options });
            
            // 3. Verify on server
            const response = {
                id: assertion.id,
                rawId: this.bufferToUrlBase64(assertion.rawId),
                type: assertion.type,
                response: {
                    authenticatorData: this.bufferToUrlBase64(assertion.response.authenticatorData),
                    clientDataJSON: this.bufferToUrlBase64(assertion.response.clientDataJSON),
                    signature: this.bufferToUrlBase64(assertion.response.signature),
                    userHandle: assertion.response.userHandle ? this.bufferToUrlBase64(assertion.response.userHandle) : null,
                },
            };
            
            const verifyResp = await callJsonApi("/passkey_auth", {
                action: "verify_authentication",
                challenge: optionsResp.options.challenge,
                response: response
            });
            
            if (verifyResp.success) {
                if (window.toast) toast("Identity Verified. Operation Authorized.", "success");
                return true;
            } else {
                throw new Error(verifyResp.error);
            }
        } catch (err) {
            console.error("Auth Error:", err);
            this.error = err.message;
            if (window.toast) toast(err.message, "error");
            return false;
        } finally {
            this.loading = false;
        }
    },
    
    // Helpers
    urlBase64ToBuffer(base64) {
        const bin = window.atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
        const buf = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
        return buf.buffer;
    },
    
    bufferToUrlBase64(buffer) {
        const bin = String.fromCharCode(...new Uint8Array(buffer));
        return window.btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    }
};

export const store = model;
