// message actions and components
import { store as imageViewerStore } from "../components/modals/image-viewer/image-viewer-store.js";
import { marked } from "../vendor/marked/marked.esm.js";
import { store as _messageResizeStore } from "/components/messages/resize/message-resize-store.js"; // keep here, required in html
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { addActionButtonsToElement } from "/components/messages/action-buttons/simple-action-buttons.js";
import { store as processGroupStore } from "/components/messages/process-group/process-group-store.js";
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";
import { formatDuration } from "./time-utils.js";

const chatHistory = document.getElementById("chat-history");

let messageGroup = null;
let currentProcessGroup = null; // Track current process group for collapsible UI
let currentDelegationSteps = {}; // Track delegation steps by agent number for nesting

/**
 * Resolve tool name from kvps, existing attribute, or previous siblings
 * For 'tool' type steps, inherits from preceding step if not directly available
 */
function resolveToolName(type, kvps, stepElement) {
  // Direct from kvps
  if (kvps?.tool_name) return kvps.tool_name;
  
  // Keep existing if present (for non-tool types during updates)
  if (type !== 'tool' && stepElement?.hasAttribute('data-tool-name')) {
    return stepElement.getAttribute('data-tool-name');
  }
  
  // Inherit from previous sibling (for tool steps)
  if (type === 'tool' && stepElement) {
    let prev = stepElement.previousElementSibling;
    while (prev) {
      if (prev.hasAttribute('data-tool-name')) {
        return prev.getAttribute('data-tool-name');
      }
      prev = prev.previousElementSibling;
    }
  }
  
  return null;
}

/**
 * Update status badge text content
 */
function updateBadgeText(badge, newCode) {
  if (!badge) return;
  badge.textContent = newCode;
}

// Process types that should be grouped into collapsible sections
const PROCESS_TYPES = ['agent', 'tool', 'code_exe', 'browser', 'progress', 'info', 'hint', 'util', 'warning'];
// Main types that should always be visible (not collapsed)
const MAIN_TYPES = ['user', 'response', 'error', 'rate_limit'];

export function setMessage(id, type, heading, content, temp, kvps = null, timestamp = null, durationMs = null, agentNumber = 0) {
  // Check if this is a process type message
  const isProcessType = PROCESS_TYPES.includes(type);
  const isMainType = MAIN_TYPES.includes(type);
  
  // Search for the existing message container by id
  let messageContainer = document.getElementById(`message-${id}`);
  let processStepElement = document.getElementById(`process-step-${id}`);
  let isNewMessage = false;

  // For user messages, close current process group FIRST (start fresh for next interaction)
  if (type === "user") {
    currentProcessGroup = null;
    currentDelegationSteps = {}; // Clear delegation tracking
  }

  // For process types, check if we should add to process group
  if (isProcessType) {
    if (processStepElement) {
      // Update existing process step
      updateProcessStep(processStepElement, id, type, heading, content, kvps, durationMs, agentNumber);
      return processStepElement;
    }
    
    // Create or get process group for current interaction
    if (!currentProcessGroup || !document.getElementById(currentProcessGroup.id)) {
      currentProcessGroup = createProcessGroup(id);
      chatHistory.appendChild(currentProcessGroup);
    }
    
    // Add step to current process group
    processStepElement = addProcessStep(currentProcessGroup, id, type, heading, content, kvps, timestamp, durationMs, agentNumber);
    return processStepElement;
  }

  // For subordinate agent responses (A1, A2, ...), treat as a process step instead of main response
  // agentNumber: 0 = main agent, 1+ = subordinate agents
  // Note: subordinate "response" is a completion marker with content
  if (type === "response" && agentNumber !== 0) {
    if (processStepElement) {
      updateProcessStep(processStepElement, id, "response", heading, content, kvps, durationMs, agentNumber);
      return processStepElement;
    }
    
    // Create or get process group for current interaction
    if (!currentProcessGroup || !document.getElementById(currentProcessGroup.id)) {
      currentProcessGroup = createProcessGroup(id);
      chatHistory.appendChild(currentProcessGroup);
    }
    
    // Add subordinate response as a response step (special type to show content)
    processStepElement = addProcessStep(currentProcessGroup, id, "response", heading, content, kvps, timestamp, durationMs, agentNumber);
    return processStepElement;
  }

  // For main agent (A0) response, embed the current process group and mark as complete
  if (type === "response" && currentProcessGroup) {
    const processGroupToEmbed = currentProcessGroup;
    // Keep currentProcessGroup reference - subsequent process messages go to same group
    
    // Mark process group as complete (END state)
    markProcessGroupComplete(processGroupToEmbed, heading);
    
    if (!messageContainer) {
      // Create new container with embedded process group
      messageContainer = createResponseContainerWithProcessGroup(id, processGroupToEmbed);
      isNewMessage = true;
    } else {
      // Check if already embedded
      const existingEmbedded = messageContainer.querySelector(".process-group");
      if (!existingEmbedded && processGroupToEmbed) {
        embedProcessGroup(messageContainer, processGroupToEmbed);
      }
    }
  }

  if (!messageContainer) {
    // Create a new container if not found
    isNewMessage = true;
    const sender = type === "user" ? "user" : "ai";
    messageContainer = document.createElement("div");
    messageContainer.id = `message-${id}`;
    messageContainer.classList.add("message-container", `${sender}-container`);
  }

  const handler = getHandler(type);
  handler(messageContainer, id, type, heading, content, temp, kvps);

  // If this is a new message, handle DOM insertion
  if (!document.getElementById(`message-${id}`)) {
    // message type visual grouping
    const groupTypeMap = {
      user: "right",
      info: "mid",
      warning: "mid",
      error: "mid",
      rate_limit: "mid",
      util: "mid",
      hint: "mid",
      // anything else is "left"
    };
    //force new group on these types
    const groupStart = {
      response: true, // response starts a new group
      user: true, // user message starts a new group (each user message should be separate)
      // anything else is false
    };

    const groupType = groupTypeMap[type] || "left";

    // here check if messageGroup is still in DOM, if not, then set it to null (context switch)
    if (messageGroup && !document.getElementById(messageGroup.id))
      messageGroup = null;

    if (
      !messageGroup || // no group yet exists
      groupStart[type] || // message type forces new group
      groupType != messageGroup.getAttribute("data-group-type") // message type changes group
    ) {
      messageGroup = document.createElement("div");
      messageGroup.id = `message-group-${id}`;
      messageGroup.classList.add(`message-group`, `message-group-${groupType}`);
      messageGroup.setAttribute("data-group-type", groupType);
    }
    messageGroup.appendChild(messageContainer);
    chatHistory.appendChild(messageGroup);
  }

  // Simplified implementation - no setup needed

  return messageContainer;
}

// Legacy copy button functions removed - now using action buttons component

export function getHandler(type) {
  switch (type) {
    case "user":
      return drawMessageUser;
    case "agent":
      return drawMessageAgent;
    case "response":
      return drawMessageResponse;
    case "tool":
      return drawMessageTool;
    case "code_exe":
      return drawMessageCodeExe;
    case "browser":
      return drawMessageBrowser;
    case "warning":
      return drawMessageWarning;
    case "rate_limit":
      return drawMessageWarning;
    case "error":
      return drawMessageError;
    case "info":
      return drawMessageInfo;
    case "util":
      return drawMessageUtil;
    case "hint":
      return drawMessageInfo;
    default:
      return drawMessageDefault;
  }
}

// draw a message with a specific type
export function _drawMessage(
  messageContainer,
  heading,
  content,
  temp,
  followUp,
  mainClass = "",
  kvps = null,
  messageClasses = [],
  contentClasses = [],
  latex = false,
  markdown = false,
  resizeBtns = true
) {
  // Find existing message div or create new one
  let messageDiv = messageContainer.querySelector(".message");
  if (!messageDiv) {
    messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    messageContainer.appendChild(messageDiv);
  }

  // Update message classes
  messageDiv.className = `message ${mainClass} ${messageClasses.join(" ")}`;

  // Handle heading (important for error/rate_limit messages that show context)
  if (heading) {
    let headingElement = messageDiv.querySelector(".msg-heading");
    if (!headingElement) {
      headingElement = document.createElement("div");
      headingElement.classList.add("msg-heading");
      messageDiv.insertBefore(headingElement, messageDiv.firstChild);
    }

    let headingH4 = headingElement.querySelector("h4");
    if (!headingH4) {
      headingH4 = document.createElement("h4");
      headingElement.appendChild(headingH4);
    }
    headingH4.innerHTML = convertIcons(escapeHTML(heading));

    // Remove heading if it exists but heading is null
    const existingHeading = messageDiv.querySelector(".msg-heading");
    if (existingHeading) {
      existingHeading.remove();
    }
  }

  // Find existing body div or create new one
  let bodyDiv = messageDiv.querySelector(".message-body");
  if (!bodyDiv) {
    bodyDiv = document.createElement("div");
    bodyDiv.classList.add("message-body");
    messageDiv.appendChild(bodyDiv);
  }

  // reapply scroll position or autoscroll
  const scroller = new Scroller(bodyDiv);

  // Handle KVPs incrementally
  drawKvpsIncremental(bodyDiv, kvps, false);

  // Handle content
  if (content && content.trim().length > 0) {
    if (markdown) {
      let contentDiv = bodyDiv.querySelector(".msg-content");
      if (!contentDiv) {
        contentDiv = document.createElement("div");
        bodyDiv.appendChild(contentDiv);
      }
      contentDiv.className = `msg-content ${contentClasses.join(" ")}`;

      let spanElement = contentDiv.querySelector("span");
      if (!spanElement) {
        spanElement = document.createElement("span");
        contentDiv.appendChild(spanElement);
      }

      let processedContent = content;
      processedContent = convertImageTags(processedContent);
      processedContent = convertImgFilePaths(processedContent);
      processedContent = marked.parse(processedContent, { breaks: true });
      processedContent = convertPathsToLinks(processedContent);
      processedContent = addBlankTargetsToLinks(processedContent);

      spanElement.innerHTML = processedContent;

      // KaTeX rendering for markdown
      if (latex) {
        spanElement.querySelectorAll("latex").forEach((element) => {
          katex.render(element.innerHTML, element, {
            throwOnError: false,
          });
        });
      }

      // Ensure action buttons exist
      addActionButtonsToElement(bodyDiv);
      adjustMarkdownRender(contentDiv);

    } else {
      let preElement = bodyDiv.querySelector(".msg-content");
      if (!preElement) {
        preElement = document.createElement("pre");
        preElement.classList.add("msg-content", ...contentClasses);
        preElement.style.whiteSpace = "pre-wrap";
        preElement.style.wordBreak = "break-word";
        bodyDiv.appendChild(preElement);
      } else {
        // Update classes
        preElement.className = `msg-content ${contentClasses.join(" ")}`;
      }

      let spanElement = preElement.querySelector("span");
      if (!spanElement) {
        spanElement = document.createElement("span");
        preElement.appendChild(spanElement);
      }

      spanElement.innerHTML = convertHTML(content);

      // Ensure action buttons exist
      addActionButtonsToElement(bodyDiv);

    }
  } else {
    // Remove content if it exists but content is empty
    const existingContent = bodyDiv.querySelector(".msg-content");
    if (existingContent) {
      existingContent.remove();
    }
  }

  // reapply scroll position or autoscroll
  scroller.reApplyScroll();

  if (followUp) {
    messageContainer.classList.add("message-followup");
  }

  return messageDiv;
}

export function addBlankTargetsToLinks(str) {
  const doc = new DOMParser().parseFromString(str, "text/html");

  doc.querySelectorAll("a").forEach((anchor) => {
    const href = anchor.getAttribute("href") || "";
    if (
      href.startsWith("#") ||
      href.trim().toLowerCase().startsWith("javascript")
    )
      return;
    if (
      !anchor.hasAttribute("target") ||
      anchor.getAttribute("target") === ""
    ) {
      anchor.setAttribute("target", "_blank");
    }

    const rel = (anchor.getAttribute("rel") || "").split(/\s+/).filter(Boolean);
    if (!rel.includes("noopener")) rel.push("noopener");
    if (!rel.includes("noreferrer")) rel.push("noreferrer");
    anchor.setAttribute("rel", rel.join(" "));
  });
  return doc.body.innerHTML;
}

export function drawMessageDefault(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    false,
    "message-default",
    kvps,
    ["message-ai"],
    ["msg-json"],
    false,
    false
  );
}

export function drawMessageAgent(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  let kvpsFlat = null;
  if (kvps) {
    kvpsFlat = { ...kvps, ...(kvps["tool_args"] || {}) };
    delete kvpsFlat["tool_args"];
  }

  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    false,
    "message-agent",
    kvpsFlat,
    ["message-ai"],
    ["msg-json"],
    false,
    false
  );
}

export function drawMessageResponse(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    "message-agent-response",
    null,
    ["message-ai"],
    [],
    true,
    true
  );
}

export function drawMessageDelegation(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    "message-agent-delegation",
    kvps,
    ["message-ai", "message-agent"],
    [],
    true,
    false
  );
}

export function drawMessageUser(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null,
  latex = false
) {
  // Find existing message div or create new one
  let messageDiv = messageContainer.querySelector(".message");
  if (!messageDiv) {
    messageDiv = document.createElement("div");
    messageDiv.classList.add("message", "message-user");
    messageContainer.appendChild(messageDiv);
  } else {
    // Ensure it has the correct classes if it already exists
    messageDiv.className = "message message-user";
  }

  // Remove heading element if it exists (user messages no longer show label per target design)
  let headingElement = messageDiv.querySelector(".msg-heading");
  if (headingElement) {
    headingElement.remove();
  }

  // Handle content
  let textDiv = messageDiv.querySelector(".message-text");
  if (content && content.trim().length > 0) {
    if (!textDiv) {
      textDiv = document.createElement("div");
      textDiv.classList.add("message-text");
      messageDiv.appendChild(textDiv);
    }
    let spanElement = textDiv.querySelector("pre");
    if (!spanElement) {
      spanElement = document.createElement("pre");
      textDiv.appendChild(spanElement);
    }
    spanElement.innerHTML = escapeHTML(content);
    addActionButtonsToElement(textDiv);
  } else {
    if (textDiv) textDiv.remove();
  }

  // Handle attachments
  let attachmentsContainer = messageDiv.querySelector(".attachments-container");
  if (kvps && kvps.attachments && kvps.attachments.length > 0) {
    if (!attachmentsContainer) {
      attachmentsContainer = document.createElement("div");
      attachmentsContainer.classList.add("attachments-container");
      messageDiv.appendChild(attachmentsContainer);
    }
    // Important: Clear existing attachments to re-render, preventing duplicates on update
    attachmentsContainer.innerHTML = "";

    kvps.attachments.forEach((attachment) => {
      const attachmentDiv = document.createElement("div");
      attachmentDiv.classList.add("attachment-item");

      const displayInfo = attachmentsStore.getAttachmentDisplayInfo(attachment);

      if (displayInfo.isImage) {
        attachmentDiv.classList.add("image-type");

        const img = document.createElement("img");
        img.src = displayInfo.previewUrl;
        img.alt = displayInfo.filename;
        img.classList.add("attachment-preview");
        img.style.cursor = "pointer";

        attachmentDiv.appendChild(img);
      } else {
        // Render as file tile with title and icon
        attachmentDiv.classList.add("file-type");

        // File icon
        if (
          displayInfo.previewUrl &&
          displayInfo.previewUrl !== displayInfo.filename
        ) {
          const iconImg = document.createElement("img");
          iconImg.src = displayInfo.previewUrl;
          iconImg.alt = `${displayInfo.extension} file`;
          iconImg.classList.add("file-icon");
          attachmentDiv.appendChild(iconImg);
        }

        // File title
        const fileTitle = document.createElement("div");
        fileTitle.classList.add("file-title");
        fileTitle.textContent = displayInfo.filename;

        attachmentDiv.appendChild(fileTitle);
      }

      attachmentDiv.addEventListener("click", displayInfo.clickHandler);

      attachmentsContainer.appendChild(attachmentDiv);
    });
  } else {
    if (attachmentsContainer) attachmentsContainer.remove();
  }
  // The messageDiv is already appended or updated, no need to append again
}

export function drawMessageTool(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    "message-tool",
    kvps,
    ["message-ai"],
    ["msg-output"],
    false,
    false
  );
}

export function drawMessageCodeExe(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    "message-code-exe",
    null,
    ["message-ai"],
    [],
    false,
    false
  );
}

export function drawMessageBrowser(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    true,
    "message-browser",
    kvps,
    ["message-ai"],
    ["msg-json"],
    false,
    false
  );
}

export function drawMessageAgentPlain(
  mainClass,
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    false,
    mainClass,
    kvps,
    [],
    [],
    false,
    false
  );
  messageContainer.classList.add("center-container");
}

export function drawMessageInfo(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  return drawMessageAgentPlain(
    "message-info",
    messageContainer,
    id,
    type,
    heading,
    content,
    temp,
    kvps
  );
}

export function drawMessageUtil(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  _drawMessage(
    messageContainer,
    heading,
    content,
    temp,
    false,
    "message-util",
    kvps,
    [],
    ["msg-json"],
    false,
    false
  );
  messageContainer.classList.add("center-container");
}

export function drawMessageWarning(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  return drawMessageAgentPlain(
    "message-warning",
    messageContainer,
    id,
    type,
    heading,
    content,
    temp,
    kvps
  );
}

export function drawMessageError(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  return drawMessageAgentPlain(
    "message-error",
    messageContainer,
    id,
    type,
    heading,
    content,
    temp,
    kvps
  );
}

function drawKvps(container, kvps, latex) {
  if (kvps) {
    const table = document.createElement("table");
    table.classList.add("msg-kvps");
    for (let [key, value] of Object.entries(kvps)) {
      const row = table.insertRow();
      row.classList.add("kvps-row");
      // Skip reasoning
      if (key === "reasoning") continue;
      if (key === "thoughts")
        // TODO: find a better way to determine special class assignment
        row.classList.add("msg-thoughts");

      const th = row.insertCell();
      th.textContent = convertToTitleCase(key);
      th.classList.add("kvps-key");

      const td = row.insertCell();
      const tdiv = document.createElement("div");
      tdiv.classList.add("kvps-val");
      td.appendChild(tdiv);

      if (Array.isArray(value)) {
        for (const item of value) {
          addValue(item);
        }
      } else {
        addValue(value);
      }

      addActionButtonsToElement(tdiv);

      // autoscroll the KVP value if needed
      // if (getAutoScroll()) #TODO needs a better redraw system
      setTimeout(() => {
        tdiv.scrollTop = tdiv.scrollHeight;
      }, 0);

      function addValue(value) {
        if (typeof value === "object") value = JSON.stringify(value, null, 2);

        if (typeof value === "string" && value.startsWith("img://")) {
          const imgElement = document.createElement("img");
          imgElement.classList.add("kvps-img");
          imgElement.src = value.replace("img://", "/image_get?path=");
          imgElement.alt = "Image Attachment";
          tdiv.appendChild(imgElement);

          // Add click handler and cursor change
          imgElement.style.cursor = "pointer";
          imgElement.addEventListener("click", () => {
            openImageModal(imgElement.src, 1000);
          });
        } else {
          const pre = document.createElement("pre");
          const span = document.createElement("span");
          span.innerHTML = convertHTML(value);
          pre.appendChild(span);
          tdiv.appendChild(pre);

          // KaTeX rendering for markdown
          if (latex) {
            span.querySelectorAll("latex").forEach((element) => {
              katex.render(element.innerHTML, element, {
                throwOnError: false,
              });
            });
          }
        }
      }
    }
    container.appendChild(table);
  }
}

function drawKvpsIncremental(container, kvps, latex) {
  if (kvps) {
    // Find existing table or create new one
    let table = container.querySelector(".msg-kvps");
    if (!table) {
      table = document.createElement("table");
      table.classList.add("msg-kvps");
      container.appendChild(table);
    }

    // Get all current rows for comparison
    let existingRows = table.querySelectorAll(".kvps-row");
    // Filter out reasoning
    const kvpEntries = Object.entries(kvps).filter(([key]) => key !== "reasoning");

    // Update or create rows as needed
    kvpEntries.forEach(([key, value], index) => {
      let row = existingRows[index];

      if (!row) {
        // Create new row if it doesn't exist
        row = table.insertRow();
        row.classList.add("kvps-row");
      }

      // Update row classes
      row.className = "kvps-row";
      if (key === "thoughts") {
        row.classList.add("msg-thoughts");
      }

      // Handle key cell
      let th = row.querySelector(".kvps-key");
      if (!th) {
        th = row.insertCell(0);
        th.classList.add("kvps-key");
      }
      th.textContent = convertToTitleCase(key);

      // Handle value cell
      let td = row.cells[1];
      if (!td) {
        td = row.insertCell(1);
      }

      let tdiv = td.querySelector(".kvps-val");
      if (!tdiv) {
        tdiv = document.createElement("div");
        tdiv.classList.add("kvps-val");
        td.appendChild(tdiv);
      }

      // reapply scroll position or autoscroll
      const scroller = new Scroller(tdiv);

      // Clear and rebuild content (for now - could be optimized further)
      tdiv.innerHTML = "";

      addActionButtonsToElement(tdiv);

      if (Array.isArray(value)) {
        for (const item of value) {
          addValue(item, tdiv);
        }
      } else {
        addValue(value, tdiv);
      }

      // reapply scroll position or autoscroll
      scroller.reApplyScroll();
    });

    // Remove extra rows if we have fewer kvps now
    while (existingRows.length > kvpEntries.length) {
      const lastRow = existingRows[existingRows.length - 1];
      lastRow.remove();
      existingRows = table.querySelectorAll(".kvps-row");
    }

    function addValue(value, tdiv) {
      if (typeof value === "object") value = JSON.stringify(value, null, 2);

      if (typeof value === "string" && value.startsWith("img://")) {
        const imgElement = document.createElement("img");
        imgElement.classList.add("kvps-img");
        imgElement.src = value.replace("img://", "/image_get?path=");
        imgElement.alt = "Image Attachment";
        tdiv.appendChild(imgElement);

        // Add click handler and cursor change
        imgElement.style.cursor = "pointer";
        imgElement.addEventListener("click", () => {
          imageViewerStore.open(imgElement.src, { refreshInterval: 1000 });
        });
      } else {
        const pre = document.createElement("pre");
        const span = document.createElement("span");
        span.innerHTML = convertHTML(value);
        pre.appendChild(span);
        tdiv.appendChild(pre);

        // Add action buttons to the row
        // const row = tdiv.closest(".kvps-row");
        // if (row) {
          // addActionButtonsToElement(pre);
        // }

        // KaTeX rendering for markdown
        if (latex) {
          span.querySelectorAll("latex").forEach((element) => {
            katex.render(element.innerHTML, element, {
              throwOnError: false,
            });
          });
        }
      }
    }
  } else {
    // Remove table if kvps is null/empty
    const existingTable = container.querySelector(".msg-kvps");
    if (existingTable) {
      existingTable.remove();
    }
  }
}

function convertToTitleCase(str) {
  return str
    .replace(/_/g, " ") // Replace underscores with spaces
    .toLowerCase() // Convert the entire string to lowercase
    .replace(/\b\w/g, function (match) {
      return match.toUpperCase(); // Capitalize the first letter of each word
    });
}

/**
 * Clean text value by removing standalone bracket lines and trimming
 * Handles both strings and arrays (filters out bracket-only items)
 */
function cleanTextValue(value) {
  if (Array.isArray(value)) {
    return value
      .filter(item => item && String(item).trim() && !/^[\[\]]$/.test(String(item).trim()))
      .join("\n");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  return String(value).replace(/^\s*[\[\]]\s*$/gm, "").trim();
}

function convertImageTags(content) {
  // Regular expression to match <image> tags and extract base64 content
  const imageTagRegex = /<image>(.*?)<\/image>/g;

  // Replace <image> tags with <img> tags with base64 source
  const updatedContent = content.replace(
    imageTagRegex,
    (match, base64Content) => {
      return `<img src="data:image/jpeg;base64,${base64Content}" alt="Image Attachment" style="max-width: 250px !important;"/>`;
    }
  );

  return updatedContent;
}

function convertHTML(str) {
  if (typeof str !== "string") str = JSON.stringify(str, null, 2);

  let result = escapeHTML(str);
  result = convertImageTags(result);
  result = convertPathsToLinks(result);
  return result;
}

function convertImgFilePaths(str) {
  return str.replace(/img:\/\//g, "/image_get?path=");
}

export function convertIcons(str) {
  return str.replace(
    /icon:\/\/([a-zA-Z0-9_]+)/g,
    '<span class="icon material-symbols-outlined">$1</span>'
  );
}

function escapeHTML(str) {
  const escapeChars = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  };
  return str.replace(/[&<>'"]/g, (char) => escapeChars[char]);
}

function convertPathsToLinks(str) {
  function generateLinks(match) {
    const parts = match.split("/");
    if (!parts[0]) parts.shift(); // drop empty element left of first "
    let conc = "";
    let html = "";
    for (const part of parts) {
      conc += "/" + part;
      html += `/<a href="#" class="path-link" onclick="openFileLink('${conc}');">${part}</a>`;
    }
    return html;
  }

  const prefix = `(?:^|[> \`'"\\n]|&#39;|&quot;)`;
  const folder = `[a-zA-Z0-9_\\/.\\-]`;
  const file = `[a-zA-Z0-9_\\-\\/]`;
  const suffix = `(?<!\\.)`;
  const pathRegex = new RegExp(
    `(?<=${prefix})\\/${folder}*${file}${suffix}`,
    "g"
  );

  // skip paths inside html tags, like <img src="/path/to/image">
  const tagRegex = /(<(?:[^<>"']+|"[^"]*"|'[^']*')*>)/g;

  return str
    .split(tagRegex) // keep tags & text separate
    .map((chunk) => {
      // if it *starts* with '<', it's a tag -> leave untouched
      if (chunk.startsWith("<")) return chunk;
      // otherwise run your link-generation
      return chunk.replace(pathRegex, generateLinks);
    })
    .join("");
}

function adjustMarkdownRender(element) {
  // find all tables in the element
  const elements = element.querySelectorAll("table");

  // wrap each with a div with class message-markdown-table-wrap
  elements.forEach((el) => {
    const wrapper = document.createElement("div");
    wrapper.className = "message-markdown-table-wrap";
    el.parentNode.insertBefore(wrapper, el);
    wrapper.appendChild(el);
  });
}

class Scroller {
  constructor(element) {
    this.element = element;
    this.wasAtBottom = this.isAtBottom();
  }

  isAtBottom(tolerance = 10) {
    const scrollHeight = this.element.scrollHeight;
    const clientHeight = this.element.clientHeight;
    const distanceFromBottom =
      scrollHeight - this.element.scrollTop - clientHeight;
    return distanceFromBottom <= tolerance;
  }

  reApplyScroll() {
    if (this.wasAtBottom) this.element.scrollTop = this.element.scrollHeight;
  }
}

// ============================================
// Process Group Embedding Functions
// ============================================

/**
 * Create a response container with an embedded process group
 */
function createResponseContainerWithProcessGroup(id, processGroup) {
  const messageContainer = document.createElement("div");
  messageContainer.id = `message-${id}`;
  messageContainer.classList.add("message-container", "ai-container", "has-process-group");
  
  // Move process group from chatHistory into the container
  if (processGroup && processGroup.parentNode) {
    processGroup.parentNode.removeChild(processGroup);
  }
  
  // Process group will be the first child
  if (processGroup) {
    processGroup.classList.add("embedded");
    messageContainer.appendChild(processGroup);
  }
  
  return messageContainer;
}

/**
 * Embed a process group into an existing message container
 */
function embedProcessGroup(messageContainer, processGroup) {
  if (!messageContainer || !processGroup) return;
  
  // Remove from current parent
  if (processGroup.parentNode) {
    processGroup.parentNode.removeChild(processGroup);
  }
  
  // Add embedded class
  processGroup.classList.add("embedded");
  messageContainer.classList.add("has-process-group");
  
  // Insert at the beginning of the container
  const firstChild = messageContainer.firstChild;
  if (firstChild) {
    messageContainer.insertBefore(processGroup, firstChild);
  } else {
    messageContainer.appendChild(processGroup);
  }
}

// ============================================
// Process Group Functions
// ============================================

/**
 * Create a new collapsible process group
 */
function createProcessGroup(id) {
  const groupId = `process-group-${id}`;
  const group = document.createElement("div");
  group.id = groupId;
  group.classList.add("process-group");
  group.setAttribute("data-group-id", groupId);
  
  // Check initial expansion state from store (respects user preference)
  const initiallyExpanded = processGroupStore.isGroupExpanded(groupId);
  if (initiallyExpanded) {
    group.classList.add('expanded');
  }
  
  // Create header
  const header = document.createElement("div");
  header.classList.add("process-group-header");
  header.innerHTML = `
    <span class="expand-icon"></span>
    <span class="group-title">Processing...</span>
    <span class="status-badge status-gen status-active group-status">GEN</span>
    <span class="group-metrics">
      <span class="metric-time" title="Start time"><span class="material-symbols-outlined">schedule</span><span class="metric-value">--:--</span></span>
      <span class="metric-steps" title="Steps"><span class="material-symbols-outlined">footprint</span><span class="metric-value">0</span></span>
      <span class="metric-duration" title="Duration"><span class="material-symbols-outlined">timer</span><span class="metric-value">0s</span></span>
    </span>
  `;
  
  // Add click handler for expansion
  header.addEventListener("click", (e) => {
    processGroupStore.toggleGroup(groupId);
    const newState = processGroupStore.isGroupExpanded(groupId);
    group.classList.toggle("expanded", newState);
  });
  
  group.appendChild(header);
  
  // Create content container
  const content = document.createElement("div");
  content.classList.add("process-group-content");
  
  // Create steps container
  const steps = document.createElement("div");
  steps.classList.add("process-steps");
  content.appendChild(steps);
  
  group.appendChild(content);
  
  return group;
}

/**
 * Create or get nested container within a parent step
 */
function getNestedContainer(parentStep) {
  let nestedContainer = parentStep.querySelector(".process-nested-container");
  
  if (!nestedContainer) {
    // Create new container
    nestedContainer = document.createElement("div");
    nestedContainer.classList.add("process-nested-container");
    
    // Create inner wrapper for animation support
    const innerWrapper = document.createElement("div");
    innerWrapper.classList.add("process-nested-inner");
    nestedContainer.appendChild(innerWrapper);
    
    parentStep.appendChild(nestedContainer);
    parentStep.classList.add("has-nested-steps");
  }
  
  // Return the inner wrapper for appending steps
  const innerWrapper = nestedContainer.querySelector(".process-nested-inner");
  return innerWrapper || nestedContainer; // Fallback to container if wrapper missing
}

/**
 * Add a step to a process group
 */
function addProcessStep(group, id, type, heading, content, kvps, timestamp = null, durationMs = null, agentNumber = 0) {
  const groupId = group.getAttribute("data-group-id");
  let stepsContainer = group.querySelector(".process-steps");
  const isGroupCompleted = group.classList.contains("process-group-completed");
  
  // Create step element
  const step = document.createElement("div");
  step.id = `process-step-${id}`;
  step.classList.add("process-step");
  step.setAttribute("data-type", type);
  step.setAttribute("data-step-id", id);
  step.setAttribute("data-agent-number", agentNumber);
  
  // Resolve tool name (direct, inherited, or null)
  // For new steps, pass null as stepElement - inheritance uses stepsContainer query
  let toolNameToUse = kvps?.tool_name;
  if (type === 'tool' && !toolNameToUse) {
    const existingSteps = stepsContainer.querySelectorAll('.process-step[data-tool-name]');
    if (existingSteps.length > 0) {
      toolNameToUse = existingSteps[existingSteps.length - 1].getAttribute("data-tool-name");
    }
  }
  if (toolNameToUse) {
    step.setAttribute("data-tool-name", toolNameToUse);
  }
  
  // Store timestamp for duration calculation
  if (timestamp) {
    step.setAttribute("data-timestamp", timestamp);
    
    // Set group start time from first step
    if (!group.getAttribute("data-start-timestamp")) {
      group.setAttribute("data-start-timestamp", timestamp);
      // Update header with formatted datetime
      const timestampEl = group.querySelector(".group-timestamp");
      if (timestampEl) {
        timestampEl.textContent = formatDateTime(timestamp);
      }
    }
  }
  
  // Store duration from backend (used for final duration calculation)
  if (durationMs != null) {
    step.setAttribute("data-duration-ms", durationMs);
  }
  
  // Add message-util class for utility/info types (controlled by showUtils preference)
  if (type === "util" || type === "info" || type === "hint") {
    step.classList.add("message-util");
    // Apply current preference state
    if (preferencesStore.showUtils) {
      step.classList.add("show-util");
    }
  }
  
  // Get step info from heading (single source of truth: backend)
  const title = getStepTitle(heading, kvps, type);
  
  // Check if step should be expanded
  // Warning/error steps auto-expand to show content
  const isStepExpanded = processGroupStore.isStepExpanded(groupId, id) || 
                         (type === "warning" || type === "error");
  if (isStepExpanded) {
    step.classList.add("step-expanded");
  }
  
  // Create step header
  const stepHeader = document.createElement("div");
  stepHeader.classList.add("process-step-header");
  
  // Status code and color class from store (maps backend types)
  const statusCode = processGroupStore.getStepCode(type, toolNameToUse);
  const statusColorClass = processGroupStore.getStatusColorClass(type, toolNameToUse);
  
  // Add status color class to step for cascading --step-accent to internal icons
  step.classList.add(statusColorClass);
  
  const activeClass = isGroupCompleted ? "" : " status-active";
  stepHeader.innerHTML = `
    <span class="step-expand-icon"></span>
    <span class="status-badge ${statusColorClass}${activeClass}">${statusCode}</span>
    <span class="step-title">${escapeHTML(title)}</span>
  `;
  
  // Add click handler for step expansion
  stepHeader.addEventListener("click", (e) => {
    e.stopPropagation();
    processGroupStore.toggleStep(groupId, id);
    const newState = processGroupStore.isStepExpanded(groupId, id);
    // Explicitly add or remove the class based on state
    if (newState) {
      step.classList.add("step-expanded");
    } else {
      step.classList.remove("step-expanded");
    }
  });
  
  step.appendChild(stepHeader);
  
  // Create step detail container
  const detail = document.createElement("div");
  detail.classList.add("process-step-detail");
  
  const detailContent = document.createElement("div");
  detailContent.classList.add("process-step-detail-content");
  
  // Add content to detail
  renderStepDetailContent(detailContent, content, kvps, type);
  
  detail.appendChild(detailContent);
  step.appendChild(detail);
  
  // Track delegation steps for nesting
  if (toolNameToUse === "call_subordinate") {
    currentDelegationSteps[agentNumber] = step;
  }
  
  // Determine where to append the step (main list or nested in parent)
  let appendTarget = stepsContainer;
  
  // Check if this step belongs to a subordinate agent
  if (agentNumber > 0 && currentDelegationSteps[agentNumber - 1]) {
    const parentStep = currentDelegationSteps[agentNumber - 1];
    appendTarget = getNestedContainer(parentStep);
    step.classList.add("nested-step");
    
    // Auto-expand parent if this nested step is a warning/error
    if (type === "warning" || type === "error") {
      parentStep.classList.add("step-expanded");
    }
  }
  
  // Remove status-active from all previous steps (only the current step is active)
  const prevSteps = stepsContainer.querySelectorAll(".process-step .status-badge.status-active");
  prevSteps.forEach(badge => badge.classList.remove("status-active"));
  
  appendTarget.appendChild(step);
  
  // Update group header
  updateProcessGroupHeader(group);
  
  return step;
}

/**
 * Update an existing process step
 */
function updateProcessStep(stepElement, id, type, heading, content, kvps, durationMs = null, agentNumber = 0) {
  // Update title
  const titleEl = stepElement.querySelector(".step-title");
  if (titleEl) {
    const title = getStepTitle(heading, kvps, type);
    titleEl.textContent = title;
  }
  
  // Update duration from backend
  if (durationMs != null) {
    stepElement.setAttribute("data-duration-ms", durationMs);
  }
  
  // Update agent number if provided
  if (agentNumber !== undefined) {
    stepElement.setAttribute("data-agent-number", agentNumber);
  }
  
  // Resolve and update tool name + badge
  const toolNameToUse = resolveToolName(type, kvps, stepElement);
  if (toolNameToUse) {
    stepElement.setAttribute("data-tool-name", toolNameToUse);
    const newCode = processGroupStore.getStepCode(type, toolNameToUse);
    updateBadgeText(stepElement.querySelector(".status-badge"), newCode);
  }
  
  // Update detail content
  const detailContent = stepElement.querySelector(".process-step-detail-content");
  let skipFullRender = false;
  
  if (detailContent) {
    // For browser, update image src incrementally to avoid flashing
    if (type === "browser" && kvps?.screenshot) {
      const existingImg = detailContent.querySelector(".screenshot-img");
      const newSrc = kvps.screenshot.replace("img://", "/image_get?path=");
      if (existingImg) {
        // Only update if src actually changed
        if (!existingImg.src.endsWith(newSrc.split("?path=")[1])) {
          existingImg.src = newSrc;
        }
        // Skip full re-render to avoid flashing, but still update group header
        skipFullRender = true;
      }
    }
    
    if (!skipFullRender) {
      renderStepDetailContent(detailContent, content, kvps, type);
    }
  }
  
  // Update parent group header
  const group = stepElement.closest(".process-group");
  if (group) {
    updateProcessGroupHeader(group);
  }
}

/**
 * Get a concise title for a process step
 */
function getStepTitle(heading, kvps, type) {
  // Try to get a meaningful title from heading or kvps
  if (heading && heading.trim()) {
    return cleanStepTitle(heading, 80);
  }
  
  // For warnings/errors without heading, use content preview as title
  if ((type === "warning" || type === "error")) {
    // We'll show full content in detail, so just use type as title
    return type === "warning" ? "Warning" : "Error";
  }
  
  if (kvps) {
    // Try common fields for title
    if (kvps.tool_name) {
      const headline = kvps.headline ? cleanStepTitle(kvps.headline, 60) : '';
      return `${kvps.tool_name}${headline ? ': ' + headline : ''}`;
    }
    if (kvps.headline) {
      return cleanStepTitle(kvps.headline, 80);
    }
    if (kvps.query) {
      return truncateText(kvps.query, 80);
    }
    if (kvps.thoughts) {
      return truncateText(String(kvps.thoughts), 80);
    }
  }
  
  // Fallback: capitalize type (backend is source of truth)
  return type ? type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ') : 'Process';
}

/**
 * Extract icon name from heading with icon:// prefix
 * Returns the icon name (e.g., "terminal") or null if no prefix found
 */
function extractIconFromHeading(heading) {
  if (!heading) return null;
  const match = String(heading).match(/^icon:\/\/([a-zA-Z0-9_]+)/);
  return match ? match[1] : null;
}

/**
 * Clean step title by removing icon:// prefixes and status phrases
 * Preserves agent markers (A1:, A2:, etc.) so users can see which subordinate agent is executing
 */
function cleanStepTitle(text, maxLength) {
  if (!text) return "";
  let cleaned = String(text);
  
  // Remove icon:// patterns (e.g., "icon://network_intelligence")
  cleaned = cleaned.replace(/icon:\/\/[a-zA-Z0-9_]+\s*/g, "");
  
  // Trim whitespace
  cleaned = cleaned.trim();
  
  return truncateText(cleaned, maxLength);
}

/**
 * Render content for step detail panel
 */
function renderStepDetailContent(container, content, kvps, type = null) {
  container.innerHTML = "";
  
  // Special handling for response type - show content as markdown (for subordinate responses)
  if (type === "response" && content && content.trim()) {
    const responseDiv = document.createElement("div");
    responseDiv.classList.add("step-response-content");
    
    // Parse markdown
    let processedContent = content;
    processedContent = convertImageTags(processedContent);
    processedContent = convertImgFilePaths(processedContent);
    processedContent = marked.parse(processedContent, { breaks: true });
    processedContent = convertPathsToLinks(processedContent);
    processedContent = addBlankTargetsToLinks(processedContent);
    
    responseDiv.innerHTML = processedContent;
    container.appendChild(responseDiv);
    return;
  }
  
  // Special handling for warning/error types - always show content prominently
  if ((type === "warning" || type === "error") && content && content.trim()) {
    const warningDiv = document.createElement("div");
    warningDiv.classList.add("step-warning-content");
    warningDiv.textContent = content;
    container.appendChild(warningDiv);
    // Don't return - also show kvps if present
  }
  
  // Special handling for code_exe type - render as terminal-style output
  if (type === "code_exe" && kvps) {
    const runtime = kvps.runtime || kvps.Runtime || "bash";
    const code = kvps.code || kvps.Code || "";
    const output = content || "";
    
    if (code || output) {
      const terminalDiv = document.createElement("div");
      terminalDiv.classList.add("step-terminal");
  
      // Show output if present
      if (output && output.trim()) {
        const outputPre = document.createElement("pre");
        outputPre.classList.add("terminal-output");
        outputPre.textContent = truncateText(output, 1000);
        terminalDiv.appendChild(outputPre);
      }
      
      container.appendChild(terminalDiv);
    }
    
    // Still render thoughts if present (but not reasoning - that's native model thinking, not structured output)
    if (kvps.thoughts || kvps.thinking) {
      const thoughtKey = kvps.thoughts ? "thoughts" : "thinking";
      const thoughtValue = kvps[thoughtKey];
      renderThoughts(container, thoughtValue);
    }
    
    return;
  }
  
  // Add KVPs if present
  if (kvps && Object.keys(kvps).length > 0) {
    const kvpsDiv = document.createElement("div");
    kvpsDiv.classList.add("step-kvps");
    
    for (const [key, value] of Object.entries(kvps)) {
      // Skip internal/display keys
      if (key === "finished" || key === "attachments") continue;
      
      // Skip code_exe specific keys that we handle specially above
      if (type === "code_exe" && (key.toLowerCase() === "runtime" || key.toLowerCase() === "session" || key.toLowerCase() === "code")) {
        continue;
      }
      
      const lowerKey = key.toLowerCase();
      
      // Skip headline and tool_name - they're shown elsewhere
      if (lowerKey === "headline" || lowerKey === "tool_name") continue;
      
      // Skip query in agent steps - it's shown in the tool call step
      if (type === "agent" && lowerKey === "query") continue;
      
      // Special handling for thoughts - render with single lightbulb icon
      // Skip reasoning
      if (lowerKey === "reasoning") continue;
      if (lowerKey === "thoughts" || lowerKey === "thinking" || lowerKey === "reflection") {
        renderThoughts(kvpsDiv, value);
        continue;
      }
      
      // Special handling for tool_args - render only for tool/mcp types (skip for agent)
      if (lowerKey === "tool_args") {
        // Skip tool_args for agent steps - it's shown in the tool call step
        if (type === "agent") continue;
        
        if (typeof value !== "object" || value === null) continue;
        const argsDiv = document.createElement("div");
        argsDiv.classList.add("step-tool-args");
        
        // Icon mapping for common tool arguments
        const argIcons = {
          'query': 'search',
          'url': 'link',
          'path': 'folder',
          'file': 'description',
          'code': 'code',
          'command': 'terminal',
          'message': 'chat',
          'text': 'notes',
          'content': 'article',
          'name': 'label',
          'id': 'tag',
          'type': 'category',
          'document': 'description',
          'documents': 'folder_open',
          'queries': 'search'
        };
        
        for (const [argKey, argValue] of Object.entries(value)) {
          const argRow = document.createElement("div");
          argRow.classList.add("tool-arg-row");
          
          const argLabel = document.createElement("span");
          argLabel.classList.add("tool-arg-label");
          
          // Use icon if available, otherwise use text label
          const lowerArgKey = argKey.toLowerCase();
          if (argIcons[lowerArgKey]) {
            argLabel.innerHTML = `<span class="material-symbols-outlined">${argIcons[lowerArgKey]}</span>`;
          } else {
            argLabel.textContent = convertToTitleCase(argKey) + ":";
          }
          
          const argVal = document.createElement("span");
          argVal.classList.add("tool-arg-value");
          
          const argText = cleanTextValue(argValue);
          
          argVal.textContent = truncateText(argText, 300);
          
          argRow.appendChild(argLabel);
          argRow.appendChild(argVal);
          argsDiv.appendChild(argRow);
        }
        
        kvpsDiv.appendChild(argsDiv);
        continue;
      }
      
      const kvpDiv = document.createElement("div");
      kvpDiv.classList.add("step-kvp");
      
      const keySpan = document.createElement("span");
      keySpan.classList.add("step-kvp-key");
      
      // Icon mapping for common kvp keys
      const kvpIcons = {
        'query': 'search',
        'url': 'link',
        'path': 'folder',
        'file': 'description',
        'code': 'code',
        'command': 'terminal',
        'message': 'chat',
        'text': 'notes',
        'content': 'article',
        'name': 'label',
        'id': 'tag',
        'type': 'category',
        'runtime': 'memory',
        'result': 'output',
        'progress': 'pending',
        'document': 'description',
        'documents': 'folder_open',
        'queries': 'search',
        'screenshot': 'image'
      };
      
      // lowerKey already defined above
      if (kvpIcons[lowerKey]) {
        keySpan.innerHTML = `<span class="material-symbols-outlined">${kvpIcons[lowerKey]}</span>`;
      } else {
        keySpan.textContent = convertToTitleCase(key) + ":";
      }
      
      const valueSpan = document.createElement("div");
      valueSpan.classList.add("step-kvp-value");
      
      if (typeof value === "string" && value.startsWith("img://")) {
        const imgElement = document.createElement("img");
        imgElement.classList.add("screenshot-img");
        imgElement.src = value.replace("img://", "/image_get?path=");
        imgElement.alt = "Image Attachment";
        imgElement.style.cursor = "pointer";
        imgElement.style.maxWidth = "100%";
        imgElement.style.display = "block";
        imgElement.style.marginTop = "4px";
        
        // Add click handler and cursor change
        imgElement.addEventListener("click", () => {
          imageViewerStore.open(imgElement.src, { name: "Image Attachment" });
        });
        
        valueSpan.appendChild(imgElement);
      } else {
        const valueText = cleanTextValue(value);
        valueSpan.textContent = truncateText(valueText, 1000);
      }
      
      kvpDiv.appendChild(keySpan);
      kvpDiv.appendChild(valueSpan);
      kvpsDiv.appendChild(kvpDiv);
    }
    
    container.appendChild(kvpsDiv);
  }
  
  // Add main content if present (JSON content)
  if (content && content.trim()) {
    const pre = document.createElement("pre");
    pre.classList.add("msg-json");
    pre.textContent = truncateText(content, 1000);
    container.appendChild(pre);
  }
}

/**
 * Helper to render thoughts/reasoning with lightbulb icon
 */
function renderThoughts(container, value) {
  const thoughtsDiv = document.createElement("div");
  thoughtsDiv.classList.add("step-thoughts", "msg-thoughts");
  
  const thoughtText = cleanTextValue(value);
  
  if (thoughtText) {
    thoughtsDiv.innerHTML = `<span class="thought-icon material-symbols-outlined">lightbulb</span><span class="thought-text">${escapeHTML(thoughtText)}</span>`;
    container.appendChild(thoughtsDiv);
  }
}

/**
 * Update process group header with step count, status, and metrics
 */
function updateProcessGroupHeader(group) {
  const steps = group.querySelectorAll(".process-step");
  const titleEl = group.querySelector(".group-title");
  const statusEl = group.querySelector(".group-status");
  const metricsEl = group.querySelector(".group-metrics");
  const isCompleted = group.classList.contains("process-group-completed");
  
  // If completed, only remove active badges and exit early (don't update metrics)
  if (isCompleted) {
    const activeBadges = group.querySelectorAll(".status-badge.status-active");
    activeBadges.forEach(badge => badge.classList.remove("status-active"));
    return;
  }
  
  // Update group title with the latest agent step heading
  if (titleEl) {
    // Find the last "agent" type step
    const agentSteps = Array.from(steps).filter(step => step.getAttribute("data-type") === "agent");
    if (agentSteps.length > 0) {
      const lastAgentStep = agentSteps[agentSteps.length - 1];
      const lastHeading = lastAgentStep.querySelector(".step-title")?.textContent;
      if (lastHeading) {
        const cleanTitle = cleanStepTitle(lastHeading, 50);
        if (cleanTitle) {
          titleEl.textContent = cleanTitle;
        }
      }
    }
  }
  
  // Update step count in metrics
  const stepsMetricEl = metricsEl?.querySelector(".metric-steps .metric-value");
  if (stepsMetricEl) {
    stepsMetricEl.textContent = steps.length.toString();
  }
  
  // Update time metric
  const timeMetricEl = metricsEl?.querySelector(".metric-time .metric-value");
  const startTimestamp = group.getAttribute("data-start-timestamp");
  if (timeMetricEl && startTimestamp) {
    const date = new Date(parseFloat(startTimestamp) * 1000);
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    timeMetricEl.textContent = `${hours}:${minutes}`;
  }
  
  // Update duration metric
  const durationMetricEl = metricsEl?.querySelector(".metric-duration .metric-value");
  if (durationMetricEl && steps.length > 0) {
    // Calculate accumulated duration from backend data
    let accumulatedMs = 0;
    steps.forEach(step => {
      accumulatedMs += parseInt(step.getAttribute("data-duration-ms") || "0", 10);
    });
    
    // Check if last step is still in progress (no duration_ms set yet)
    const lastStep = steps[steps.length - 1];
    const lastStepDuration = lastStep.getAttribute("data-duration-ms");
    const lastStepTimestamp = lastStep.getAttribute("data-timestamp");
    
    if (lastStepDuration == null && lastStepTimestamp) {
      // Last step is in progress - add live elapsed time for this step only
      const lastStepStartMs = parseFloat(lastStepTimestamp) * 1000;
      const liveElapsedMs = Math.max(0, Date.now() - lastStepStartMs);
      accumulatedMs += liveElapsedMs;
    }
    
    durationMetricEl.textContent = formatDuration(accumulatedMs);
  }
  
  if (steps.length > 0) {
    // Get the last step's type for status
    const lastStep = steps[steps.length - 1];
    const lastType = lastStep.getAttribute("data-type");
    const lastToolName = lastStep.getAttribute("data-tool-name");
    const lastTitle = lastStep.querySelector(".step-title")?.textContent || "";
    
    // Update status badge (keep status-active during execution)
    if (statusEl) {
      // Status code and color class from store (maps backend types)
      const statusCode = processGroupStore.getStepCode(lastType, lastToolName);
      const statusColorClass = processGroupStore.getStatusColorClass(lastType, lastToolName);
      
      statusEl.textContent = statusCode;
      statusEl.className = `status-badge ${statusColorClass} status-active group-status`;
    }
    
    // Update title
    if (titleEl) {
      // Prefer agent type steps for the group title as they contain thinking/planning info
      if (lastType === "agent" && lastTitle) {
        titleEl.textContent = cleanStepTitle(lastTitle, 50);
      } else {
        // Try to find the most recent agent step for a better title
        const agentSteps = group.querySelectorAll('.process-step[data-type="agent"]');
        if (agentSteps.length > 0) {
          const lastAgentStep = agentSteps[agentSteps.length - 1];
          const agentTitle = lastAgentStep.querySelector(".step-title")?.textContent || "";
          if (agentTitle) {
            titleEl.textContent = cleanStepTitle(agentTitle, 50);
            return;
          }
        }
        titleEl.textContent = cleanStepTitle(lastTitle, 50) || `Processing...`;
      }
    }
  }
}

/**
 * Truncate text to a maximum length
 */
function truncateText(text, maxLength) {
  if (!text) return "";
  text = String(text).trim();
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + "...";
}

/**
 * Mark a process group as complete (END state)
 */
function markProcessGroupComplete(group, responseTitle) {
  if (!group) return;
  
  // Update status badge to END (remove status-active)
  const statusEl = group.querySelector(".group-status");
  if (statusEl) {
    statusEl.innerHTML = '<span class="badge-icon material-symbols-outlined">check</span>END';
    statusEl.className = "status-badge status-end group-status"; // No status-active
  }
  
  // Remove status-active from all step badges (stop spinners)
  const stepBadges = group.querySelectorAll(".process-step .status-badge.status-active");
  stepBadges.forEach(badge => badge.classList.remove("status-active"));
  
  // Update title if response title is available
  const titleEl = group.querySelector(".group-title");
  if (titleEl && responseTitle) {
    const cleanTitle = cleanStepTitle(responseTitle, 50);
    if (cleanTitle) {
      titleEl.textContent = cleanTitle;
    }
  }
  
  // Add completed class to group
  group.classList.add("process-group-completed");
  
  // Calculate final duration from backend data (sum of all step durations)
  const steps = group.querySelectorAll(".process-step");
  let totalDurationMs = 0;
  steps.forEach(step => {
    const durationMs = parseInt(step.getAttribute("data-duration-ms") || "0", 10);
    totalDurationMs += durationMs;
  });
  
  // Update duration metric with final value from backend
  const metricsEl = group.querySelector(".group-metrics");
  const durationMetricEl = metricsEl?.querySelector(".metric-duration .metric-value");
  if (durationMetricEl && totalDurationMs > 0) {
    durationMetricEl.textContent = formatDuration(totalDurationMs);
  }
}

/**
 * Reset process group state (called on context switch)
 */
export function resetProcessGroups() {
  currentProcessGroup = null;
  currentDelegationSteps = {};
  messageGroup = null;
}

/**
 * Format Unix timestamp as date-time string (YYYY-MM-DD HH:MM:SS)
 */
function formatDateTime(timestamp) {
  const date = new Date(timestamp * 1000); // Convert seconds to milliseconds
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}
