import { store as chatInputStore } from "/components/chat/input/input-store.js";
import { store as memoryStore } from "/components/modals/memory/memory-dashboard-store.js";
import { store as projectsStore } from "/components/projects/projects-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { getContext } from "/index.js";
import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";

const model = {
	// State
	banners: [],
	bannersLoading: false,
	lastBannerRefresh: 0,
	hasDismissedBanners: false,

	get isVisible() {
		return !chatsStore.selected;
	},

	init() {
		// Reload banners when settings change
		document.addEventListener("settings-updated", () => {
			this.refreshBanners(true);
		});
	},

	onCreate() {
		if (this.isVisible) {
			this.refreshBanners();
		}
	},

	// Build frontend context to send to backend
	buildFrontendContext() {
		return {
			url: window.location.href,
			protocol: window.location.protocol,
			hostname: window.location.hostname,
			port: window.location.port,
			browser: navigator.userAgent,
			timestamp: new Date().toISOString(),
		};
	},

	// Frontend banner checks (most checks are on backend; add browser-only checks here)
	runFrontendBannerChecks() {
		return [];
	},

	// Call backend API for additional banners
	async runBackendBannerChecks(frontendBanners, frontendContext) {
		try {
			const response = await API.callJsonApi("/banners", {
				banners: frontendBanners,
				context: frontendContext,
			});
			return response?.banners || [];
		} catch (error) {
			console.error("Failed to fetch backend banners:", error);
			return [];
		}
	},

	// Get list of dismissed banner IDs from storage
	getDismissedBannerIds() {
		const permanent = JSON.parse(
			localStorage.getItem("dismissed_banners") || "[]",
		);
		const temporary = JSON.parse(
			sessionStorage.getItem("dismissed_banners") || "[]",
		);
		return new Set([...permanent, ...temporary]);
	},

	// Merge and filter banners: deduplicate by ID, skip dismissed, sort by priority
	mergeBanners(frontendBanners, backendBanners) {
		const dismissed = this.getDismissedBannerIds();
		const bannerMap = new Map();

		for (const banner of frontendBanners) {
			if (
				banner.id &&
				(banner.dismissible === false || !dismissed.has(banner.id))
			) {
				bannerMap.set(banner.id, banner);
			}
		}
		for (const banner of backendBanners) {
			if (
				banner.id &&
				(banner.dismissible === false || !dismissed.has(banner.id))
			) {
				bannerMap.set(banner.id, banner);
			}
		}

		return Array.from(bannerMap.values()).sort(
			(a, b) => (b.priority || 0) - (a.priority || 0),
		);
	},

	// Refresh banners: frontend checks → backend checks → merge
	async refreshBanners(force = false) {
		const now = Date.now();
		if (!force && now - this.lastBannerRefresh < 1000) return;
		this.lastBannerRefresh = now;
		this.bannersLoading = true;

		try {
			const frontendContext = this.buildFrontendContext();
			const frontendBanners = this.runFrontendBannerChecks();
			const backendBanners = await this.runBackendBannerChecks(
				frontendBanners,
				frontendContext,
			);

			const dismissed = this.getDismissedBannerIds();
			const loadIds = new Set(
				[...frontendBanners, ...backendBanners]
					.filter((b) => b?.id && b.dismissible !== false)
					.map((b) => b.id),
			);
			this.hasDismissedBanners = Array.from(loadIds).some((id) =>
				dismissed.has(id),
			);

			this.banners = this.mergeBanners(frontendBanners, backendBanners);
		} catch (error) {
			console.error("Failed to refresh banners:", error);
			this.banners = this.runFrontendBannerChecks();
			this.hasDismissedBanners = false;
		} finally {
			this.bannersLoading = false;
		}
	},

	get sortedBanners() {
		return [...this.banners].sort(
			(a, b) => (b.priority || 0) - (a.priority || 0),
		);
	},

	/**
	 * Dismiss a banner by ID.
	 *
	 * Usage:
	 *   dismissBanner('banner-id')         - Temporary dismiss (sessionStorage, cleared on browser close)
	 *   dismissBanner('banner-id', true)   - Permanent dismiss (localStorage, persists across sessions)
	 *
	 * Dismissed banners are filtered out in mergeBanners() and won't appear until storage is cleared.
	 *
	 * @param {string} bannerId - The unique ID of the banner to dismiss
	 * @param {boolean} permanent - If true, store in localStorage; if false, store in sessionStorage
	 */
	dismissBanner(bannerId, permanent = false) {
		this.banners = this.banners.filter((b) => b.id !== bannerId);

		const storage = permanent ? localStorage : sessionStorage;
		const dismissed = JSON.parse(storage.getItem("dismissed_banners") || "[]");
		if (!dismissed.includes(bannerId)) {
			dismissed.push(bannerId);
			storage.setItem("dismissed_banners", JSON.stringify(dismissed));
		}

		this.hasDismissedBanners = this.getDismissedBannerIds().size > 0;
	},

	undismissBanners() {
		localStorage.removeItem("dismissed_banners");
		sessionStorage.removeItem("dismissed_banners");
		this.hasDismissedBanners = false;
		this.refreshBanners(true);
	},

	getBannerClass(type) {
		const classes = {
			info: "banner-info",
			warning: "banner-warning",
			error: "banner-error",
		};
		return classes[type] || "banner-info";
	},

	getBannerIcon(type) {
		const icons = {
			info: "info",
			warning: "warning",
			error: "error",
		};
		return icons[type] || "info";
	},

	// Execute an action by ID
	executeAction(actionId) {
		switch (actionId) {
			case "new-chat":
				chatsStore.newChat();
				break;
			case "scheduler":
				window.openModal("modals/scheduler/scheduler-modal.html");
				break;
			case "settings": {
				// Open settings modal
				const settingsButton = document.getElementById("settings");
				if (settingsButton) {
					settingsButton.click();
				}
				break;
			}
			case "projects":
				projectsStore.openProjectsModal();
				break;
			case "memory":
				memoryStore.openModal();
				break;
			case "files":
				chatInputStore.browseFiles();
				break;
			case "website":
				window.open("https://matherly.net", "_blank");
				break;
			case "github":
				window.open("https://github.com/jrmatherly/agent-zero", "_blank");
				break;
		}
	},
};

// Create and export the store
const store = createStore("welcomeStore", model);
export { store };
