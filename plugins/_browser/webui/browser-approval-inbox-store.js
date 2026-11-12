import { createStore } from "/js/AlpineStore.js";
import { store as site } from "/plugins/_browser/webui/browser-site-requests-store.js";
import { store as action } from "/plugins/_browser/webui/browser-action-requests-store.js";
import { store as notifications } from "/components/notifications/notification-store.js";
import { getCurrentUserISOString } from "/js/time-utils.js";

// Presentation only. Each inbox still owns its context fencing, polling and
// explicit decision boundary; this coordinator never creates an approval.
export function createApprovalInboxModel({ stores, selection = () => "", notify = () => {} }) {
  let notifiedContext = null;
  return {
    unavailable() { return stores().some((store) => store.active && store.unavailableHere()); },
    observe() {
      const contextId = selection();
      if (!this.unavailable()) { notifiedContext = null; return; }
      if (!contextId || notifiedContext === contextId) return;
      notifiedContext = contextId;
      notify("Browser permission requests are temporarily unavailable. Pending requests remain paused. Agent Zero will check again automatically while this chat is open.");
    },
  };
}

export const store = createStore("browserApprovalInbox", createApprovalInboxModel({
  stores: () => [site, action],
  selection: () => globalThis.Alpine?.store("chats")?.selected || "",
  notify: (message) => {
    // Keep connection diagnostics in the notification center, not the composer
    // or a new toast. A stable frontend ID also bounds repeated outage entries.
    notifications.addOrUpdateNotification({ id: "frontend-browser-permission-sync", type: "info", title: "Browser permissions",
      message, detail: "", timestamp: getCurrentUserISOString(), display_time: 0, read: false, frontend: true,
      group: "browser-permission-sync", priority: 10 });
    notifications.updateUnreadCount();
  },
}));
