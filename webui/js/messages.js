// message actions and components
import { store as imageViewerStore } from "../components/modals/image-viewer/image-viewer-store.js";
import { marked } from "../vendor/marked/marked.esm.js";
import { store as _messageResizeStore } from "/components/messages/resize/message-resize-store.js"; // keep here, required in html
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { addActionButtonsToElement } from "/components/messages/action-buttons/simple-action-buttons.js";
import { store as processGroupStore } from "/components/messages/process-group/process-group-store.js";
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";

const chatHistory = document.getElementById("chat-history");

let messageGroup = null;
let currentProcessGroup = null; // Track current process group for collapsible UI

// Process types that should be grouped into collapsible sections
const PROCESS_TYPES = ['agent', 'tool', 'code_exe', 'browser', 'info', 'hint', 'util'];
// Main types that should always be visible (not collapsed)
const MAIN_TYPES = ['user', 'response', 'warning', 'error', 'rate_limit'];

/**
 * Check if a response is from the main agent (A0)
 * Subordinate agents (A1, A2, ...) responses should be treated as process steps
 */
function isMainAgentResponse(heading) {
  if (!heading) return true; // Default to main agent
  // Check for subordinate agent patterns like "A1:", "A2:", etc.
  const match = heading.match(/\bA(\d+):/);
  if (!match) return true; // No agent marker = main agent
  return match[1] === "0"; // Only A0 is the main agent
}

export function setMessage(id, type, heading, content, temp, kvps = null, timestamp = null) {
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
  }

  // For process types, check if we should add to process group
  if (isProcessType) {
    if (processStepElement) {
      // Update existing process step
      updateProcessStep(processStepElement, id, type, heading, content, kvps);
      return processStepElement;
    }
    
    // Create or get process group for current interaction
    if (!currentProcessGroup || !document.getElementById(currentProcessGroup.id)) {
      currentProcessGroup = createProcessGroup(id);
      chatHistory.appendChild(currentProcessGroup);
    }
    
    // Add step to current process group
    processStepElement = addProcessStep(currentProcessGroup, id, type, heading, content, kvps, timestamp);
    return processStepElement;
  }

  // For subordinate agent responses (A1, A2, ...), treat as a process step instead of main response
  if (type === "response" && !isMainAgentResponse(heading)) {
    if (processStepElement) {
      updateProcessStep(processStepElement, id, "agent", heading, content, kvps);
      return processStepElement;
    }
    
    // Create or get process group for current interaction
    if (!currentProcessGroup || !document.getElementById(currentProcessGroup.id)) {
      currentProcessGroup = createProcessGroup(id);
      chatHistory.appendChild(currentProcessGroup);
    }
    
    // Add subordinate response as a step (type "agent" for appropriate styling)
    processStepElement = addProcessStep(currentProcessGroup, id, "agent", heading, content, kvps, timestamp);
    return processStepElement;
  }

  // For main agent (A0) response, embed the current process group
  if (type === "response" && currentProcessGroup) {
    const processGroupToEmbed = currentProcessGroup;
    // Keep currentProcessGroup reference - subsequent process messages go to same group
    
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

  // Handle heading
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

    if (resizeBtns) {
      let minMaxBtn = headingElement.querySelector(".msg-min-max-btns");
      if (!minMaxBtn) {
        minMaxBtn = document.createElement("div");
        minMaxBtn.classList.add("msg-min-max-btns");
        minMaxBtn.innerHTML = `
          <a href="#" class="msg-min-max-btn" @click.prevent="$store.messageResize.minimizeMessageClass('${mainClass}', $event)"><span class="material-symbols-outlined" x-text="$store.messageResize.getSetting('${mainClass}').minimized ? 'expand_content' : 'minimize'"></span></a>
          <a href="#" class="msg-min-max-btn" x-show="!$store.messageResize.getSetting('${mainClass}').minimized" @click.prevent="$store.messageResize.maximizeMessageClass('${mainClass}', $event)"><span class="material-symbols-outlined" x-text="$store.messageResize.getSetting('${mainClass}').maximized ? 'expand' : 'expand_all'"></span></a>
        `;
        headingElement.appendChild(minMaxBtn);
      }
    }
  } else {
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

  // Handle heading
  let headingElement = messageDiv.querySelector(".msg-heading");
  if (!headingElement) {
    headingElement = document.createElement("h4");
    headingElement.classList.add("msg-heading");
    messageDiv.insertBefore(headingElement, messageDiv.firstChild);
  }
  headingElement.innerHTML = `${heading} <span class='icon material-symbols-outlined'>person</span>`;

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
      if (key === "thoughts" || key === "reasoning")
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
    const kvpEntries = Object.entries(kvps);

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
      if (key === "thoughts" || key === "reasoning") {
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
  
  // Default to collapsed state - don't add 'expanded' class
  // (Users can expand manually by clicking)
  
  // Create header
  const header = document.createElement("div");
  header.classList.add("process-group-header");
  header.innerHTML = `
    <span class="material-symbols-outlined expand-icon">chevron_right</span>
    <span class="material-symbols-outlined group-icon">neurology</span>
    <span class="group-title">Processing...</span>
    <span class="step-count">0 steps</span>
    <span class="group-timestamp"></span>
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
 * Add a step to a process group
 */
function addProcessStep(group, id, type, heading, content, kvps, timestamp = null) {
  const groupId = group.getAttribute("data-group-id");
  const stepsContainer = group.querySelector(".process-steps");
  
  // Create step element
  const step = document.createElement("div");
  step.id = `process-step-${id}`;
  step.classList.add("process-step");
  step.setAttribute("data-type", type);
  step.setAttribute("data-step-id", id);
  
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
  
  // Add message-util class for utility/info types (controlled by showUtils preference)
  if (type === "util" || type === "info" || type === "hint") {
    step.classList.add("message-util");
    // Apply current preference state
    if (preferencesStore.showUtils) {
      step.classList.add("show-util");
    }
  }
  
  // Get step info
  const icon = processGroupStore.getStepIcon(type);
  const label = processGroupStore.getStepLabel(type);
  const title = getStepTitle(heading, kvps, type);
  
  // Check if step should be expanded
  const isStepExpanded = processGroupStore.isStepExpanded(groupId, id);
  if (isStepExpanded) {
    step.classList.add("step-expanded");
  }
  
  // Create step header
  const stepHeader = document.createElement("div");
  stepHeader.classList.add("process-step-header");
  
  // Calculate relative time from group start
  let relativeTimeStr = "";
  if (timestamp) {
    const groupStartTime = parseFloat(group.getAttribute("data-start-timestamp") || "0");
    if (groupStartTime > 0) {
      const relativeMs = (timestamp - groupStartTime) * 1000;
      relativeTimeStr = formatRelativeTime(relativeMs);
    }
  }
  
  stepHeader.innerHTML = `
    <span class="material-symbols-outlined step-icon">${icon}</span>
    <span class="step-type">${label}</span>
    <span class="step-title">${escapeHTML(title)}</span>
    ${relativeTimeStr ? `<span class="step-time">${relativeTimeStr}</span>` : ""}
    <span class="material-symbols-outlined step-expand-icon">expand_more</span>
  `;
  
  // Add click handler for step expansion
  stepHeader.addEventListener("click", (e) => {
    e.stopPropagation();
    processGroupStore.toggleStep(groupId, id);
    step.classList.toggle("step-expanded", processGroupStore.isStepExpanded(groupId, id));
  });
  
  step.appendChild(stepHeader);
  
  // Create step detail container
  const detail = document.createElement("div");
  detail.classList.add("process-step-detail");
  
  const detailContent = document.createElement("div");
  detailContent.classList.add("process-step-detail-content");
  
  // Add content to detail
  renderStepDetailContent(detailContent, content, kvps);
  
  detail.appendChild(detailContent);
  step.appendChild(detail);
  
  stepsContainer.appendChild(step);
  
  // Update group header
  updateProcessGroupHeader(group);
  
  return step;
}

/**
 * Update an existing process step
 */
function updateProcessStep(stepElement, id, type, heading, content, kvps) {
  // Update title
  const titleEl = stepElement.querySelector(".step-title");
  if (titleEl) {
    const title = getStepTitle(heading, kvps, type);
    titleEl.textContent = title;
  }
  
  // Update detail content
  const detailContent = stepElement.querySelector(".process-step-detail-content");
  if (detailContent) {
    renderStepDetailContent(detailContent, content, kvps);
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
  
  return processGroupStore.getStepLabel(type);
}

/**
 * Clean step title by removing icon:// prefixes
 * Preserves agent markers (A0:, A1:, etc.) so users can see which agent is executing
 */
function cleanStepTitle(text, maxLength) {
  if (!text) return "";
  let cleaned = String(text);
  
  // Remove icon:// patterns (e.g., "icon://network_intelligence")
  cleaned = cleaned.replace(/icon:\/\/[a-zA-Z0-9_]+\s*/g, "");
  
  // Keep agent markers (A0:, A1:, etc.) - users need to see which agent is executing
  // Only remove "A0:" as it's the main agent (implied)
  cleaned = cleaned.replace(/^A0:\s*/i, "");
  
  // Trim whitespace
  cleaned = cleaned.trim();
  
  return truncateText(cleaned, maxLength);
}

/**
 * Render content for step detail panel
 */
function renderStepDetailContent(container, content, kvps) {
  container.innerHTML = "";
  
  // Add KVPs if present
  if (kvps && Object.keys(kvps).length > 0) {
    const kvpsDiv = document.createElement("div");
    kvpsDiv.classList.add("step-kvps");
    
    for (const [key, value] of Object.entries(kvps)) {
      // Skip internal/display keys
      if (key === "finished" || key === "attachments") continue;
      
      const kvpDiv = document.createElement("div");
      kvpDiv.classList.add("step-kvp");
      
      // Add msg-thoughts class for thoughts-related keys (controlled by showThoughts preference)
      const lowerKey = key.toLowerCase();
      
      if (lowerKey === "thoughts" || lowerKey === "thinking" || lowerKey === "reflection") {
        kvpDiv.classList.add("msg-thoughts");
        // Apply current preference state - hide if showThoughts is false
        if (!preferencesStore.showThoughts) {
          kvpDiv.classList.add("hide-thoughts");
        }
      }
      
      const keySpan = document.createElement("span");
      keySpan.classList.add("step-kvp-key");
      keySpan.textContent = convertToTitleCase(key) + ":";
      
      const valueSpan = document.createElement("span");
      valueSpan.classList.add("step-kvp-value");
      
      let valueText = value;
      if (typeof value === "object") {
        valueText = JSON.stringify(value, null, 2);
      }
      
      valueSpan.textContent = truncateText(String(valueText), 500);
      
      kvpDiv.appendChild(keySpan);
      kvpDiv.appendChild(valueSpan);
      kvpsDiv.appendChild(kvpDiv);
    }
    
    container.appendChild(kvpsDiv);
  }
  
  // Add main content if present (JSON content - controlled by showJson preference)
  if (content && content.trim()) {
    const pre = document.createElement("pre");
    pre.classList.add("msg-json");
    // Apply current preference state
    if (preferencesStore.showJson) {
      pre.classList.add("show-json");
    }
    pre.textContent = truncateText(content, 1000);
    container.appendChild(pre);
  }
}

/**
 * Update process group header with step count and status
 */
function updateProcessGroupHeader(group) {
  const steps = group.querySelectorAll(".process-step");
  const countEl = group.querySelector(".step-count");
  const titleEl = group.querySelector(".group-title");
  
  if (countEl) {
    const count = steps.length;
    countEl.textContent = `${count} step${count !== 1 ? "s" : ""}`;
  }
  
  if (titleEl && steps.length > 0) {
    // Get the last step's type for the title
    const lastStep = steps[steps.length - 1];
    const lastType = lastStep.getAttribute("data-type");
    const lastTitle = lastStep.querySelector(".step-title")?.textContent || "";
    
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
      titleEl.textContent = `Processing (${processGroupStore.getStepLabel(lastType)})`;
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
 * Reset process group state (called on context switch)
 */
export function resetProcessGroups() {
  currentProcessGroup = null;
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

/**
 * Format relative time for steps (e.g., +0.5s, +2.3s)
 */
function formatRelativeTime(ms) {
  if (ms < 100) {
    return "+0s";
  }
  const seconds = ms / 1000;
  if (seconds < 60) {
    return `+${seconds.toFixed(1)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `+${minutes}m${remainingSeconds}s`;
}
