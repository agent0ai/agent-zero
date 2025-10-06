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

globalThis.fetchApi = api.fetchApi; // TODO - backward compatibility for non-modular scripts, remove once refactored to alpine

// Declare variables for DOM elements, they will be assigned on DOMContentLoaded
let leftPanel, rightPanel, container, chatInput, chatHistory, sendButton, inputSection, statusSection, progressBar, autoScrollSwitch, timeDate;

let autoScroll = true;
let context = "";
globalThis.resetCounter = 0; // Used by stores and getChatBasedId
let skipOneSpeech = false;
let connectionStatus = undefined; // undefined = not checked yet, true = connected, false = disconnected

export function getAutoScroll() {
  return autoScroll;
}

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
            : "User message";

        // Render user message with attachments
        setMessage(messageId, "user", heading, message, false, {
          // attachments: attachmentsWithUrls, // skip here, let the backend properly log them
        });

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

function toastFetchError(text, error) {
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

function updateUserTime() {
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
  const userTimeElement = document.getElementById("time-date");
  userTimeElement.innerHTML = `${timeString}<br><span id="user-date">${dateString}</span>`;
}

updateUserTime();
setInterval(updateUserTime, 1000);

function setMessage(id, type, heading, content, temp, kvps = null) {
  const result = msgs.setMessage(id, type, heading, content, temp, kvps);
  const chatHistoryEl = document.getElementById("chat-history");
  if (autoScroll && chatHistoryEl) {
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

function getConnectionStatus() {
  return connectionStatus;
}
globalThis.getConnectionStatus = getConnectionStatus;

function setConnectionStatus(connected) {
  connectionStatus = connected;
  // Broadcast connection status without touching Alpine directly
  try {
    window.dispatchEvent(new CustomEvent("connection-status", { detail: { connected } }));
  } catch (_e) {
    // no-op
  }
}

let lastLogVersion = 0;
let lastLogGuid = "";
let lastSpokenNo = 0;

async function poll() {
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

    if (!context) setContext(response.context);
    if (response.context != context) return; //skip late polls after context change

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
      for (const log of response.logs) {
        const messageId = log.id || log.no; // Use log.id if available
        setMessage(
          messageId,
          log.type,
          log.heading,
          log.content,
          log.temp,
          log.kvps
        );
      }
      afterMessagesUpdate(response.logs);
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
      
      // Check if this context exists in the chats list
      const contextExists = chatsStore.contains(context);

      // If it doesn't exist in the chats list, try to select the first chat
      if (!contextExists && chatsStore.contexts.length > 0) {
        const firstChatId = chatsStore.firstId();
        if (firstChatId) {
          setContext(firstChatId);
          chatsStore.setSelected(firstChatId);
        }
      }
      
      tasksStore.setSelected(context);
    } else {
      // No context selected, try to select the first available item
      if (contexts.length > 0) {
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

  if (!active) {
    removeClassFromElement(progressBarEl, "shiny-text");
  } else {
    addClassToElement(progressBarEl, "shiny-text");
  }

  progress = msgs.convertIcons(progress);

  if (progressBarEl.innerHTML != progress) {
    progressBarEl.innerHTML = progress;
  }
}

globalThis.pauseAgent = async function (paused) {
  await inputStore.pauseAgent(paused);
};

globalThis.resetChat = async function (ctxid = null) {
  await chatsStore.resetChat(ctxid);
};

globalThis.newChat = async function () {
  await chatsStore.newChat();
};

globalThis.killChat = async function (id) {
  await chatsStore.killChat(id);
};

globalThis.selectChat = async function (id) {
  await chatsStore.selectChat(id);
};

function generateShortId() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

export const newContext = function () {
  context = generateShortId();
  setContext(context);
}
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

export const getContext = function () {
  return context;
}
globalThis.getContext = getContext;
globalThis.setContext = setContext;

export const getChatBasedId = function (id) {
  return context + "-" + globalThis.resetCounter + "-" + id;
};

globalThis.toggleAutoScroll = async function (_autoScroll) {
  autoScroll = _autoScroll;
};

globalThis.toggleJson = async function (showJson) {
  css.toggleCssProperty(".msg-json", "display", showJson ? "block" : "none");
};

globalThis.toggleThoughts = async function (showThoughts) {
  css.toggleCssProperty(
    ".msg-thoughts",
    "display",
    showThoughts ? undefined : "none"
  );
};

globalThis.toggleUtils = async function (showUtils) {
  css.toggleCssProperty(
    ".message-util",
    "display",
    showUtils ? undefined : "none"
  );
};

globalThis.toggleDarkMode = function (isDark) {
  if (isDark) {
    document.body.classList.remove("light-mode");
    document.body.classList.add("dark-mode");
  } else {
    document.body.classList.remove("dark-mode");
    document.body.classList.add("light-mode");
  }
  console.log("Dark mode:", isDark);
  localStorage.setItem("darkMode", isDark);
};

globalThis.toggleSpeech = function (isOn) {
  console.log("Speech:", isOn);
  localStorage.setItem("speech", isOn);
  if (!isOn) speechStore.stopAudio();
};

globalThis.nudge = async function () {
  await inputStore.nudge();
};

globalThis.restart = async function () {
  await chatsStore.restart();
};

// Modify this part
document.addEventListener("DOMContentLoaded", () => {
  const isDarkMode = localStorage.getItem("darkMode") !== "false";
  toggleDarkMode(isDarkMode);
});

globalThis.loadChats = async function () {
  await chatsStore.loadChats();
};

globalThis.saveChat = async function () {
  await chatsStore.saveChat();
};


function addClassToElement(element, className) {
  element.classList.add(className);
}

function removeClassFromElement(element, className) {
  element.classList.remove(className);
}

function justToast(text, type = "info", timeout = 5000, group = "") {
  notificationStore.addFrontendToastOnly(
    type,
    text,
    "",
    timeout / 1000,
    group
  )
}
globalThis.justToast = justToast;
  

function toast(text, type = "info", timeout = 5000) {
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

function updateAfterScroll() {
  // const toleranceEm = 1; // Tolerance in em units
  // const tolerancePx = toleranceEm * parseFloat(getComputedStyle(document.documentElement).fontSize); // Convert em to pixels
  const tolerancePx = 10;
  const chatHistory = document.getElementById("chat-history");
  if (!chatHistory) return;
  
  const isAtBottom =
    chatHistory.scrollHeight - chatHistory.scrollTop <=
    chatHistory.clientHeight + tolerancePx;

  scrollChanged(isAtBottom);
}
globalThis.updateAfterScroll = updateAfterScroll;

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

// Open the scheduler detail view for a specific task
function openTaskDetail(taskId) {
  // Wait for Alpine.js to be fully loaded
  if (globalThis.Alpine) {
    // Get the settings modal button and click it to ensure all init logic happens
    const settingsButton = document.getElementById("settings");
    if (settingsButton) {
      // Programmatically click the settings button
      settingsButton.click();

      // Now get a reference to the modal element
      const modalEl = document.getElementById("settingsModal");
      if (!modalEl) {
        console.error("Settings modal element not found after clicking button");
        return;
      }

      // Get the Alpine.js data for the modal
      const modalData = globalThis.Alpine ? Alpine.$data(modalEl) : null;

      // Use a timeout to ensure the modal is fully rendered
      setTimeout(() => {
        // Switch to the scheduler tab first
        modalData.switchTab("scheduler");

        // Use another timeout to ensure the scheduler component is initialized
        setTimeout(() => {
          // Get the scheduler component
          const schedulerComponent = document.querySelector(
            '[x-data="schedulerSettings"]'
          );
          if (!schedulerComponent) {
            console.error("Scheduler component not found");
            return;
          }

          // Get the Alpine.js data for the scheduler component
          const schedulerData = globalThis.Alpine
            ? Alpine.$data(schedulerComponent)
            : null;

          // Show the task detail view for the specific task
          schedulerData.showTaskDetail(taskId);

          console.log("Task detail view opened for task:", taskId);
        }, 50); // Give time for the scheduler tab to initialize
      }, 25); // Give time for the modal to render
    } else {
      console.error("Settings button not found");
    }
  } else {
    console.error("Alpine.js not loaded");
  }
}

// Make the function available globally
globalThis.openTaskDetail = openTaskDetail;
