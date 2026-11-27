import { toastFrontendNotice } from "/components/notifications/notification-store.js";
import { createStore } from "/js/AlpineStore.js";
import * as Sleep from "/js/sleep.js";

// define the model object holding data and functions
const model = {
  isLoading: false,
  authConfigured: null,
  tunnelLink: "",
  linkGenerated: false,
  loadingText: "",
  qrCodeInstance: null,
  provider: "cloudflared",
  loginProvider: "",
  microsoftLoginCode: "",
  microsoftLoginUrl: "",
  codeCopied: false,
  copyState: "",
  notificationPollInterval: null,
  hasError: false,

  init() {
    this.checkTunnelStatus();
  },

  cleanup() {
    this.stopNotificationPolling();
  },

  get copyLinkIcon() {
    if (this.copyState === "success") return "check";
    if (this.copyState === "error") return "close";
    return "content_copy";
  },

  get copyLinkLabel() {
    if (this.copyState === "success") return "Copied";
    if (this.copyState === "error") return "Copy failed";
    return "Copy link";
  },

  get loginActionVisible() {
    return Boolean(this.microsoftLoginUrl || this.microsoftLoginCode);
  },

  get loginActionTitle() {
    return this.loginProvider === "tailscale" ? "Tailscale sign-in" : "Microsoft sign-in";
  },

  get loginActionCopy() {
    if (this.loginProvider === "tailscale") {
      return "Open the Tailscale link to approve this container or enable Funnel. Agent Zero will continue when Tailscale reports the public URL.";
    }
    return "Approve the tunnel request, then Agent Zero will finish enabling Remote Control.";
  },

  clearMicrosoftLogin() {
    this.loginProvider = "";
    this.microsoftLoginCode = "";
    this.microsoftLoginUrl = "";
    this.codeCopied = false;
  },

  copyLoginCode() {
    if (!this.microsoftLoginCode) return;
    navigator.clipboard.writeText(this.microsoftLoginCode).then(() => {
      this.codeCopied = true;
      window.toastFrontendInfo("Login code copied to clipboard!", "Clipboard");
      // Reset after 3 seconds
      setTimeout(() => {
        this.codeCopied = false;
      }, 3000);
    }).catch((err) => {
      console.error("Failed to copy code: ", err);
      toastFrontendNotice("error", "Failed to copy login code", "Clipboard Error");
    });
  },

  processNotifications(notifications) {
    if (!notifications || !Array.isArray(notifications)) return;
    
    for (const n of notifications) {
      switch (n.event) {
        case "downloading":
          this.loadingText = n.message;
          break;
        case "download_progress":
          if (n.data && n.data.percent !== undefined) {
            this.loadingText = `Downloading: ${n.data.percent.toFixed(1)}%`;
          } else {
            this.loadingText = n.message;
          }
          break;
        case "download_complete":
          this.loadingText = n.message;
          break;
        case "creating_tunnel":
          this.clearMicrosoftLogin();
          this.loadingText = n.message;
          break;
        case "info":
          // Sign-in providers can provide a device code, a login URL, or both.
          if (n.data && n.data.url) {
            this.loginProvider = n.data.provider || (n.data.code ? "microsoft" : "tailscale");
            this.microsoftLoginCode = n.data.code || "";
            this.microsoftLoginUrl = n.data.url || "";
            this.loadingText = this.loginProvider === "tailscale"
              ? "Waiting for Tailscale approval..."
              : "Waiting for Microsoft login...";
          } else {
            this.loadingText = n.message;
          }
          break;
        case "error":
          this.hasError = true;
          window.toastFrontendError(n.message, "Remote Control");
          this.stopNotificationPolling();
          break;
        case "tunnel_url":
          if (n.data && n.data.url) {
            this.tunnelLink = n.data.url;
            this.linkGenerated = true;
            Sleep.Skip().then(() => this.generateQRCode());
          }
          break;
        case "tunnel_stopped":
          this.loadingText = n.message;
          break;
      }
    }
  },

  startNotificationPolling() {
    this.stopNotificationPolling();
    this.hasError = false;
    this.notificationPollInterval = setInterval(async () => {
      try {
        const response = await fetchApi("/api/plugins/_tunnel/tunnel", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "notifications" }),
        });
        const data = await response.json();
        if (data.notifications) {
          this.processNotifications(data.notifications);
        }
        // Check if tunnel is ready
        if (data.tunnel_url && data.is_running) {
          this.tunnelLink = data.tunnel_url;
          this.linkGenerated = true;
          Sleep.Skip().then(() => this.generateQRCode());
          this.stopNotificationPolling();
        }
      } catch (error) {
        console.error("Error polling notifications:", error);
      }
    }, 500);
  },

  stopNotificationPolling() {
    if (this.notificationPollInterval) {
      clearInterval(this.notificationPollInterval);
      this.notificationPollInterval = null;
    }
  },

  generateQRCode() {
    if (!this.tunnelLink) return;

    const qrContainer = document.getElementById("qrcode-tunnel");
    if (!qrContainer) return;

    // Clear any existing QR code
    qrContainer.innerHTML = "";

    try {
      // Generate new QR code
      this.qrCodeInstance = new QRCode(qrContainer, {
        text: this.tunnelLink,
        width: 128,
        height: 128,
        colorDark: "#000000",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.M,
      });
    } catch (error) {
      console.error("Error generating QR code:", error);
      qrContainer.innerHTML =
        '<div class="qr-error">QR code generation failed</div>';
    }
  },

  async checkTunnelStatus() {
    try {
      const response = await fetchApi("/api/plugins/_tunnel/tunnel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action: "get" }),
      });

      const data = await response.json();
      this.authConfigured = data.auth_configured === true;
      if (data.provider) this.provider = data.provider;

      if (data.success && data.tunnel_url) {
        // Update the stored URL if it's different from what we have
        if (this.tunnelLink !== data.tunnel_url) {
          this.tunnelLink = data.tunnel_url;
          localStorage.setItem("agent_zero_tunnel_url", data.tunnel_url);
        }
        this.linkGenerated = true;
        // Generate QR code for the tunnel URL
        Sleep.Skip().then(() => this.generateQRCode());
      } else {
        // Check if we have a stored tunnel URL
        const storedTunnelUrl = localStorage.getItem("agent_zero_tunnel_url");

        if (storedTunnelUrl) {
          // Use the stored URL but verify it's still valid
          const verifyResponse = await fetchApi("/api/plugins/_tunnel/tunnel", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ action: "verify", url: storedTunnelUrl }),
          });

          const verifyData = await verifyResponse.json();

          if (verifyData.success && verifyData.is_valid) {
            this.tunnelLink = storedTunnelUrl;
            this.linkGenerated = true;
            // Generate QR code for the tunnel URL
            Sleep.Skip().then(() => this.generateQRCode());
          } else {
            // Clear stale URL
            localStorage.removeItem("agent_zero_tunnel_url");
            this.tunnelLink = "";
            this.linkGenerated = false;
          }
        } else {
          // No stored URL, show the generate button
          this.tunnelLink = "";
          this.linkGenerated = false;
        }
      }
      return this.authConfigured;
    } catch (error) {
      this.authConfigured = null;
      console.error("Error checking tunnel status:", error);
      this.tunnelLink = "";
      this.linkGenerated = false;
    }
  },

  async requireAuth() {
    const provider = this.provider;
    const allowed = await this.checkTunnelStatus();
    this.provider = provider;
    if (allowed) return true;
    window.toastFrontendError(this.authConfigured === false
      ? "Set an Agent Zero login and password in Settings → Authentication before starting Remote Control."
      : "Unable to check sign-in settings. Try again.", "Remote Control");
    return false;
  },

  async refreshLink() {
    if (!await this.requireAuth()) return;
    // Call generate but with a confirmation first
    if (
      confirm(
        "Create new Remote Control access? The current URL will stop working."
      )
    ) {

      this.isLoading = true;
      this.hasError = false;
      this.clearMicrosoftLogin();
      this.loadingText = "Refreshing tunnel...";

      try {
        // First stop any existing tunnel
        const stopResponse = await fetchApi("/api/plugins/_tunnel/tunnel", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ action: "stop" }),
        });

        // Check if stopping was successful
        const stopData = await stopResponse.json();
        if (!stopData.success) {
          console.warn("Warning: Couldn't stop existing tunnel cleanly");
          // Continue anyway since we want to create a new one
        }

        // Then generate a new one
        await this.generateLink();
      } catch (error) {
        console.error("Error refreshing tunnel:", error);
        toastFrontendNotice("error", "Error refreshing Remote Control", "Remote Control");
      } finally {
        this.isLoading = false;
        this.loadingText = "";
      }
    }
  },

  async generateLink() {
    if (!await this.requireAuth()) return;

    this.isLoading = true;
    this.hasError = false;
    this.clearMicrosoftLogin();
    this.loadingText = "Starting tunnel...";

    // Start polling for notifications
    this.startNotificationPolling();

    try {
      // Call the backend API to create a tunnel
      const response = await fetchApi("/api/plugins/_tunnel/tunnel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          action: "create",
          provider: this.provider,
        }),
      });

      const data = await response.json();

      // Process any notifications from response
      if (data.notifications) {
        this.processNotifications(data.notifications);
      }

      // Check for error
      if (!data.success && data.message) {
        this.hasError = true;
        window.toastFrontendError(data.message, "Remote Control");
        console.error("Tunnel creation failed:", data);
        this.stopNotificationPolling();
        return;
      }

      if (data.success && data.tunnel_url) {
        // Store the tunnel URL in localStorage for persistence
        localStorage.setItem("agent_zero_tunnel_url", data.tunnel_url);

        this.tunnelLink = data.tunnel_url;
        this.linkGenerated = true;
        this.stopNotificationPolling();

        // Generate QR code for the tunnel URL
        Sleep.Skip().then(() => this.generateQRCode());

        // Show success message to confirm creation
        window.toastFrontendInfo(
          "Remote Control is ready",
          "Remote Control"
        );
      }
    } catch (error) {
      toastFrontendNotice("error", "Error creating Remote Control", "Remote Control");
      console.error("Error creating tunnel:", error);
    } finally {
      this.isLoading = false;
      this.loadingText = "";
      this.stopNotificationPolling();
      this.clearMicrosoftLogin();

    }
  },

  async stopTunnel() {
    if (
      confirm(
        "Stop Remote Control? The current URL will no longer be accessible."
      )
    ) {
      this.isLoading = true;
      this.loadingText = "Stopping tunnel...";

      try {
        // Call the backend to stop the tunnel
        const response = await fetchApi("/api/plugins/_tunnel/tunnel", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ action: "stop" }),
        });

        const data = await response.json();

        if (data.success) {
          // Clear the stored URL
          localStorage.removeItem("agent_zero_tunnel_url");

          // Clear QR code
          const qrContainer = document.getElementById("qrcode-tunnel");
          if (qrContainer) {
            qrContainer.innerHTML = "";
          }
          this.qrCodeInstance = null;

          // Update UI state
          this.tunnelLink = "";
          this.linkGenerated = false;

          window.toastFrontendInfo(
            "Remote Control stopped",
            "Remote Control"
          );
        } else {
          toastFrontendNotice("error", "Failed to stop Remote Control", "Remote Control");
        }
      } catch (error) {
        toastFrontendNotice("error", "Error stopping Remote Control", "Remote Control");
        console.error("Error stopping tunnel:", error);
      } finally {
        this.isLoading = false;
        this.loadingText = "";
      }
    }
  },

  copyToClipboard() {
    if (!this.tunnelLink) return;

    navigator.clipboard
      .writeText(this.tunnelLink)
      .then(() => {
        this.copyState = "success";

        // Show toast notification
        window.toastFrontendInfo(
          "Remote Control URL copied",
          "Clipboard"
        );

        // Reset button after 2 seconds
        setTimeout(() => {
          this.copyState = "";
        }, 2000);
      })
      .catch((err) => {
        console.error("Failed to copy URL: ", err);
        this.copyState = "error";
        toastFrontendNotice(
          "error",
          "Failed to copy Remote Control URL",
          "Clipboard Error"
        );

        // Reset button after 2 seconds
        setTimeout(() => {
          this.copyState = "";
        }, 2000);
      });
  },
};

// convert it to alpine store
const store = createStore("tunnelStore", model);

// export for use in other files
export { store };
