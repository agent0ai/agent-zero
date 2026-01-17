import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { callJsonApi } from "/js/api.js";
import * as modals from "/js/modals.js";
import {
  NotificationType,
  NotificationPriority,
  store as notificationStore,
} from "/components/notifications/notification-store.js";

// shortcuts utils for convenience

// api
export { callJsonApi };

// notifications
export { NotificationType, NotificationPriority };
export const frontendNotification =
  notificationStore.frontendNotification.bind(notificationStore);

// chat context
export function getCurrentContextId() {
  return chatsStore.getSelectedChatId();
}

export function getCurrentContext(){
  return chatsStore.getSelectedContext();
}

// modals
export function openModal(modalPath) {
  return modals.openModal(modalPath);
}

export function closeModal(modalPath = null) {
  return modals.closeModal(modalPath);
}
