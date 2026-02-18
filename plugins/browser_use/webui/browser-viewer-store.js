import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
    // State
    connected: false,
    agentBusy: false,
    currentUrl: "",
    currentTitle: "",
    alive: false,
    error: null,

    // Internal
    _ws: null,
    _canvas: null,
    _ctx: null,
    _pollInterval: null,
    _initialized: false,

    init() {
        if (this._initialized) return;
        this._initialized = true;
    },

    // Called when modal opens (via x-create)
    async open(canvasEl) {
        this._canvas = canvasEl;
        this._ctx = canvasEl.getContext("2d");
        this.error = null;

        try {
            const result = await callJsonApi("/api/plugins/browser_use/browser_use_connect", {
                action: "start",
                context_id: getCurrentContextId(),
            });

            if (result.error) {
                this.error = result.error;
                return;
            }

            this.connected = true;
            this.currentUrl = result.url || "";
            this._startPolling();
        } catch (e) {
            this.error = `Failed to connect: ${e.message}`;
        }
    },

    _startPolling() {
        this._pollInterval = setInterval(async () => {
            try {
                const status = await callJsonApi("/api/plugins/browser_use/browser_use_connect", {
                    action: "status",
                    context_id: getCurrentContextId(),
                });
                this.alive = status.alive;
                this.agentBusy = status.busy;
                this.currentUrl = status.url || this.currentUrl;
                this.currentTitle = status.title || this.currentTitle;

                if (this.alive) {
                    const shot = await callJsonApi("/api/plugins/browser_use/browser_use_interact", {
                        action: "screenshot",
                        context_id: getCurrentContextId(),
                    });
                    if (shot.path) {
                        await this._renderScreenshot(shot.path);
                    }
                }
            } catch (e) {
                // Polling error, ignore
            }
        }, 1000);
    },

    async _renderScreenshot(imgPath) {
        if (!this._canvas || !this._ctx) return;

        const cleanPath = imgPath.replace(/^img:\/\//, "").split("&")[0];
        const url = `/image_get?path=${encodeURIComponent(cleanPath)}&t=${Date.now()}`;

        const img = new Image();
        img.onload = () => {
            this._canvas.width = img.width;
            this._canvas.height = img.height;
            this._ctx.drawImage(img, 0, 0);
        };
        img.src = url;
    },

    async navigate(url) {
        if (!url) return;
        try {
            const result = await callJsonApi("/api/plugins/browser_use/browser_use_interact", {
                action: "navigate",
                url: url,
                context_id: getCurrentContextId(),
            });
            if (result.url) {
                this.currentUrl = result.url;
                this.currentTitle = result.title || "";
            }
        } catch (e) {
            this.error = `Navigation failed: ${e.message}`;
        }
    },

    async takeScreenshot() {
        try {
            const result = await callJsonApi("/api/plugins/browser_use/browser_use_interact", {
                action: "screenshot",
                context_id: getCurrentContextId(),
            });
            if (result.path) {
                await this._renderScreenshot(result.path);
            }
        } catch (e) {
            this.error = `Screenshot failed: ${e.message}`;
        }
    },

    async closeBrowser() {
        try {
            await callJsonApi("/api/plugins/browser_use/browser_use_connect", {
                action: "stop",
                context_id: getCurrentContextId(),
            });
            this.connected = false;
            this.alive = false;
        } catch (e) {
            this.error = `Close failed: ${e.message}`;
        }
    },

    // Called when modal closes (via x-destroy)
    destroy() {
        if (this._pollInterval) {
            clearInterval(this._pollInterval);
            this._pollInterval = null;
        }
        this._canvas = null;
        this._ctx = null;
        this.connected = false;
        this.error = null;
    },
};

function getCurrentContextId() {
    try {
        return window.Alpine?.store("chats")?.selected || "";
    } catch {
        return "";
    }
}

export const store = createStore("browserViewer", model);
