// message actions and components
import { store as imageViewerStore } from "../components/modals/image-viewer/image-viewer-store.js";
import { marked } from "../vendor/marked/marked.esm.js";
import { store as _messageResizeStore } from "/components/messages/resize/message-resize-store.js"; // keep here, required in html
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { addActionButtonsToElement } from "/components/messages/action-buttons/simple-action-buttons.js";
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";
import { formatDuration } from "./time-utils.js";

// ============================================
// Timing Constants
// ============================================
// Delay before collapsing previous steps when a new step is added
const STEP_COLLAPSE_DELAY_MS = 3000;
// Delay before collapsing the last step when processing completes
const FINAL_STEP_COLLAPSE_DELAY_MS = 3000;

// // Tool-specific status codes (fallback for tool steps)
// const TOOL_STATUS_CODES = {
//   call_subordinate: "SUB",
//   search_engine: "WEB",
//   a2a_chat: "A2A",
//   behaviour_adjustment: "ADJ",
//   document_query: "DOC",
//   vision_load: "EYE",
//   notify_user: "NTF",
//   scheduler: "SCH",
//   unknown: "UNK",
//   memory_save: "MEM",
//   memory_load: "MEM",
//   memory_forget: "MEM",
//   memory_delete: "MEM",
// };

// Tool-specific status classes (fallback for tool steps)
// const TOOL_STATUS_CLASSES = {
//   call_subordinate: "status-sub",
// };

const TYPE_STATUS_CODES = {
  // agent: "GEN",
  response: "END",
  // tool: "USE",
  // code_exe: "EXE",
  // browser: "WWW",
  // progress: "HLD",
  // mcp: "MCP",
  // subagent: "SUB",
  info: "INF",
  hint: "HNT",
  // warning: "WRN",
  rate_limit: "WRN",
  // error: "ERR",
  // util: "UTL",
  done: "END",
};

const TYPE_STATUS_CLASSES = {
  // agent: "status-gen",
  response: "status-end",
  // tool: "status-tool",
  // code_exe: "status-exe",
  // browser: "status-www",
  // progress: "status-wait",
  // mcp: "status-mcp",
  // subagent: "status-sub",
  info: "status-inf",
  hint: "status-hnt",
  // warning: "status-wrn",
  rate_limit: "status-wrn",
  // error: "status-err",
  // util: "status-utl",
  done: "status-end",
};

let _chatHistory = null;
let _massRender = false;

// handlers for log message rendering
export function getMessageHandler(type) {
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
    case "progress":
      return drawMessageProgress;
    case "mcp":
      return drawMessageMcp;
    case "subagent":
      return drawMessageSubagent;
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
      return drawMessageHint;
    default:
      return drawMessageDefault;
  }
}

/**
 * Mark a process group as the active one (via .active class)
 */
function setActiveProcessGroup(group) {
  if (!group) return;

  // Already active? Nothing to do
  if (group.classList.contains("active")) return;

  // Clear active + shiny from all other groups
  getChatHistoryEl()
    .querySelectorAll(".process-group.active")
    .forEach((g) => {
      if (g !== group) {
        g.classList.remove("active");
        g.querySelectorAll(".step-title.shiny-text").forEach((el) =>
          el.classList.remove("shiny-text"),
        );
      }
    });

  // Mark this group as active
  group.classList.add("active");
}

export function clearActiveStepShine() {
  // Clear all shiny step titles in process steps
  getChatHistoryEl()
    .querySelectorAll(".process-step .step-title.shiny-text")
    .forEach((el) => {
      el.classList.remove("shiny-text");
    });
}

function getChatHistoryEl() {
  if (!_chatHistory) _chatHistory = document.getElementById("chat-history");
  return _chatHistory;
}

function getLastMessageGroup() {
  return getChatHistoryEl()?.lastElementChild;
}

// function getLastMessageContainer() {
//   const chatHistoryEl = getChatHistoryEl();
//   if (!chatHistoryEl) return null;
//   const lastGroup = chatHistoryEl.lastElementChild;
//   if (!lastGroup) return null;
//   return lastGroup.lastElementChild;
// }

function appendToMessageGroup(
  messageContainer,
  position,
  forceNewGroup = false,
) {
  const chatHistoryEl = getChatHistoryEl();
  if (!chatHistoryEl) return;

  const lastGroup = chatHistoryEl.lastElementChild;
  const lastGroupType = lastGroup?.getAttribute("data-group-type");

  if (!forceNewGroup && lastGroup && lastGroupType === position) {
    lastGroup.appendChild(messageContainer);
  } else {
    const group = document.createElement("div");
    group.classList.add("message-group", `message-group-${position}`);
    group.setAttribute("data-group-type", position);
    group.appendChild(messageContainer);
    chatHistoryEl.appendChild(group);
  }
}

// function getStatusCode(type, toolName = null) {
//   if (type === "tool" && toolName && TOOL_STATUS_CODES[toolName]) {
//     return TOOL_STATUS_CODES[toolName];
//   }
//   return TYPE_STATUS_CODES[type] || type?.toUpperCase()?.slice(0, 4) || "GEN";
// }

// function getStatusClass(type, toolName = null) {
//   if (type === "tool" && toolName && TOOL_STATUS_CLASSES[toolName]) {
//     return TOOL_STATUS_CLASSES[toolName];
//   }
//   return TYPE_STATUS_CLASSES[type] || "status-gen";
// }

// /**
//  * Resolve tool name from kvps, existing attribute, or previous siblings
//  * For 'tool' type steps, inherits from preceding step if not directly available
//  */
// function resolveToolName(type, kvps, stepElement) {
//   // Direct from kvps
//   if (kvps?.tool_name) return kvps.tool_name;

//   // Keep existing if present (for non-tool types during updates)
//   if (type !== "tool" && stepElement?.hasAttribute("data-tool-name")) {
//     return stepElement.getAttribute("data-tool-name");
//   }

//   // // Inherit from previous sibling (for tool steps)
//   // if (type === 'tool' && stepElement) {
//   //   let prev = stepElement.previousElementSibling;
//   //   while (prev) {
//   //     if (prev.hasAttribute('data-tool-name')) {
//   //       return prev.getAttribute('data-tool-name');
//   //     }
//   //     prev = prev.previousElementSibling;
//   //   }
//   // }

//   return null;
// }

// entrypoint called from poll/WS communication, this is how all messages are rendered and updated
// input is raw log format
export function setMessages(messages) {
  // set _massRender flag for handlers to know how to behave
  const history = getChatHistoryEl();
  const historyEmpty = !history || history.childElementCount === 0;
  const isLargeAppend = !historyEmpty && messages.length > 10;
  const cutoff = isLargeAppend ? Math.max(0, messages.length - 2) : 0;

  // process messages
  for (let i = 0; i < messages.length; i++) {
    _massRender = historyEmpty || (isLargeAppend && i < cutoff);
    setMessage(messages[i]);
  }

  // reset _massRender flag
  _massRender = false;
}

// entrypoint called from poll/WS communication, this is how all messages are rendered and updated
// input is raw log format
export function setMessage({
  no,
  id,
  type,
  heading,
  content,
  kvps,
  timestamp,
  agentno,
  ...additional
}) {
  const handler = getMessageHandler(type);
  // prefer log ID if set to match user message created on frontend with backend updates
  return handler({
    id: id || no,
    type,
    heading,
    content,
    kvps,
    timestamp,
    agentno,
    ...additional,
  });
}

function getOrCreateMessageContainer(
  id,
  position,
  containerClasses = [],
  forceNewGroup = false,
) {
  let container = document.getElementById(`message-${id}`);
  if (!container) {
    container = document.createElement("div");
    container.id = `message-${id}`;
    container.classList.add("message-container");
  }

  if (containerClasses.length) {
    container.classList.add(...containerClasses);
  }

  if (!container.parentNode) {
    appendToMessageGroup(container, position, forceNewGroup);
  }

  return container;
}

function getLastProcessGroup(allowCompleted = true) {
  const lastContainer = getLastMessageGroup();
  if (!lastContainer) return null;
  const groups = lastContainer.querySelectorAll(".process-group");
  if (groups.length === 0) return null;
  const group = groups[groups.length - 1];
  if (!allowCompleted && group.classList.contains("process-group-completed"))
    return null;

  return group;
}

function getOrCreateProcessGroup(id, allowCompleted = true) {
  // first try direct match by ID
  const byId = document.getElementById(`process-group-${id}`);
  if (byId) return byId;

  // if not found, try to find the last process group
  const existing = getLastProcessGroup(allowCompleted);
  if (existing) return existing;

  // lastly create new
  const messageContainer = document.createElement("div");
  messageContainer.id = `process-group-${id}`;
  messageContainer.classList.add(
    "message-container",
    "ai-container",
    "has-process-group",
  );

  const group = createProcessGroup(id);
  group.classList.add("embedded");
  messageContainer.appendChild(group);

  appendToMessageGroup(messageContainer, "left");
  setActiveProcessGroup(group);
  return group;
}

function buildDetailPayload(stepData) {
  if (!stepData) return null;
  return {
    type: stepData.type,
    heading: stepData.heading,
    content: stepData.content,
    kvps: stepData.kvps,
    timestamp: stepData.timestamp,
    agentno: stepData.agentno,
    toolName: stepData.toolName,
    statusCode: stepData.statusCode,
    statusClass: stepData.statusClass,
  };
}

function buildStepCopyContent(stepData) {
  if (!stepData) return "";
  const parts = [];
  if (stepData.heading) parts.push(stepData.heading);
  if (stepData.content) parts.push(stepData.content);
  if (stepData.kvps) {
    for (const [key, value] of Object.entries(stepData.kvps)) {
      if (key === "reasoning" || key === "finished" || key === "attachments")
        continue;
      const valStr =
        typeof value === "object"
          ? JSON.stringify(value, null, 2)
          : String(value);
      parts.push(`${key}: ${valStr}`);
    }
  }
  return parts.join("\n\n");
}

function drawProcessStep({
  id,
  title,
  code,
  classes,
  kvps,
  content,
  contentClasses,
  copyText,
  speakText,
  log,
  allowCompletedGroup = false,
  ...additional
}) {
  // group and steps DOM elements
  const group = getOrCreateProcessGroup(id, allowCompletedGroup);
  const stepsContainer = group.querySelector(".process-steps");
  const stepId = `process-step-${id}`;
  let step = document.getElementById(stepId);

  const isNewStep = !step;
  const isGroupCompleted = group.classList.contains("process-group-completed");

  // const detailData = buildDetailPayload(stepData);
  // const speakText = speakContent ?? copyText;
  // const speakText = speakContent ?? copyText;

  if (isNewStep) {
    // create the base DOM element for the step
    step = document.createElement("div");
    step.id = stepId;
    step.classList.add("process-step");

    // set data attributes of the step
    step.setAttribute("data-log-type", log.type);
    step.setAttribute("data-step-id", id);
    step.setAttribute("data-agent-number", log.agentno);

    // apply step classes
    if (classes) step.classList.add(...classes);

    // if (toolName) {
    //   step.setAttribute("data-tool-name", toolName);
    // }
    // timestamp data
    // if (log.timestamp) {
    //   step.setAttribute("data-timestamp", log.timestamp);

    //   if (!group.getAttribute("data-start-timestamp")) {
    //     group.setAttribute("data-start-timestamp", log.timestamp);
    //     const timeMetricEl = group.querySelector(".metric-time .metric-value");
    //     if (timeMetricEl) {
    //       const date = new Date(parseFloat(timestamp) * 1000);
    //       const hours = String(date.getHours()).padStart(2, "0");
    //       const minutes = String(date.getMinutes()).padStart(2, "0");
    //       timeMetricEl.textContent = `${hours}:${minutes}`;
    //     }
    //   }
    // }

    // // create step detail container
    // detail = document.createElement("div");
    // detail.classList.add("process-step-detail");
    // detailContent = document.createElement("div")
    // detailContent.classList.add("process-step-detail-content")

    // const stepActionBtns = document.createElement("div");
    // stepActionBtns.classList.add("step-detail-actions");
    // detail.appendChild(stepActionBtns);
    // step.appendChild(detail);

    let appendTarget = stepsContainer;
    const parentStep = findParentDelegationStep(group, log.agentno);
    if (parentStep) {
      appendTarget = getNestedContainer(parentStep);
      step.classList.add("nested-step");
    }

    // remove any existing shiny-text from group
    group
      .querySelectorAll(".process-step .step-title.shiny-text")
      .forEach((el) => {
        el.classList.remove("shiny-text");
      });

    // insert step
    appendTarget.appendChild(step);

    // add interaction handlers - don't collapse when user interacts
    addStepCollapseInteractionHandlers(step); // TODO? cleanup listeners?

    // expand all or current step based on settings
    const detailMode = preferencesStore.detailMode;
    const isActiveGroup = group.classList.contains("active");

    //expand all
    if (detailMode === "expanded") {
      step.classList.add("step-expanded");
      // expand current step and schedule collapse of previous
    } else if (detailMode === "current") {
      if (isActiveGroup && !isGroupCompleted) {
        step.classList.add("step-expanded");
        const allExpandedSteps = stepsContainer.querySelectorAll(
          ".process-step.step-expanded",
        );
        allExpandedSteps.forEach((expandedStep) => {
          if (expandedStep.id !== stepId) {
            scheduleStepCollapse(expandedStep, STEP_COLLAPSE_DELAY_MS);
          }
        });
      }
    }
  }

  // is step expanded?
  const isExpanded = step.classList.contains("step-expanded");

  // create step header
  const stepHeader = ensureChild(
    step,
    ".process-step-header",
    "div",
    "process-step-header",
  );

  // create step detail
  const stepDetail = ensureChild(
    step,
    ".process-step-detail",
    "div",
    "process-step-detail",
  );
  const stepDetailScroll = ensureChild(
    stepDetail,
    ".process-step-detail-scroll",
    "div",
    "process-step-detail-scroll",
  );

  // create action buttons
  const stepActionBtns = ensureChild(
    stepDetail,
    ".step-detail-actions",
    "div",
    "step-detail-actions",
  );

  // else {
  //   if (timestamp && !step.hasAttribute("data-timestamp")) {
  //     step.setAttribute("data-timestamp", timestamp);
  //   }
  //   if (agentno !== undefined) {
  //     step.setAttribute("data-agent-number", agentno);
  //   }
  // }

  // const toolNameToUse = resolveToolName(type, kvps, step) || toolName;
  // if (toolNameToUse) {
  //   step.setAttribute("data-tool-name", toolNameToUse);
  // }

  if (!stepHeader.hasAttribute("data-expand-handler")) {
    stepHeader.setAttribute("data-expand-handler", "true");
    stepHeader.addEventListener("click", (e) => {
      e.stopPropagation();
      cancelStepCollapse(step);
      step.classList.toggle("step-expanded");
      if (step.classList.contains("step-expanded")) {
        step.setAttribute("data-user-pinned", "true");
      } else {
        step.removeAttribute("data-user-pinned");
      }
    });
  }

  // header row - expand icon
  ensureChild(stepHeader, ".step-expand-icon", "span", "step-expand-icon");

  // header row - status badge
  const badge = ensureChild(stepHeader, ".step-badge", "span", "step-badge");

  // set code class if changed
  const prevCode = step.getAttribute("data-step-code");
  if (prevCode !== code) {
    if (prevCode) step.classList.remove(prevCode);
    step.setAttribute("data-step-code", code);
    step.classList.add(code);
    step.querySelector(".step-badge").textContent = code;
    badge.innerText = code;
  }

  // header row - title
  const titleEl = ensureChild(stepHeader, ".step-title", "span", "step-title");
  titleEl.textContent = title;

  // const detail = ensureChild(step, ".process-step-detail", "div", "process-step-detail");
  // const detailContent = ensureChild(
  //   detail,
  //   ".process-step-detail-content",
  //   "div",
  //   "process-step-detail-content",
  // );

  // let skipFullRender = false;

  // const terminal = stepDetailContent.querySelector(".terminal-output");
  // const scroller = terminal ? new Scroller(terminal) : null;

  // if (type === "browser" && kvps?.screenshot) {
  //   const existingImg = detailContent.querySelector(".screenshot-img");
  //   const newSrc = kvps.screenshot.replace("img://", "/image_get?path=");
  //   if (existingImg) {
  //     if (!existingImg.src.endsWith(newSrc.split("?path=")[1])) {
  //       existingImg.src = newSrc;
  //     }
  //     skipFullRender = true;
  //   }
  // }

  // if (!skipFullRender) {
  //   renderStepDetailContent(detailContent, content, kvps, type);

  //   const newTerminal = detailContent.querySelector(".terminal-output");
  //   if (newTerminal && scroller?.wasAtBottom) {
  //     newTerminal.scrollTop = newTerminal.scrollHeight;
  //   }
  // }

  const detailScroller = new Scroller(stepDetailScroll); // scroller for step detail content

  // update KVPs of the step detail
  const kvpsTable = drawKvpsIncremental(stepDetailScroll, kvps);

  // update content
  const stepDetailContent = ensureChild(
    stepDetailScroll,
    ".process-step-detail-content",
    "p",
    "process-step-detail-content",
    ...(contentClasses || []),
  );
  stepDetailContent.textContent = content;

  // const detailDataToUse =
  //   detailData ||
  //   buildDetailPayload({
  //     ...stepData,
  //     toolName: toolNameToUse,
  //     statusCode: resolvedStatusCode,
  //     statusClass: resolvedStatusClass,
  //   });

  // const stepActions = ensureChild(detail, ".step-detail-actions", "div", "step-detail-actions");
  addActionButtonsToElement(stepActionBtns, {
    detailPayload: {}, // detailDataToUse,
    onViewDetails: null,
    copyContent: copyText,
    speakContent: speakText,
  });

  if (isExpanded && !isMassRender()) detailScroller.reApplyScroll(); // reapply scroll position (autoscroll if bottom) - only when expanded already and not

  updateProcessGroupHeader(group);

  if (isNewStep && !isGroupCompleted) {
    titleEl.classList.add("shiny-text");
  }

  // return anything useful
  return {
    step,
    detail: stepDetail,
    content: stepDetailContent,
    contentScroller: detailScroller,
    kvpsTable,
    actionButtons: stepActionBtns,
    isExpanded,
  };
}

function drawStandaloneMessage(id, heading, content, options = {}) {
  const {
    position = "mid",
    forceNewGroup = false,
    containerClasses = [],
    mainClass = "",
    messageClasses = [],
    contentClasses = [],
    markdown = false,
    latex = false,
    kvps = null,
    copyContent = null,
    speakContent = null,
  } = options;

  const container = getOrCreateMessageContainer(
    id,
    position,
    containerClasses,
    forceNewGroup,
  );
  const messageDiv = _drawMessage({
    messageContainer: container,
    heading,
    content,
    kvps,
    messageClasses,
    contentClasses,
    markdown,
    latex,
    mainClass,
  });

  const copyText = copyContent ?? content ?? "";
  const speakText = speakContent ?? copyText;
  addActionButtonsToElement(messageDiv, {
    copyContent: copyText,
    speakContent: speakText,
  });

  return container;
}

// draw a message with a specific type
export function _drawMessage({
  messageContainer,
  heading,
  content,
  kvps = null,
  messageClasses = [],
  contentClasses = [],
  markdown = false,
  latex = false,
  mainClass = "",
}) {
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
      processedContent = convertFilePaths(processedContent);
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

export function drawMessageDefault({
  id,
  heading,
  content,
  kvps = null,
  ...additional
}) {
  return drawStandaloneMessage(id, heading, content, {
    position: "left",
    containerClasses: ["ai-container"],
    mainClass: "message-default",
    messageClasses: ["message-ai"],
    contentClasses: ["msg-json"],
    kvps,
  });
}

export function drawMessageAgent({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  const title = cleanStepTitle(heading);
  let displayKvps = {};
  if (kvps?.thoughts) displayKvps["icon://lightbulb"] = kvps.thoughts;
  if (kvps?.step) displayKvps["icon://step"] = kvps.step;

  return drawProcessStep({
    id,
    title,
    code: "GEN",
    codeClass: "status-gen",
    classes: null,
    kvps: displayKvps,
    copyText: kvps?.thoughts,
    speakText: kvps?.thoughts,
    log: arguments[0],
  });
}

export function drawMessageResponse({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  // response of subordinate agent - render as process step
  if (agentno && agentno > 0) {
    const title = getStepTitle(heading, kvps, type);
    const statusCode = getStatusCode(type);
    const statusClass = getStatusClass(type);
    return drawProcessStep({
      id,
      title,
      statusClass,
      statusCode,
      kvps,
      type,
      heading,
      content,
      timestamp,
      agentno,
    });
  }

  // response of agent 0, render as response to user
  // get last process group or create new container (if first message)
  const group = getLastProcessGroup();
  let container = null;

  if (group)
    container = ensureChild(
      group,
      ".process-group-response",
      "div",
      "process-group-response",
    );
  else container = getOrCreateMessageContainer(id, "left");

  const messageDiv = _drawMessage({
    messageContainer: container,
    heading: null,
    content,
    kvps: null,
    messageClasses: [],
    contentClasses: [],
    markdown: true,
    latex: true,
    mainClass: "message-agent-response",
  });

  // const copyText = copyContent ?? content ?? "";
  // const speakText = speakContent ?? copyText;
  // addActionButtonsToElement(messageDiv, {
  //   copyContent: copyText,
  //   speakContent: speakText,
  // });

  if (group) updateProcessGroupHeader(group);

  return container;
}

export function drawMessageUser({
  id,
  heading,
  content,
  kvps = null,
  ...additional
}) {
  const messageContainer = getOrCreateMessageContainer(
    id,
    "right",
    ["user-container"],
    true,
  );

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

  // Render heading below message, if provided
  let headingElement = messageDiv.querySelector(".message-user-heading");
  if (heading && heading.trim() && heading.trim() !== "User message") {
    if (!headingElement) {
      headingElement = document.createElement("div");
      headingElement.className = "message-user-heading shiny-text";
    }
    headingElement.textContent = heading;
    messageDiv.appendChild(headingElement);
  } else if (headingElement) {
    headingElement.remove();
  }

  // Add action buttons below text and attachments (hover for pointer, always for touch - via CSS)
  addActionButtonsToElement(messageDiv, {
    copyContent: content || "",
    speakContent: content || "",
  });
}

export function drawMessageTool({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  const title = cleanStepTitle(heading);
  let displayKvps = { ...kvps };

  return drawProcessStep({
    id,
    title,
    code: "USE",
    codeClass: "status-tool",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    copyText: content,
    speakText: content,
    log: arguments[0],
  });
}

export function drawMessageCodeExe({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  let title = "Code Execution";
  // show command at the start and end
  if (
    type === "code_exe" &&
    kvps?.code &&
    /done_all|code_execution_tool/.test(heading || "")
  ) {
    const s = kvps.session ?? kvps.Session;
    title = `${s != null ? `[${s}] ` : ""}${kvps.runtime || "bash"}> ${kvps.code.trim()}`;
  } else {
    // during execution show the original heading (current step)
    title = cleanStepTitle(heading);
  }

  // KVPS to show
  const displayKvps = {};
  if (kvps?.runtime) displayKvps.runtime = kvps.runtime;
  if (kvps?.session) displayKvps.session = kvps.session;

  // render the standard step
  const stepData = drawProcessStep({
    id,
    title,
    code: "EXE",
    codeClass: "status-exe",
    classes: null,
    kvps: displayKvps,
    content,
    contentClasses: ["terminal-output"],
    copyText: content,
    speakText: null,
    log: arguments[0],
  });
}

export function drawMessageBrowser({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  const title = cleanStepTitle(heading);
  let displayKvps = { ...kvps };

  return drawProcessStep({
    id,
    title,
    code: "HDL",
    codeClass: "status-hdl",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    copyText: content,
    speakText: content,
    log: arguments[0],
  });
}

export function drawMessageMcp({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  const title = cleanStepTitle(heading);
  let displayKvps = { ...kvps };

  return drawProcessStep({
    id,
    title,
    code: "MCP",
    codeClass: "status-mcp",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    copyText: content,
    speakText: content,
    log: arguments[0],
  });
}

export function drawMessageSubagent({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  const title = cleanStepTitle(heading);
  let displayKvps = { ...kvps };

  return drawProcessStep({
    id,
    title,
    code: "SUB",
    codeClass: "status-sub",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    copyText: content,
    speakText: content,
    log: arguments[0],
  });
}

export function drawMessageInfo({
  id,
  heading,
  content,
  kvps = null,
  ...additional
}) {
  return drawStandaloneMessage(id, heading, content, {
    position: "mid",
    containerClasses: ["ai-container", "center-container"],
    mainClass: "message-info",
    kvps,
  });
}

export function drawMessageUtil({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  const title = cleanStepTitle(heading);

  return drawProcessStep({
    id,
    title,
    code: "UTL",
    codeClass: "status-utl",
    classes: ["message-util"],
    kvps,
    copyText: null,
    speakText: null,
    log: arguments[0],
    allowCompletedGroup: true,
  });
}

export function drawMessageHint({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  const title = getStepTitle(heading, kvps, type);
  const statusCode = getStatusCode(type);
  const statusClass = getStatusClass(type);

  return drawProcessStep({
    id,
    title,
    statusClass,
    statusCode,
    kvps,
    type,
    heading,
    content,
    timestamp,
    agentno,
  });
}

export function drawMessageProgress({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  ...additional
}) {
  const title = cleanStepTitle(heading);
  let displayKvps = { ...kvps };

  return drawProcessStep({
    id,
    title,
    code: "HDL",
    codeClass: "status-hdl",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    // copyText: kvps?.thoughts,
    // speakText: kvps?.thoughts,
    log: arguments[0],
  });
}

export function drawMessageWarning({
  id,
  heading,
  content,
  kvps = null,
  ...additional
}) {
  const title = cleanStepTitle(heading);
  let displayKvps = { ...kvps };

  //TODO: if process group is running, append there instead
  // return drawProcessStep({
  //   id,
  //   title,
  //   code: "WRN",
  //   codeClass: "status-wrn",
  //   classes: null,
  //   kvps: displayKvps,
  //   content,
  //   // contentClasses: [],
  //   copyText: content,
  //   speakText: content,
  //   log: arguments[0],
  // });
  return drawStandaloneMessage(id, heading, content, {
    position: "mid",
    containerClasses: ["ai-container", "center-container"],
    mainClass: "message-warning",
    kvps,
  });
}

export function drawMessageError({
  id,
  heading,
  content,
  kvps = null,
  ...additional
}) {
  return drawStandaloneMessage(id, heading, content, {
    position: "mid",
    containerClasses: ["ai-container", "center-container"],
    mainClass: "message-error",
    kvps,
  });
}

// export function drawMessageError({
//   id,
//   heading,
//   content,
//   kvps = null,
//   ...additional
// }) {
//   const messageContainer = getOrCreateMessageContainer(id, "mid", [
//     "ai-container",
//     "center-container",
//   ]);

//   // Create or get the message div
//   let messageDiv = messageContainer.querySelector(".message");
//   if (!messageDiv) {
//     messageDiv = document.createElement("div");
//     messageDiv.classList.add("message", "message-error-group");
//     messageContainer.appendChild(messageDiv);
//   }

//   // Check if error group already exists
//   let errorGroup = messageDiv.querySelector(".error-group");
//   if (!errorGroup) {
//     errorGroup = document.createElement("div");
//     errorGroup.classList.add("error-group");
//     errorGroup.setAttribute("data-error-id", id);

//     // Create header (clickable for expand/collapse)
//     const header = document.createElement("div");
//     header.classList.add("error-group-header");

//     // Expand icon (triangle)
//     const expandIcon = document.createElement("span");
//     expandIcon.classList.add("expand-icon");
//     header.appendChild(expandIcon);

//     // Status badge (before title)
//     const badge = document.createElement("span");
//     badge.classList.add("step-badge", "status-err");
//     badge.textContent = "ERR";
//     header.appendChild(badge);

//     // Title
//     const title = document.createElement("span");
//     title.classList.add("error-title");
//     title.textContent = "Error";
//     header.appendChild(title);

//     // Subtitle (short error description)
//     const subtitle = document.createElement("span");
//     subtitle.classList.add("error-subtitle");
//     header.appendChild(subtitle);

//     // Click handler for expand/collapse
//     header.addEventListener("click", () => {
//       errorGroup.classList.toggle("expanded");
//     });

//     errorGroup.appendChild(header);

//     // Create content container (collapsible)
//     const contentWrapper = document.createElement("div");
//     contentWrapper.classList.add("error-group-content");

//     const contentInner = document.createElement("div");
//     contentInner.classList.add("error-content-inner");
//     contentWrapper.appendChild(contentInner);

//     errorGroup.appendChild(contentWrapper);
//     messageDiv.appendChild(errorGroup);

//     // Check detail mode and expand if needed
//     const detailMode = preferencesStore.detailMode || "current";
//     if (detailMode === "current" || detailMode === "expanded") {
//       errorGroup.classList.add("expanded");
//     }
//   }

//   // Update subtitle with short error description
//   const subtitle = errorGroup.querySelector(".error-subtitle");
//   if (subtitle) {
//     // Extract short description from heading or content
//     let shortDesc = "";
//     // Skip if heading is just "Error" (redundant with title)
//     if (heading && heading.trim() && heading.trim().toLowerCase() !== "error") {
//       shortDesc = heading.trim();
//     }
//     // If no useful heading, try to extract from content
//     if (!shortDesc && content && content.trim()) {
//       const lines = content.trim().split("\n");
//       // Look for the error line (usually last meaningful line or one matching ErrorType: pattern)
//       for (let i = lines.length - 1; i >= 0; i--) {
//         const line = lines[i].trim();
//         if (line && /^[\w\.]+Error[:\s]/.test(line)) {
//           shortDesc = line;
//           break;
//         }
//       }
//       // Fallback to first non-empty line if no error pattern found
//       if (!shortDesc) {
//         for (const line of lines) {
//           if (line.trim() && !line.startsWith("Traceback")) {
//             shortDesc = line.trim();
//             break;
//           }
//         }
//       }
//     }
//     // Truncate if too long
//     if (shortDesc.length > 100) {
//       shortDesc = shortDesc.substring(0, 97) + "...";
//     }
//     subtitle.textContent = shortDesc;
//     subtitle.title = shortDesc; // Full text on hover
//   }

//   // Update content (full callstack)
//   const contentInner = errorGroup.querySelector(".error-content-inner");
//   if (contentInner && content) {
//     contentInner.innerHTML = "";

//     // Create pre element for callstack/content
//     const pre = document.createElement("pre");
//     pre.classList.add("error-callstack");
//     pre.textContent = content;
//     contentInner.appendChild(pre);

//     // Add action buttons for copy functionality
//     addActionButtonsToElement(contentInner, {
//       copyContent: content,
//       speakContent: content,
//     });
//   }

//   messageContainer.classList.add("center-container");
// }

function drawKvpsIncremental(container, kvps, latex) {
  // existing KVPS table
  let table = container.querySelector(".msg-kvps");
  if (kvps) {
    // create table if not found
    if (!table) {
      table = document.createElement("table");
      table.classList.add("msg-kvps");
      container.appendChild(table);
    }

    // Get all current rows for comparison
    let existingRows = table.querySelectorAll(".kvps-row");
    // Filter out reasoning
    const kvpEntries = Object.entries(kvps).filter(
      ([key]) => key !== "reasoning",
    );

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

      // Handle key cell
      let th = row.querySelector(".kvps-key");
      if (!th) {
        th = row.insertCell(0);
        th.classList.add("kvps-key");
      }
      const iconName = extractIconFromKey(key);
      if (iconName) {
        th.innerHTML = `<span class="material-symbols-outlined">${iconName}</span>`;
      } else {
        th.textContent = convertToTitleCase(key);
      }

      // Handle value cell
      let td = row.cells[1];
      if (!td) {
        td = row.insertCell(1);
        td.classList.add("kvps-val");
      }

      // reapply scroll position or autoscroll
      // no inner scrolling for kvps anymore
      // const scroller = new Scroller(td);

      // Clear and rebuild content (for now - could be optimized further)
      td.innerHTML = "";

      if (Array.isArray(value)) {
        for (const item of value) {
          addValue(item, td);
        }
      } else {
        addValue(value, td);
      }

      // reapply scroll position or autoscroll
      // scroller.reApplyScroll();
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
        const span = document.createElement("span");
        span.innerHTML = convertHTML(value);
        tdiv.appendChild(span);

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
    if (table) existingTable.remove();
    return null;
  }
  return table;
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
// function cleanTextValue(value) {
//   if (Array.isArray(value)) {
//     return value
//       .filter(
//         (item) =>
//           item && String(item).trim() && !/^[\[\]]$/.test(String(item).trim()),
//       )
//       .join("\n");
//   }
//   if (typeof value === "object" && value !== null) {
//     return JSON.stringify(value, null, 2);
//   }
//   return String(value)
//     .replace(/^\s*[\[\]]\s*$/gm, "")
//     .trim();
// }

function convertImageTags(content) {
  // Regular expression to match <image> tags and extract base64 content
  const imageTagRegex = /<image>(.*?)<\/image>/g;

  // Replace <image> tags with <img> tags with base64 source
  const updatedContent = content.replace(
    imageTagRegex,
    (match, base64Content) => {
      return `<img src="data:image/jpeg;base64,${base64Content}" alt="Image Attachment" style="max-width: 250px !important;"/>`;
    },
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

function convertFilePaths(str) {
  return str.replace(/file:\/\//g, "/download_work_dir_file?path=");
}

export function convertIcons(str) {
  return str.replace(
    /icon:\/\/([a-zA-Z0-9_]+)/g,
    '<span class="icon material-symbols-outlined">$1</span>',
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
    "g",
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

  // find all images
  const images = element.querySelectorAll("img");

  // wrap each image in <a>
  images.forEach((img) => {
    if (img.parentNode?.tagName === "A") return;
    const link = document.createElement("a");
    link.className = "message-markdown-image-wrap";
    link.href = img.src;
    img.parentNode.insertBefore(link, img);
    link.appendChild(img);
    link.onclick = (e) => (
      e.preventDefault(),
      imageViewerStore.open(img.src, { name: img.alt || "Image" })
    );
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

/**
 * Create a new collapsible process group
 */
function createProcessGroup(id) {
  const groupId = `process-group-${id}`;
  const group = document.createElement("div");
  group.id = groupId;
  group.classList.add("process-group");
  group.setAttribute("data-group-id", groupId);

  // Determine initial expansion state from current detail mode
  const initiallyExpanded = preferencesStore.detailMode !== "collapsed";
  if (initiallyExpanded) {
    group.classList.add("expanded");
  }

  // Create header
  const header = document.createElement("div");
  header.classList.add("process-group-header");
  header.innerHTML = `
    <span class="expand-icon"></span>
    <span class="group-title">Processing...</span>
    <span class="step-badge GEN">GEN</span>
    <span class="group-metrics">
      <span class="metric-time" title="Start time"><span class="material-symbols-outlined">schedule</span><span class="metric-value">--:--</span></span>
      <span class="metric-steps" title="Steps"><span class="material-symbols-outlined">footprint</span><span class="metric-value">0</span></span>
      <span class="metric-notifications" title="Warnings/Info/Hint" hidden><span class="material-symbols-outlined">priority_high</span><span class="metric-value">0</span></span>
      <span class="metric-duration" title="Duration"><span class="material-symbols-outlined">timer</span><span class="metric-value">0s</span></span>
    </span>
  `;

  // Add click handler for expansion
  header.addEventListener("click", () => {
    group.classList.toggle("expanded");
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
 * Schedule a step to collapse after a delay
 * Automatically handles cancellation on click and reset on hover
 */
function scheduleStepCollapse(stepElement, delayMs) {
  // skip if any existing timeout for this step
  if (stepElement.hasAttribute("data-collapse-timeout-id")) {
    return;
  }

  // Schedule the collapse
  const timeoutId = setTimeout(() => {
    stepElement.classList.remove("step-expanded");
    stepElement.removeAttribute("data-collapse-timeout-id");
    // Clear user-pinned flag when auto-collapsing
    stepElement.removeAttribute("data-user-pinned");
  }, delayMs);

  // Store the timeout ID
  stepElement.setAttribute("data-collapse-timeout-id", String(timeoutId));
}

/**
 * Cancel a scheduled collapse for a step
 */
function cancelStepCollapse(stepElement) {
  const timeoutIdStr = stepElement.getAttribute("data-collapse-timeout-id");
  if (!timeoutIdStr) return;
  const timeoutId = Number(timeoutIdStr);
  if (!Number.isNaN(timeoutId)) clearTimeout(timeoutId);
  stepElement.removeAttribute("data-collapse-timeout-id");
}

/**
 * Add interaction handlers to prevent fighting with user
 * - Hover: cancels the collapse timeout (keeps step open while reading)
 * - Leave: starts a new timeout ONLY if user hasn't clicked (no explicit interaction)
 * - Click anywhere on step: permanently cancels auto-collapse (user wants it open)
 */
function addStepCollapseInteractionHandlers(stepElement) {
  // On hover, cancel the timeout to keep it open while user is reading
  stepElement.addEventListener("mouseenter", () => {
    if (stepElement.classList.contains("step-expanded")) {
      cancelStepCollapse(stepElement);
    }
  });

  // On leave, start a new timeout ONLY if user hasn't explicitly clicked
  // and only in "current" mode (in "expanded" mode, everything stays open)
  stepElement.addEventListener("mouseleave", () => {
    const detailMode = preferencesStore.detailMode;
    // Don't schedule collapse in "expanded" mode - user wants everything open
    if (detailMode === "expanded") return;

    // Don't restart timeout if user has explicitly interacted (clicked)
    if (
      stepElement.classList.contains("step-expanded") &&
      !stepElement.hasAttribute("data-user-pinned")
    ) {
      scheduleStepCollapse(stepElement, STEP_COLLAPSE_DELAY_MS);
    }
  });

  // On click anywhere on step, permanently cancel auto-collapse
  stepElement.addEventListener("click", () => {
    if (stepElement.classList.contains("step-expanded")) {
      cancelStepCollapse(stepElement);
      // Mark as user-pinned so mouseleave won't restart timeout
      stepElement.setAttribute("data-user-pinned", "true");
    }
  });
}

/**
 * Find parent delegation step for nested agents (DOM-first, reverse scan).
 */
function findParentDelegationStep(group, agentno) {
  if (!group || !agentno || agentno <= 0) return null;
  const steps = group.querySelectorAll(".process-step");
  for (let i = steps.length - 1; i >= 0; i -= 1) {
    const step = steps[i];
    const stepAgent = Number(step.getAttribute("data-agent-number"));
    if (
      stepAgent === agentno - 1 &&
      step.getAttribute("data-log-type") === "tool" // map to the last tool call of superior agent
    ) {
      return step;
    }
  }
  return null;
}

/**
 * Get a concise title for a process step
 */
function getStepTitle(heading, kvps, type) {
  // code_exe: show command when finished
  // const showCommand =
  //   type === "code_exe" &&
  //   kvps?.code &&
  //   /done_all|code_execution_tool/.test(heading || "");
  // if (showCommand) {
  //   const s = kvps.session ?? kvps.Session;
  //   return `${s != null ? `[${s}] ` : ""}${kvps.runtime || "bash"}> ${kvps.code.trim()}`;
  // }

  // Try to get a meaningful title from heading or kvps
  if (heading && heading.trim()) {
    return cleanStepTitle(heading, 100);
  }

  // For warnings/errors without heading, use content preview as title
  if (type === "warning" || type === "error") {
    // We'll show full content in detail, so just use type as title
    return type === "warning" ? "Warning" : "Error";
  }

  if (kvps) {
    // Try common fields for title
    if (kvps.tool_name) {
      const headline = kvps.headline ? cleanStepTitle(kvps.headline, 60) : "";
      return `${kvps.tool_name}${headline ? ": " + headline : ""}`;
    }
    if (kvps.headline) {
      return cleanStepTitle(kvps.headline, 100);
    }
    if (kvps.query) {
      return truncateText(kvps.query, 100);
    }
    if (kvps.thoughts) {
      return truncateText(String(kvps.thoughts), 100);
    }
  }

  // Fallback: capitalize type (backend is source of truth)
  return type
    ? type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, " ")
    : "Process";
}

/**
 * Extract icon name from a key with icon:// prefix
 */
function extractIconFromKey(key) {
  if (!key) return null;
  const match = String(key).match(/^icon:\/\/([a-zA-Z0-9_]+)/);
  return match ? match[1] : null;
}

/**
 * Clean step title by removing icon:// prefixes and status phrases
 * Preserves agent markers (A1:, A2:, etc.) so users can see which subordinate agent is executing
 */
function cleanStepTitle(text, maxLength = 100) {
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
// function renderStepDetailContent(container, content, kvps, type = null) {
//   container.innerHTML = "";

//   drawKvpsIncremental(container, kvps);

//   // Special handling for response type - show content as markdown (for subordinate responses)
//   if (type === "response" && content && content.trim()) {
//     const responseDiv = document.createElement("div");
//     responseDiv.classList.add("step-response-content");

//     // Parse markdown
//     let processedContent = content;
//     processedContent = convertImageTags(processedContent);
//     processedContent = convertImgFilePaths(processedContent);
//     processedContent = convertFilePaths(processedContent);
//     processedContent = marked.parse(processedContent, { breaks: true });
//     processedContent = convertPathsToLinks(processedContent);
//     processedContent = addBlankTargetsToLinks(processedContent);

//     responseDiv.innerHTML = processedContent;
//     container.appendChild(responseDiv);
//     return;
//   }

//   // Special handling for warning/error types - always show content prominently
//   if ((type === "warning" || type === "error") && content && content.trim()) {
//     const warningDiv = document.createElement("div");
//     warningDiv.classList.add("step-warning-content");
//     warningDiv.textContent = content;
//     container.appendChild(warningDiv);
//     // Don't return - also show kvps if present
//   }

//   // Special handling for code_exe type - render as terminal-style output
//   if (type === "code_exe" && kvps) {
//     const runtime = kvps.runtime || kvps.Runtime || "bash";
//     const code = kvps.code || kvps.Code || "";
//     const output = content || "";

//     if (code || output) {
//       const terminalDiv = document.createElement("div");
//       terminalDiv.classList.add("step-terminal");

//       // Show output if present (no truncation - CSS handles max-height)
//       if (output && output.trim()) {
//         const outputPre = document.createElement("pre");
//         outputPre.classList.add("terminal-output");
//         // Escape HTML first, then convert paths to clickable links
//         let processedOutput = escapeHTML(output);
//         processedOutput = convertPathsToLinks(processedOutput);
//         outputPre.innerHTML = processedOutput;
//         terminalDiv.appendChild(outputPre);
//       }

//       container.appendChild(terminalDiv);
//     }

//     // Still render thoughts if present (but not reasoning - that's native model thinking, not structured output)
//     if (kvps.thoughts || kvps.thinking) {
//       const thoughtKey = kvps.thoughts ? "thoughts" : "thinking";
//       const thoughtValue = kvps[thoughtKey];
//       renderThoughts(container, thoughtValue);
//     }

//     return;
//   }

//   // Add KVPs if present
//   if (kvps && Object.keys(kvps).length > 0) {
//     const kvpsDiv = document.createElement("div");
//     kvpsDiv.classList.add("step-kvps");

//     for (const [key, value] of Object.entries(kvps)) {
//       // Skip internal/display keys
//       if (key === "finished" || key === "attachments") continue;

//       // Skip code_exe specific keys that we handle specially above
//       if (
//         type === "code_exe" &&
//         (key.toLowerCase() === "runtime" ||
//           key.toLowerCase() === "session" ||
//           key.toLowerCase() === "code")
//       ) {
//         continue;
//       }

//       const lowerKey = key.toLowerCase();

//       // Skip headline and tool_name - they're shown elsewhere
//       if (lowerKey === "headline" || lowerKey === "tool_name") continue;

//       // Skip query in agent steps - it's shown in the tool call step
//       if (type === "agent" && lowerKey === "query") continue;

//       // Special handling for thoughts - render with single lightbulb icon
//       // Skip reasoning
//       if (lowerKey === "reasoning") continue;
//       if (
//         lowerKey === "thoughts" ||
//         lowerKey === "thinking" ||
//         lowerKey === "reflection"
//       ) {
//         renderThoughts(kvpsDiv, value);
//         continue;
//       }

//       // Special handling for tool_args - render only for tool/mcp types (skip for agent)
//       if (lowerKey === "tool_args") {
//         // Skip tool_args for agent steps - it's shown in the tool call step
//         if (type === "agent") continue;

//         if (typeof value !== "object" || value === null) continue;
//         const argsDiv = document.createElement("div");
//         argsDiv.classList.add("step-tool-args");

//         for (const [argKey, argValue] of Object.entries(value)) {
//           const argRow = document.createElement("div");
//           argRow.classList.add("tool-arg-row");

//           const argLabel = document.createElement("span");
//           argLabel.classList.add("tool-arg-label");

//           const iconName = extractIconFromKey(argKey);
//           if (iconName) {
//             argLabel.innerHTML = `<span class="material-symbols-outlined">${iconName}</span>`;
//           } else {
//             argLabel.textContent = convertToTitleCase(argKey) + ":";
//           }

//           const argVal = document.createElement("span");
//           argVal.classList.add("tool-arg-value");

//           const argText = cleanTextValue(argValue);

//           argVal.textContent = truncateText(argText, 300);

//           argRow.appendChild(argLabel);
//           argRow.appendChild(argVal);
//           argsDiv.appendChild(argRow);
//         }

//         kvpsDiv.appendChild(argsDiv);
//         continue;
//       }

//       const kvpDiv = document.createElement("div");
//       kvpDiv.classList.add("step-kvp");

//       const keySpan = document.createElement("span");
//       keySpan.classList.add("step-kvp-key");

//       const iconName = extractIconFromKey(key);
//       if (iconName) {
//         keySpan.innerHTML = `<span class="material-symbols-outlined">${iconName}</span>`;
//       } else {
//         keySpan.textContent = convertToTitleCase(key) + ":";
//       }

//       const valueSpan = document.createElement("div");
//       valueSpan.classList.add("step-kvp-value");

//       if (typeof value === "string" && value.startsWith("img://")) {
//         const imgElement = document.createElement("img");
//         imgElement.classList.add("screenshot-img");
//         imgElement.src = value.replace("img://", "/image_get?path=");
//         imgElement.alt = "Image Attachment";
//         imgElement.style.cursor = "pointer";
//         imgElement.style.maxWidth = "100%";
//         imgElement.style.display = "block";
//         imgElement.style.marginTop = "4px";

//         // Add click handler and cursor change
//         imgElement.addEventListener("click", () => {
//           imageViewerStore.open(imgElement.src, { name: "Image Attachment" });
//         });

//         valueSpan.appendChild(imgElement);
//       } else {
//         const valueText = cleanTextValue(value);
//         valueSpan.textContent = truncateText(valueText, 1000);
//       }

//       kvpDiv.appendChild(keySpan);
//       kvpDiv.appendChild(valueSpan);
//       kvpsDiv.appendChild(kvpDiv);
//     }

//     container.appendChild(kvpsDiv);
//   }

//   // Add main content if present (JSON content)
//   if (content && content.trim()) {
//     const pre = document.createElement("pre");
//     pre.classList.add("msg-json");
//     pre.textContent = truncateText(content, 1000);
//     container.appendChild(pre);
//   }
// }

/**
 * Helper to render thoughts/reasoning with lightbulb icon
 */
// function renderThoughts(container, value) {
//   const thoughtsDiv = document.createElement("div");
//   thoughtsDiv.classList.add("step-thoughts", "msg-thoughts");

//   const thoughtText = cleanTextValue(value);

//   if (thoughtText) {
//     thoughtsDiv.innerHTML = `<span class="thought-icon material-symbols-outlined">lightbulb</span><span class="thought-text">${escapeHTML(thoughtText)}</span>`;
//     container.appendChild(thoughtsDiv);
//   }
// }

/**
 * Update process group header with step count, status, and metrics
 */
function updateProcessGroupHeader(group) {
  const header = group.querySelector(".process-group-header");
  const steps = group.querySelectorAll(".process-step");
  const titleEl = header.querySelector(".group-title");
  const badgeEl = header.querySelector(".step-badge");
  const metricsEl = header.querySelector(".group-metrics");
  const response = group.querySelector(".process-group-response");
  const isCompleted = !!response;
  const notificationsEl = metricsEl?.querySelector(".metric-notifications");

  // Update group title with the latest agent step heading
  if (titleEl) {
    // Find the last "agent" type step
    const agentSteps = Array.from(steps).filter(
      (step) => step.getAttribute("data-log-type") === "agent",
    );
    if (agentSteps.length > 0) {
      const lastAgentStep = agentSteps[agentSteps.length - 1];
      const lastHeading =
        lastAgentStep.querySelector(".step-title")?.textContent;
      if (lastHeading) {
        const cleanTitle = cleanStepTitle(lastHeading, 50);
        if (cleanTitle) {
          titleEl.textContent = cleanTitle;
        }
      }
    }
  }

  // If completed, set badge to END
  if (isCompleted) {
    badgeEl.outerHTML = `<span class="step-badge END">END</span>`;
  } else {
    // if not complete, clone the last step badge
    if (badgeEl && steps.length > 0) {
      const lastStep = steps[steps.length - 1];
      const code = lastStep.getAttribute("data-step-code");
      badgeEl.outerHTML = `<span class="step-badge ${code}">${code}</span>`;
    }
  }

  // Update step count in metrics - All GEN steps from all agents per process group
  const stepsMetricEl = metricsEl?.querySelector(".metric-steps .metric-value");
  if (stepsMetricEl) {
    const genSteps = group.querySelectorAll('.process-step[data-type="agent"]');
    stepsMetricEl.textContent = genSteps.length.toString();
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
  const durationMetricEl = metricsEl?.querySelector(
    ".metric-duration .metric-value",
  );
  if (durationMetricEl && steps.length > 0) {
    const firstTimestampMs = parseInt(
      steps[0]?.getAttribute("data-timestamp") || "0",
      10,
    );

    const lastStep = steps[steps.length - 1];
    const lastTimestampMs = parseInt(
      lastStep.getAttribute("data-timestamp") || "0",
      10,
    );

    const totalDurationMs = Math.max(0, lastTimestampMs - firstTimestampMs);

    durationMetricEl.textContent = formatDuration(totalDurationMs);
  }

  if (notificationsEl) {
    const counts = { warning: 0, info: 0, hint: 0 };
    steps.forEach((step) => {
      const stepType = step.getAttribute("data-type");
      if (Object.prototype.hasOwnProperty.call(counts, stepType)) {
        counts[stepType] += 1;
      }
    });

    const totalNotifications = counts.warning + counts.info + counts.hint;
    const countEl = notificationsEl.querySelector(".metric-value");
    notificationsEl.classList.remove("status-wrn", "status-inf", "status-hnt");

    if (totalNotifications > 0) {
      if (countEl) {
        countEl.textContent = totalNotifications.toString();
      }
      if (counts.warning > 0) {
        notificationsEl.classList.add("status-wrn");
      } else if (counts.info > 0) {
        notificationsEl.classList.add("status-inf");
      } else {
        notificationsEl.classList.add("status-hnt");
      }
      notificationsEl.hidden = false;
      notificationsEl.title = `Warnings: ${counts.warning}, Info: ${counts.info}, Hints: ${counts.hint}`;
    } else {
      notificationsEl.hidden = true;
    }
  }

  if (steps.length > 0) {
    // Get the last step's type for status
    // const lastStep = steps[steps.length - 1];
    // const lastType = lastStep.getAttribute("data-type");
    // const lastToolName = lastStep.getAttribute("data-tool-name");
    // const lastTitle = lastStep.querySelector(".step-title")?.textContent || "";
    // Update status badge
    // if (statusEl) {
    //   const statusCode = getStatusCode(lastType, lastToolName);
    //   const statusColorClass = getStatusClass(lastType, lastToolName);
    //   statusEl.textContent = statusCode;
    //   statusEl.className = `step-badge ${statusColorClass} group-status`;
    // }
    // Update title
    // if (titleEl) {
    //   // Prefer agent type steps for the group title as they contain thinking/planning info
    //   if (lastType === "agent" && lastTitle) {
    //     titleEl.textContent = cleanStepTitle(lastTitle, 50);
    //   } else {
    //     // Try to find the most recent agent step for a better title
    //     const agentSteps = group.querySelectorAll(
    //       '.process-step[data-type="agent"]',
    //     );
    //     if (agentSteps.length > 0) {
    //       const lastAgentStep = agentSteps[agentSteps.length - 1];
    //       const agentTitle =
    //         lastAgentStep.querySelector(".step-title")?.textContent || "";
    //       if (agentTitle) {
    //         titleEl.textContent = cleanStepTitle(agentTitle, 50);
    //         return;
    //       }
    //     }
    //     titleEl.textContent = cleanStepTitle(lastTitle, 50) || `Processing...`;
    //   }
    // }
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

  // // Update status badge to END
  // const statusEl = group.querySelector(".group-status");
  // if (statusEl) {
  //   // statusEl.innerHTML = '<span class="badge-icon material-symbols-outlined">check</span>END';
  //   statusEl.innerHTML = "END";
  //   statusEl.className = "step-badge status-end group-status";
  // }

  // // Update title if response title is available
  // const titleEl = group.querySelector(".group-title");
  // if (titleEl && responseTitle) {
  //   const cleanTitle = cleanStepTitle(responseTitle, 50);
  //   if (cleanTitle) {
  //     titleEl.textContent = cleanTitle;
  //   }
  // }

  // Add completed class to group
  group.classList.add("process-group-completed");

  // Collapse all expanded steps when processing is done (in "current" mode) with delay
  const detailMode = preferencesStore.detailMode;
  if (detailMode === "current") {
    // Schedule collapse for all expanded steps (deterministic)
    const allExpandedSteps = group.querySelectorAll(
      ".process-step.step-expanded",
    );
    allExpandedSteps.forEach((expandedStep) => {
      scheduleStepCollapse(expandedStep, FINAL_STEP_COLLAPSE_DELAY_MS);
    });
  }

  // Calculate final duration from backend data (difference between first and last timestamps)
  const steps = group.querySelectorAll(".process-step");
  const firstTimestampMs = parseInt(
    steps[0]?.getAttribute("data-timestamp") || "0",
    10,
  );
  const lastTimestampMs = parseInt(
    steps[steps.length - 1]?.getAttribute("data-timestamp") || "0",
    10,
  );
  const totalDurationMs = Math.max(0, lastTimestampMs - firstTimestampMs);

  // Update duration metric with final value from backend
  const metricsEl = group.querySelector(".group-metrics");
  const durationMetricEl = metricsEl?.querySelector(
    ".metric-duration .metric-value",
  );
  if (durationMetricEl && totalDurationMs > 0) {
    durationMetricEl.textContent = formatDuration(totalDurationMs);
  }
}

// gets or creates a child DOM element
function ensureChild(parent, selector, tagName, ...classNames) {
  let el = parent.querySelector(selector);
  if (!el) {
    el = document.createElement(tagName);
    if (classNames.length) el.classList.add(...classNames);
    parent.appendChild(el);
  }
  return el;
}

// returns true if this is the initial render of a chat eg. when reloading window, switching chat or catching up after a break
// returns false when already in a rendered chat and adding messages regurarly
function isMassRender() {
  return _massRender;
}
