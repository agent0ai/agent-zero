import * as msgs from "/js/messages.js";
import * as api from "/js/api.js";
import * as css from "/js/css.js";
import { sleep } from "/js/sleep.js";
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";
import { store as inputStore } from "/components/chat/input/input-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as tasksStore } from "/components/sidebar/tasks/tasks-store.js";
import { store as chatTopStore } from "/components/chat/top-section/chat-top-store.js";
import { store as _tooltipsStore } from "/components/tooltips/tooltip-store.js";
import { applyModeSteps } from "/components/messages/process-group/process-group-dom.js";

globalThis.fetchApi = api.fetchApi; // TODO - backward compatibility for non-modular scripts, remove once refactored to alpine

// Declare variables for DOM elements, they will be assigned on DOMContentLoaded
let leftPanel,
  rightPanel,
  container,
  chatInput,
  chatHistory,
  sendButton,
  inputSection,
  statusSection,
  progressBar,
  autoScrollSwitch,
  timeDate;

let autoScroll = true;
let context = null;
globalThis.resetCounter = 0; // Used by stores and getChatBasedId
let skipOneSpeech = false;

// Sidebar toggle logic is now handled by sidebar-store.js

export async function sendMessage() {
  const chatInputEl = document.getElementById("chat-input");
  if (!chatInputEl) {
    console.warn("chatInput not available, cannot send message");
    return;
  }
  try {
    const message = chatInputEl.value.trim();
    const attachmentsWithUrls = attachmentsStore.getAttachmentsForSending();
    const hasAttachments = attachmentsWithUrls.length > 0;

    if (message || hasAttachments) {
      // Sending a message is an explicit user intent to go to the bottom
      forceScrollChatToBottom();

      let response;
      const messageId = generateGUID();

      // Clear input and attachments
      chatInputEl.value = "";
      attachmentsStore.clearAttachments();
      adjustTextareaHeight();

      // Include attachments in the user message
      if (hasAttachments) {
        const heading =
          attachmentsWithUrls.length > 0
            ? "Uploading attachments..."
            : "";

        // Render user message with attachments
        setMessages([{ id: messageId, type: "user", heading, content: message, kvps: {
          // attachments: attachmentsWithUrls, // skip here, let the backend properly log them
        }}]);

        // sleep one frame to render the message before upload starts - better UX
        sleep(0);

        const formData = new FormData();
        formData.append("text", message);
        formData.append("context", context);
        formData.append("message_id", messageId);

        for (let i = 0; i < attachmentsWithUrls.length; i++) {
          formData.append("attachments", attachmentsWithUrls[i].file);
        }

        response = await api.fetchApi("/message_async", {
          method: "POST",
          body: formData,
        });
      } else {
        // For text-only messages
        const data = {
          text: message,
          context,
          message_id: messageId,
        };
        response = await api.fetchApi("/message_async", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });
      }

      // Handle response
      const jsonResponse = await response.json();
      if (!jsonResponse) {
        toast("No response returned.", "error");
      } else {
        setContext(jsonResponse.context);
      }
    }
  } catch (e) {
    toastFetchError("Error sending message", e); // Will use new notification system
  }
}
globalThis.sendMessage = sendMessage;

function getChatHistoryEl() {
  return document.getElementById("chat-history");
}

function forceScrollChatToBottom() {
  const chatHistoryEl = getChatHistoryEl();
  if (!chatHistoryEl) return;
  chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
}
globalThis.forceScrollChatToBottom = forceScrollChatToBottom;

export function toastFetchError(text, error) {
  console.error(text, error);
  // Use new frontend error notification system (async, but we don't need to wait)
  const errorMessage = error?.message || error?.toString() || "Unknown error";

  if (getConnectionStatus()) {
    // Backend is connected, just show the error
    toastFrontendError(`${text}: ${errorMessage}`).catch((e) =>
      console.error("Failed to show error toast:", e)
    );
  } else {
    // Backend is disconnected, show connection error
    toastFrontendError(
      `${text} (backend appears to be disconnected): ${errorMessage}`,
      "Connection Error"
    ).catch((e) => console.error("Failed to show connection error toast:", e));
  }
}
globalThis.toastFetchError = toastFetchError;

// Event listeners will be set up in DOMContentLoaded

export function updateChatInput(text) {
  const chatInputEl = document.getElementById("chat-input");
  if (!chatInputEl) {
    console.warn("`chatInput` element not found, cannot update.");
    return;
  }
  console.log("updateChatInput called with:", text);

  // Append text with proper spacing
  const currentValue = chatInputEl.value;
  const needsSpace = currentValue.length > 0 && !currentValue.endsWith(" ");
  chatInputEl.value = currentValue + (needsSpace ? " " : "") + text + " ";

  // Adjust height and trigger input event
  adjustTextareaHeight();
  chatInputEl.dispatchEvent(new Event("input"));

  console.log("Updated chat input value:", chatInputEl.value);
}

async function updateUserTime() {
  let userTimeElement = document.getElementById("time-date");

  while (!userTimeElement) {
    await sleep(100);
    userTimeElement = document.getElementById("time-date");
  }

  const now = new Date();
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const seconds = now.getSeconds();
  const ampm = hours >= 12 ? "pm" : "am";
  const formattedHours = hours % 12 || 12;

  // Format the time
  const timeString = `${formattedHours}:${minutes
    .toString()
    .padStart(2, "0")}:${seconds.toString().padStart(2, "0")} ${ampm}`;

  // Format the date
  const options = { year: "numeric", month: "short", day: "numeric" };
  const dateString = now.toLocaleDateString(undefined, options);

  // Update the HTML
  userTimeElement.innerHTML = `${timeString}<br><span id="user-date">${dateString}</span>`;
}

updateUserTime();
setInterval(updateUserTime, 1000);

function setMessages(logs) {
  const result = msgs.setMessages(logs);
  const chatHistoryEl = document.getElementById("chat-history");
  if (preferencesStore.autoScroll && chatHistoryEl) {
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
  }
  return result;
}

globalThis.loadKnowledge = async function () {
  await inputStore.loadKnowledge();
};

function adjustTextareaHeight() {
  const chatInputEl = document.getElementById("chat-input");
  if (chatInputEl) {
    chatInputEl.style.height = "auto";
    chatInputEl.style.height = chatInputEl.scrollHeight + "px";
  }
}

export const sendJsonData = async function (url, data) {
  return await api.callJsonApi(url, data);
  // const response = await api.fetchApi(url, {
  //     method: 'POST',
  //     headers: {
  //         'Content-Type': 'application/json'
  //     },
  //     body: JSON.stringify(data)
  // });

  // if (!response.ok) {
  //     const error = await response.text();
  //     throw new Error(error);
  // }
  // const jsonResponse = await response.json();
  // return jsonResponse;
};
globalThis.sendJsonData = sendJsonData;

function generateGUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    var r = (Math.random() * 16) | 0;
    var v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function getConnectionStatus() {
  return chatTopStore.connected;
}
globalThis.getConnectionStatus = getConnectionStatus;

function setConnectionStatus(connected) {
  chatTopStore.connected = connected;
  // connectionStatus = connected;
  // // Broadcast connection status without touching Alpine directly
  // try {
  //   window.dispatchEvent(
  //     new CustomEvent("connection-status", { detail: { connected } })
  //   );
  // } catch (_e) {
  //   // no-op
  // }
}

let lastLogVersion = 0;
let lastLogGuid = "";
let lastSpokenNo = 0;

export async function poll() {
  let updated = false;
  try {
    // Get timezone from navigator
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    const log_from = lastLogVersion;
    const response = await sendJsonData("/poll", {
      log_from: log_from,
      notifications_from: notificationStore.lastNotificationVersion || 0,
      context: context || null,
      timezone: timezone,
    });

    // Check if the response is valid
    if (!response) {
      console.error("Invalid response from poll endpoint");
      return false;
    }

    // deselect chat if it is requested by the backend
    if (response.deselect_chat) {
      chatsStore.deselectChat();
      return
    }

    if (
      response.context != context &&
      !(response.context === null && context === null) &&
      context !== null
    ) {
      return;
    }

    // if the chat has been reset, restart this poll as it may have been called with incorrect log_from
    if (lastLogGuid != response.log_guid) {
      const chatHistoryEl = document.getElementById("chat-history");
      if (chatHistoryEl) chatHistoryEl.innerHTML = "";
      lastLogVersion = 0;
      lastLogGuid = response.log_guid;
      await poll();
      return;
    }

    if (lastLogVersion != response.log_version) {
      updated = true;
      setMessages(response.logs);

      afterMessagesUpdate(response.logs);
      applyModeSteps(preferencesStore.detailMode, preferencesStore.showUtils);
    }

    lastLogVersion = response.log_version;
    lastLogGuid = response.log_guid;

    updateProgress(response.log_progress, response.log_progress_active);

    // Update notifications from response
    notificationStore.updateFromPoll(response);

    //set ui model vars from backend
    inputStore.paused = response.paused;

    // Update status icon state
    setConnectionStatus(true);

    // Update chats list using store
    let contexts = response.contexts || [];
    chatsStore.applyContexts(contexts);

    // Update tasks list using store
    let tasks = response.tasks || [];
    tasksStore.applyTasks(tasks);

    // Make sure the active context is properly selected in both lists
    if (context) {
      // Update selection in both stores
      chatsStore.setSelected(context);

      const contextInChats = chatsStore.contains(context);
      const contextInTasks = tasksStore.contains(context);

      if (contextInTasks) {
        tasksStore.setSelected(context);
      }

      if (!contextInChats && !contextInTasks) {
        if (chatsStore.contexts.length > 0) {
          // If it doesn't exist in the list but other contexts do, fall back to the first
          const firstChatId = chatsStore.firstId();
          if (firstChatId) {
            setContext(firstChatId);
            chatsStore.setSelected(firstChatId);
          }
        } else if (typeof deselectChat === "function") {
          // No contexts remain – clear state so the welcome screen can surface
          deselectChat();
        }
      }
    } else {
      const welcomeStore =
        globalThis.Alpine && typeof globalThis.Alpine.store === "function"
          ? globalThis.Alpine.store("welcomeStore")
          : null;
      const welcomeVisible = Boolean(welcomeStore && welcomeStore.isVisible);

      // No context selected, try to select the first available item unless welcome screen is active
      if (!welcomeVisible && contexts.length > 0) {
        const firstChatId = chatsStore.firstId();
        if (firstChatId) {
          setContext(firstChatId);
          chatsStore.setSelected(firstChatId);
        }
      }
    }

    lastLogVersion = response.log_version;
    lastLogGuid = response.log_guid;
  } catch (error) {
    console.error("Error:", error);
    setConnectionStatus(false);
  }

  return updated;
}
globalThis.poll = poll;

function afterMessagesUpdate(logs) {
  if (localStorage.getItem("speech") == "true") {
    speakMessages(logs);
  }
}

function speakMessages(logs) {
  if (skipOneSpeech) {
    skipOneSpeech = false;
    return;
  }
  // log.no, log.type, log.heading, log.content
  for (let i = logs.length - 1; i >= 0; i--) {
    const log = logs[i];

    // if already spoken, end
    // if(log.no < lastSpokenNo) break;

    // finished response
    if (log.type == "response") {
      // lastSpokenNo = log.no;
      speechStore.speakStream(
        getChatBasedId(log.no),
        log.content,
        log.kvps?.finished
      );
      return;

      // finished LLM headline, not response
    } else if (
      log.type == "agent" &&
      log.kvps &&
      log.kvps.headline &&
      log.kvps.tool_args &&
      log.kvps.tool_name != "response"
    ) {
      // lastSpokenNo = log.no;
      speechStore.speakStream(getChatBasedId(log.no), log.kvps.headline, true);
      return;
    }
  }
}

function updateProgress(progress, active) {
  const progressBarEl = document.getElementById("progress-bar");
  if (!progressBarEl) return;
  if (!progress) progress = "";

  setProgressBarShine(progressBarEl, active);

  progress = msgs.convertIcons(progress);

  if (progressBarEl.innerHTML != progress) {
    progressBarEl.innerHTML = progress;
  }
}

function setProgressBarShine(progressBarEl, active) {
  if (!progressBarEl) return;
  if (!active) {
    removeClassFromElement(progressBarEl, "shiny-text");
    // clear any lingering shines in process steps
    msgs.clearActiveStepShine();
  } else {
    addClassToElement(progressBarEl, "shiny-text");
  }
}

globalThis.pauseAgent = async function (paused) {
  await inputStore.pauseAgent(paused);
};

function generateShortId() {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

export const newContext = function () {
  context = generateShortId();
  setContext(context);
};
globalThis.newContext = newContext;

export const setContext = function (id) {
  if (id == context) return;
  context = id;
  // Always reset the log tracking variables when switching contexts
  // This ensures we get fresh data from the backend
  lastLogGuid = "";
  lastLogVersion = 0;
  lastSpokenNo = 0;

  // Stop speech when switching chats
  speechStore.stopAudio();

  // Clear the chat history immediately to avoid showing stale content
  const chatHistoryEl = document.getElementById("chat-history");
  if (chatHistoryEl) chatHistoryEl.innerHTML = "";

  // Update both selected states using stores
  chatsStore.setSelected(id);
  tasksStore.setSelected(id);

  //skip one speech if enabled when switching context
  if (localStorage.getItem("speech") == "true") skipOneSpeech = true;
};

export const deselectChat = function () {
  // Clear current context to show welcome screen
  setContext(null);

  // Clear localStorage selections so we don't auto-restore
  localStorage.removeItem("lastSelectedChat");
  localStorage.removeItem("lastSelectedTask");

  // Clear the chat history
  chatHistory.innerHTML = "";
};
globalThis.deselectChat = deselectChat;

export const getContext = function () {
  return context;
};
globalThis.getContext = getContext;
globalThis.setContext = setContext;

export const getChatBasedId = function (id) {
  return context + "-" + globalThis.resetCounter + "-" + id;
};

function addClassToElement(element, className) {
  element.classList.add(className);
}

function removeClassFromElement(element, className) {
  element.classList.remove(className);
}

export function justToast(text, type = "info", timeout = 5000, group = "") {
  notificationStore.addFrontendToastOnly(type, text, "", timeout / 1000, group);
}
globalThis.justToast = justToast;

export function toast(text, type = "info", timeout = 5000) {
  // Convert timeout from milliseconds to seconds for new notification system
  const display_time = Math.max(timeout / 1000, 1); // Minimum 1 second

  // Use new frontend notification system based on type
  switch (type.toLowerCase()) {
    case "error":
      return notificationStore.frontendError(text, "Error", display_time);
    case "success":
      return notificationStore.frontendInfo(text, "Success", display_time);
    case "warning":
      return notificationStore.frontendWarning(text, "Warning", display_time);
    case "info":
    default:
      return notificationStore.frontendInfo(text, "Info", display_time);
  }
}
globalThis.toast = toast;

// OLD: hideToast function removed - now using new notification system

function scrollChanged(isAtBottom) {
  // Reflect scroll state into preferences store; UI is bound via x-model
  preferencesStore.autoScroll = isAtBottom;
}

export function updateAfterScroll() {
  // const toleranceEm = 1; // Tolerance in em units
  // const tolerancePx = toleranceEm * parseFloat(getComputedStyle(document.documentElement).fontSize); // Convert em to pixels
  // Larger trigger zone near bottom for autoscroll
  const tolerancePx = 80;
  const chatHistory = document.getElementById("chat-history");
  if (!chatHistory) return;

  const isAtBottom =
    chatHistory.scrollHeight - chatHistory.scrollTop <=
    chatHistory.clientHeight + tolerancePx;

  scrollChanged(isAtBottom);
}
globalThis.updateAfterScroll = updateAfterScroll;

import { store as _chatNavigationStore } from "/components/chat/navigation/chat-navigation-store.js";


// Navigation logic in chat-navigation-store.js
// forceScrollChatToBottom is kept here as it is used by system events


// setInterval(poll, 250);

async function startPolling() {
  const shortInterval = 25;
  const longInterval = 250;
  const shortIntervalPeriod = 100;
  let shortIntervalCount = 0;

  async function _doPoll() {
    let nextInterval = longInterval;

    try {
      const result = await poll();
      if (result) shortIntervalCount = shortIntervalPeriod; // Reset the counter when the result is true
      if (shortIntervalCount > 0) shortIntervalCount--; // Decrease the counter on each call
      nextInterval = shortIntervalCount > 0 ? shortInterval : longInterval;
    } catch (error) {
      console.error("Error:", error);
    }

    // Call the function again after the selected interval
    setTimeout(_doPoll.bind(this), nextInterval);
  }

  _doPoll();
}

// All initializations and event listeners are now consolidated here
document.addEventListener("DOMContentLoaded", function () {
  // Assign DOM elements to variables now that the DOM is ready
  leftPanel = document.getElementById("left-panel");
  rightPanel = document.getElementById("right-panel");
  container = document.querySelector(".container");
  chatInput = document.getElementById("chat-input");
  chatHistory = document.getElementById("chat-history");
  sendButton = document.getElementById("send-button");
  inputSection = document.getElementById("input-section");
  statusSection = document.getElementById("status-section");
  progressBar = document.getElementById("progress-bar");
  autoScrollSwitch = document.getElementById("auto-scroll-switch");
  timeDate = document.getElementById("time-date-container");

  // Sidebar and input event listeners are now handled by their respective stores

  if (chatHistory) {
    chatHistory.addEventListener("scroll", updateAfterScroll);
  }

  // Start polling for updates
  startPolling();
});

/*
 * A0 Chat UI
 *
 * Unified sidebar layout:
 * - Both Chats and Tasks lists are always visible in a vertical layout
 * - Both lists are sorted by creation time (newest first)
 * - Tasks use the same context system as chats for communication with the backend
 */
