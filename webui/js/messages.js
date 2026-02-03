// message actions and components
import { store as imageViewerStore } from "../components/modals/image-viewer/image-viewer-store.js";
import { marked } from "../vendor/marked/marked.esm.js";
import { store as _messageResizeStore } from "/components/messages/resize/message-resize-store.js"; // keep here, required in html
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";
import {
  createActionButton,
  copyToClipboard,
} from "/components/messages/action-buttons/simple-action-buttons.js";
import { store as stepDetailStore } from "/components/modals/process-step-detail/step-detail-store.js";
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";
import { formatDuration } from "./time-utils.js";
import { Scroller } from "./scroller.js";

// Delay before collapsing previous steps when a new step is added
const STEP_COLLAPSE_DELAY = {
  "agent": 2000,
  "other": 4000, // tools should stay longer as next gen step is placed quickly
}
// delay collapse when hovering
const STEP_COLLAPSE_HOVER_DELAY_MS = 5000;

// dom references
let _chatHistory = null;

// state vars
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

// entrypoint called from poll/WS communication, this is how all messages are rendered and updated
// input is raw log format
export function setMessages(messages) {
  // set _massRender flag for handlers to know how to behave
  const history = getChatHistoryEl();
  const historyEmpty = !history || history.childElementCount === 0;
  const isLargeAppend = !historyEmpty && messages.length > 10;
  const cutoff = isLargeAppend ? Math.max(0, messages.length - 2) : 0;
  const massRender = historyEmpty || isLargeAppend;

  const mainScroller = new Scroller(history, { smooth: !massRender, toleranceRem: 4, reapplyDelayMs: 1000 });

  const results = []
  
  // process messages
  for (let i = 0; i < messages.length; i++) {
    _massRender = historyEmpty || (isLargeAppend && i < cutoff);
    results.push(setMessage(messages[i]) || {});
  }

  // reset _massRender flag
  _massRender = false;

  const shouldScroll = historyEmpty || !results[results.length - 1]?.dontScroll;

  if(shouldScroll) mainScroller.reApplyScroll();
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

function getChatHistoryEl() {
  if (!_chatHistory) _chatHistory = document.getElementById("chat-history");
  return _chatHistory;
}

function getLastMessageGroup() {
  return getChatHistoryEl()?.lastElementChild;
}

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

function getLastProcessGroup(allowCompleted = true) {
  const lastContainer = getLastMessageGroup();
  if (!lastContainer) return null;
  const groups = lastContainer.querySelectorAll(".process-group");
  if (groups.length === 0) return null;
  const group = groups[groups.length - 1];
  if (!allowCompleted && isProcessGroupComplete(group)) return null;

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
  return group;
}

function buildDetailPayload(stepData, extras = {}) {
  if (!stepData) return null;
  return {
    ...stepData,
    ...extras,
  };
}

function drawProcessStep({
  id,
  title,
  code,
  classes,
  kvps,
  content,
  contentClasses,
  actionButtons = [],
  log,
  allowCompletedGroup = false,
  ...additional
}) {
  // group and steps DOM elements
  const stepId = `process-step-${id}`;
  let step = document.getElementById(stepId);

  const group =
    getStepProcessGroup(step) ||
    getOrCreateProcessGroup(id, allowCompletedGroup);
  const stepsContainer = group.querySelector(".process-steps");

  const isNewStep = !step;
  const isGroupComplete = isProcessGroupComplete(group);

  // Set start timestamp on group when first step is created
  if (isNewStep && !group.hasAttribute("data-start-timestamp") && log.timestamp) {
    group.setAttribute("data-start-timestamp", String(log.timestamp));
  }

  if (isNewStep) {
    // create the base DOM element for the step
    step = document.createElement("div");
    step.id = stepId;
    step.classList.add("process-step");

    // set data attributes of the step
    step.setAttribute("data-log-type", log.type);
    step.setAttribute("data-step-id", id);
    step.setAttribute("data-agent-number", log.agentno);
    
    // set timestamp attribute (convert to milliseconds for duration calculation)
    if (log.timestamp) {
      step.setAttribute("data-timestamp", String(Math.round(log.timestamp * 1000)));
    }

    // apply step classes
    if (classes) step.classList.add(...classes);

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

    // expand all or current step based on settings
    const detailMode = preferencesStore.detailMode;
    // const isActiveGroup = group.classList.contains("active");

    //expand all
    if (detailMode === "expanded") {
      step.classList.add("expanded");
      // expand current step and schedule collapse of previous
    } else if (
      detailMode === "current" &&
      !isMassRender() &&
      !isGroupComplete
    ) {
      stepsContainer
        .querySelectorAll(".process-step.expanded")
        .forEach((expandedStep) => {
          const delay = STEP_COLLAPSE_DELAY[expandedStep.getAttribute("data-log-type")] || STEP_COLLAPSE_DELAY.other;
          console.log("collapsing", expandedStep.getAttribute("data-log-type"), delay);
          scheduleStepCollapse(expandedStep, delay);
        });
      step.classList.add("expanded");
    }

    // create step header
    const stepHeader = ensureChild(
      step,
      ".process-step-header",
      "div",
      "process-step-header",
    );
  }

  // is step expanded?
  const isExpanded = step.classList.contains("expanded");

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
    "process-step-detail-scroll" );

  // set click handlers
  setupProcessStepHandlers(step, stepHeader);

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

  // auto-scroller of the step detail
  const detailScroller = new Scroller(stepDetailScroll, {
    smooth: !isMassRender(), toleranceRem: 4
  }); // scroller for step detail content

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

  // reapply scroll position (autoscroll if bottom) - only when expanded already and not mass rendering
  if (isExpanded) detailScroller.reApplyScroll();

  // Render action buttons: get/create container, clear, append
  const stepActionBtns = ensureChild(
    stepDetail,
    ".step-detail-actions",
    "div",
    "step-detail-actions",
    "step-action-buttons",
  );
  stepActionBtns.textContent = "";
  (actionButtons || [])
    .filter(Boolean)
    .forEach((button) => stepActionBtns.appendChild(button));

  // update the process grop header by this step
  updateProcessGroupHeader(group);

  // remove shine from previous steps and add to this one if new and not completed
  if (isNewStep && !isGroupComplete) {
    stepDetailScroll
      .querySelectorAll(".step-title.shiny-text")
      .forEach((el) => {
        el.classList.remove("shiny-text");
      });
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

function drawStandaloneMessage({
  id,
  heading,
  content,
  position = "mid",
  forceNewGroup = false,
  containerClasses = [],
  mainClass = "",
  messageClasses = [],
  contentClasses = [],
  markdown = false,
  latex = false,
  kvps = null,
  actionButtons = [],
}) {
  // end last process group on any standalone messge
  completeLastProcessGroup();

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

  // Collapsible with action buttons
  setupCollapsible(messageDiv, ".step-action-buttons", false, actionButtons);

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
  smoothStream = false,
}) {
  // Find existing message div or create new one
  let messageDiv = messageContainer.querySelector(".message");
  if (!messageDiv) {
    messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    messageContainer.appendChild(messageDiv);
  }

  // Update message classes (preserve collapsible state)
  const preserve = ["message-collapsible", "expanded", "has-overflow"]
    .filter((c) => messageDiv.classList.contains(c)).join(" ");
  messageDiv.className = `message ${mainClass} ${messageClasses.join(" ")} ${preserve}`;

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
  bodyDiv.dataset.scrollStabilization = "1";
  const scroller = new Scroller(bodyDiv, { smooth: !isMassRender() });

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

      // let spanElement = contentDiv.querySelector("span");
      // if (!spanElement) {
      //   spanElement = document.createElement("span");
      //   contentDiv.appendChild(spanElement);
      // }

      let processedContent = content;
      processedContent = convertImageTags(processedContent);
      processedContent = convertImgFilePaths(processedContent);
      processedContent = convertFilePaths(processedContent);
      processedContent = marked.parse(processedContent, { breaks: true });
      processedContent = convertPathsToLinks(processedContent);
      processedContent = addBlankTargetsToLinks(processedContent);

      // do a smooth stream if requested
      if (smoothStream) smoothRender(contentDiv, processedContent);
      else contentDiv.innerHTML = processedContent;

      // KaTeX rendering for markdown
      if (latex) {
        contentDiv.querySelectorAll("latex").forEach((element) => {
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

      // let spanElement = preElement.querySelector("span");
      // if (!spanElement) {
      //   spanElement = document.createElement("span");
      //   preElement.appendChild(spanElement);
      // }

      if (smoothStream) smoothRender(preElement, convertHTML(content));
      else preElement.innerHTML = convertHTML(content);
    }
  } else {
    // Remove content if it exists but content is empty
    const existingContent = bodyDiv.querySelector(".msg-content");
    if (existingContent) {
      existingContent.remove();
    }
  }

  // reapply scroll position or reset for collapsed
  messageDiv.classList.contains("expanded")
    ? scroller.reApplyScroll()
    : (bodyDiv.scrollTop = 0);

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
  const contentText = String(content ?? "");
  const actionButtons = contentText.trim()
    ? [
        createActionButton("speak", "", () => speechStore.speak(contentText)),
        createActionButton("copy", "", () => copyToClipboard(contentText)),
      ].filter(Boolean)
    : [];

  return drawStandaloneMessage({
    id,
    heading,
    content,
    position: "left",
    containerClasses: ["ai-container"],
    mainClass: "message-default",
    messageClasses: ["message-ai"],
    contentClasses: ["msg-json"],
    kvps,
    actionButtons,
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
  if (kvps?.thoughts) displayKvps["icon://lightbulb[Thoughts]"] = kvps.thoughts;
  if (kvps?.step) displayKvps["icon://step[Step]"] = kvps.step;
  const thoughtsText = String(kvps?.thoughts ?? "");
  const headerLabels = [
    kvps?.tool_name && { label: kvps.tool_name, class: "tool-name-badge" },
  ].filter(Boolean);
  const actionButtons = [
    createActionButton("detail", "", () =>
      stepDetailStore.showStepDetail(
        buildDetailPayload(arguments[0], { headerLabels }),
      ),
    ),
  ];

  if (thoughtsText.trim()) {
    actionButtons.push(
      createActionButton("speak", "", () => speechStore.speak(thoughtsText)),
    );
    actionButtons.push(
      createActionButton("copy", "", () => copyToClipboard(thoughtsText)),
    );
  }

  return drawProcessStep({
    id,
    title,
    code: "GEN",
    classes: null,
    kvps: displayKvps,
    actionButtons,
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
    const contentText = String(content ?? "");
    const actionButtons = contentText.trim()
      ? [
          createActionButton("speak", "", () => speechStore.speak(contentText)),
          createActionButton("copy", "", () => copyToClipboard(contentText)),
        ].filter(Boolean)
      : [];
    return drawProcessStep({
      id,
      title,
      code: "RES",
      kvps: {},
      type,
      heading,
      content,
      timestamp,
      agentno,
      actionButtons,
      log: arguments[0],
    });
  }

  // response of agent 0, render as response to user
  // get last process group or create new container (if first message)
  const group = getLastProcessGroup();
  let container = null;

  if (group) {
    // new response, collapse all previous steps once
    if (!group.querySelector(".process-group-response")) {
      if (preferencesStore.detailMode == "current")
        group.querySelectorAll(".process-step").forEach((step) => {
          scheduleStepCollapse(step);
        });
    }

    container = ensureChild(
      group,
      ".process-group-response",
      "div",
      "process-group-response",
    );
  } else container = getOrCreateMessageContainer(id, "left");

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
    smoothStream: false ,// smooth render disabled, not reliable yet !isMassRender(), // stream smoothly if not in mass render mode
  });

  // Collapsible with action buttons
  const responseText = String(content ?? "");
  const responseActionButtons = responseText.trim()
    ? [
        createActionButton("speak", "", () => speechStore.speak(responseText)),
        createActionButton("copy", "", () => copyToClipboard(responseText)),
      ].filter(Boolean)
    : [];
  setupCollapsible(messageDiv, ":scope > .step-action-buttons", !isMassRender(), responseActionButtons);

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

  // end last process group on any user message
  completeLastProcessGroup();

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

  // Render action buttons: get/create container, clear, append
  const userText = String(content ?? "");
  const userActionButtons = userText.trim()
    ? [
        createActionButton("speak", "", () => speechStore.speak(userText)),
        createActionButton("copy", "", () => copyToClipboard(userText)),
      ].filter(Boolean)
    : [];
  const actionButtonsContainer = ensureChild(
    messageDiv,
    ".step-action-buttons",
    "div",
    "step-action-buttons",
  );
  actionButtonsContainer.textContent = "";
  userActionButtons.forEach((button) =>
    actionButtonsContainer.appendChild(button),
  );
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

  const tool_name = kvps?._tool_name || "";

  if(!tool_name){
   return drawMessageToolSimple({ ...arguments[0] }); 
  } else if (kvps._tool_name === "skills_tool") {
    return drawMessageToolSimple({ ...arguments[0], code: "SKL" });
  } else if (kvps._tool_name === "vision_load") {
    return drawMessageToolSimple({ ...arguments[0], code: "EYE" });
  } else if (kvps._tool_name === "search_engine") {
    return drawMessageToolSimple({ ...arguments[0], code: "WEB" });
  } else if (kvps._tool_name === "browser_agent") {
    return drawMessageToolSimple({ ...arguments[0], code: "WWW" });
  } else if (kvps._tool_name.startsWith("memory_")) {
    return drawMessageToolSimple({ ...arguments[0], code: "MEM" });
  } else {
    return drawMessageToolSimple({ ...arguments[0] });
  }

}

export function drawMessageToolSimple({
  id,
  type,
  heading,
  content,
  kvps = null,
  timestamp = null,
  agentno = 0,
  code,
  displayKvps,
  ...additional
}) {
  const title = cleanStepTitle(heading);
  displayKvps = displayKvps || { ...kvps };
  const headerLabels = [
    kvps?._tool_name && { label: kvps._tool_name, class: "tool-name-badge" },
  ].filter(Boolean);
  const contentText = String(content ?? "");
  const actionButtons = contentText.trim()
    ? [
        createActionButton("detail", "", () =>
          stepDetailStore.showStepDetail(
            buildDetailPayload(arguments[0], { headerLabels }),
          ),
        ),
        createActionButton("speak", "", () => speechStore.speak(contentText)),
        createActionButton("copy", "", () => copyToClipboard(contentText)),
      ].filter(Boolean)
    : [];

  return drawProcessStep({
    id,
    title,
    code: code || "USE",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    actionButtons,
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
  if (kvps?.code && /done_all|code_execution_tool/.test(heading || "")) {
    const s = kvps.session;
    title = `${s != null ? `[${s}] ` : ""}${kvps.runtime || "bash"}> ${kvps.code.trim()}`;
  } else {
    // during execution show the original heading (current step)
    title = cleanStepTitle(heading);
  }

  // KVPS to show
  const displayKvps = {};
  // if (kvps?.runtime) displayKvps.runtime = kvps.runtime;
  // if (kvps?.session>=0) displayKvps.session = kvps.session;

  const headerLabels = [
    kvps?.runtime && { label: kvps.runtime, class: "tool-name-badge" },
    kvps?.session != null && {
      label: `Session ${kvps.session}`,
      class: "header-label",
    },
  ].filter(Boolean);

  // render the standard step
  const commandText = String(kvps?.code ?? "");
  const outputText = String(content ?? "");
  const actionButtons = [
    createActionButton("detail", "", () =>
      stepDetailStore.showStepDetail(
        buildDetailPayload(arguments[0], { headerLabels }),
      ),
    ),
    commandText.trim()
      ? createActionButton("copy", "Command", () =>
          copyToClipboard(commandText),
        )
      : null,
    outputText.trim()
      ? createActionButton("copy", "Output", () => copyToClipboard(outputText))
      : null,
  ].filter(Boolean);
  const stepData = drawProcessStep({
    id,
    title,
    code: "EXE",
    classes: null,
    kvps: displayKvps,
    content,
    contentClasses: ["terminal-output"],
    actionButtons,
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
  const answerText = String(kvps?.answer ?? "");
  const actionButtons = answerText.trim()
    ? [
        createActionButton("detail", "", () =>
          stepDetailStore.showStepDetail(
            buildDetailPayload(arguments[0], { headerLabels: [] }),
          ),
        ),
        createActionButton("speak", "", () => speechStore.speak(answerText)),
        createActionButton("copy", "", () => copyToClipboard(answerText)),
      ].filter(Boolean)
    : [];

  return drawProcessStep({
    id,
    title,
    code: "HDL",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    actionButtons,
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
  const headerLabels = [
    kvps?.tool_name && { label: kvps.tool_name, class: "tool-name-badge" },
  ].filter(Boolean);
  const contentText = String(content ?? "");
  const actionButtons = contentText.trim()
    ? [
        createActionButton("detail", "", () =>
          stepDetailStore.showStepDetail(
            buildDetailPayload(arguments[0], { headerLabels }),
          ),
        ),
        createActionButton("speak", "", () => speechStore.speak(contentText)),
        createActionButton("copy", "", () => copyToClipboard(contentText)),
      ].filter(Boolean)
    : [];

  return drawProcessStep({
    id,
    title,
    code: "MCP",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    actionButtons,
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
  const headerLabels = [
    kvps?.tool_name && { label: kvps.tool_name, class: "tool-name-badge" },
  ].filter(Boolean);
  const contentText = String(content ?? "");
  const actionButtons = contentText.trim()
    ? [
        createActionButton("detail", "", () =>
          stepDetailStore.showStepDetail(
            buildDetailPayload(arguments[0], { headerLabels }),
          ),
        ),
        createActionButton("speak", "", () => speechStore.speak(contentText)),
        createActionButton("copy", "", () => copyToClipboard(contentText)),
      ].filter(Boolean)
    : [];

  return drawProcessStep({
    id,
    title,
    code: "SUB",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    actionButtons,
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
  const title = cleanStepTitle(heading || content);
  let displayKvps = { ...kvps };
  const contentText = String(content ?? "");
  const actionButtons = contentText.trim()
    ? [
        createActionButton("speak", "", () => speechStore.speak(contentText)),
        createActionButton("copy", "", () => copyToClipboard(contentText)),
      ].filter(Boolean)
    : [];

  return drawProcessStep({
    id,
    title,
    code: "INF",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    actionButtons,
    log: arguments[0],
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
  const title = cleanStepTitle(heading || content);
  const contentText = String(content ?? "");
  const actionButtons = contentText.trim()
    ? [
        createActionButton("speak", "", () => speechStore.speak(contentText)),
        createActionButton("copy", "", () => copyToClipboard(contentText)),
      ].filter(Boolean)
    : [];

  const result = drawProcessStep({
    id,
    title,
    code: "UTL",
    classes: ["message-util"],
    kvps,
    content,
    actionButtons,
    log: arguments[0],
    allowCompletedGroup: true,
  });


  result.dontScroll = !preferencesStore.showUtils;
  return result;
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
  const contentText = String(content ?? "");
  const actionButtons = contentText.trim()
    ? [
        createActionButton("speak", "", () => speechStore.speak(contentText)),
        createActionButton("copy", "", () => copyToClipboard(contentText)),
      ].filter(Boolean)
    : [];

  return drawStandaloneMessage({
    id,
    title,
    // statusClass,
    statusCode: "HNT",
    kvps,
    type,
    heading,
    content,
    timestamp,
    agentno,
    actionButtons,
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
  const title = cleanStepTitle(heading || content);
  let displayKvps = { ...kvps };

  return drawProcessStep({
    id,
    title,
    code: "HDL",
    classes: null,
    kvps: displayKvps,
    content,
    // contentClasses: [],
    actionButtons: [],
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
  const title = cleanStepTitle(heading || content);
  let displayKvps = { ...kvps };
  const contentText = String(content ?? "");
  const actionButtons = contentText.trim()
    ? [
        createActionButton("speak", "", () => speechStore.speak(contentText)),
        createActionButton("copy", "", () => copyToClipboard(contentText)),
      ].filter(Boolean)
    : [];

  //TODO: if process group is running, append there instead
  // return drawProcessStep({
  //   id,
  //   title,
  //   code: "WRN",
  //   classes: null,
  //   kvps: displayKvps,
  //   content,
  //   // contentClasses: [],
  //   log: arguments[0],
  // });
  return drawStandaloneMessage({
    id,
    heading,
    content,
    position: "mid",
    containerClasses: ["ai-container", "center-container"],
    mainClass: "message-warning",
    kvps,
    actionButtons,
  });
}

export function drawMessageError({
  id,
  heading,
  content,
  kvps = null,
  ...additional
}) {
  const contentText = String(content ?? "");
  const errorText = kvps?.text || "Error";
  const errorHeading = errorText ? `Error - ${errorText}` : "Error";
  const actionButtons = [
    createActionButton("detail", "", () =>
      stepDetailStore.showStepDetail(
        buildDetailPayload(arguments[0], { headerLabels: [] }),
      ),
    ),
    contentText.trim()
      ? createActionButton("copy", "", () => copyToClipboard(contentText))
      : null,
  ].filter(Boolean);

  return drawStandaloneMessage({
    id,
    heading: errorHeading,
    content,
    position: "mid",
    containerClasses: ["ai-container", "center-container"],
    mainClass: "message-error",
    actionButtons,
  });
}

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
      const convertedKey = convertIcons(String(key), "");
      if (convertedKey !== String(key)) {
        th.innerHTML = convertedKey;
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
        const span = document.createElement("p");
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
    if (table) table.remove();
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

// markdown render helpers //

// wraps an element with a container div
const wrapElement = (el, className) => {
  const wrapper = document.createElement("div");
  wrapper.className = className;
  el.parentNode.insertBefore(wrapper, el);
  wrapper.appendChild(el);
  return wrapper;
};

// data extractors
const extractTableTSV = (table) =>
  [...table.rows]
    .map((row) =>
      [...row.cells]
        .map((cell) =>
          cell.textContent.replace(/\t/g, "  ").replace(/\n/g, " "),
        )
        .join("\t"),
    )
    .join("\n");

function adjustMarkdownRender(element) {
  // find all tables in the element
  const tables = element.querySelectorAll("table");
  tables.forEach((el) => {
    const wrapper = wrapElement(el, "message-markdown-table-wrap");
    const outerWrapper = wrapElement(wrapper, "markdown-block-wrap");
    const actionsDiv = document.createElement("div");
    actionsDiv.className = "step-action-buttons";
    actionsDiv.appendChild(
      createActionButton("copy", "", () =>
        copyToClipboard(extractTableTSV(el)),
      ),
    );
    outerWrapper.appendChild(actionsDiv);
  });

  // find all code blocks
  const codeElements = element.querySelectorAll("pre > code");
  codeElements.forEach((code) => {
    const pre = code.parentNode;
    const wrapper = wrapElement(pre, "code-block-wrapper");
    const outerWrapper = wrapElement(wrapper, "markdown-block-wrap");
    const actionsDiv = document.createElement("div");
    actionsDiv.className = "step-action-buttons";
    actionsDiv.appendChild(
      createActionButton("copy", "", () => copyToClipboard(code.textContent)),
    );
    outerWrapper.appendChild(actionsDiv);
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
      <span class="metric-steps display-none" title="Steps"><span class="material-symbols-outlined">footprint</span><span class="metric-value">0</span></span>
      <span class="metric-notifications" title="Warnings/Info/Hint" hidden><span class="material-symbols-outlined">priority_high</span><span class="metric-value">0</span></span>
      <span class="metric-duration display-none" title="Duration"><span class="material-symbols-outlined">timer</span><span class="metric-value">--</span></span>

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
function scheduleStepCollapse(stepElement, delayMs=STEP_COLLAPSE_DELAY.other) {
  // skip if any existing timeout for this step
  if (stepElement.hasAttribute("data-collapse-timeout-id")) return;
  // skip already collapsed steps
  if (!stepElement.classList.contains("expanded")) return;

  // Schedule the collapse
  const timeoutId = setTimeout(() => {
    stepElement.removeAttribute("data-collapse-timeout-id");

    if (stepElement.dataset.clicked === "true") {
      console.log(`Skip clicked collapse: ${stepElement.id}`);
      return;
    }

    if (stepElement.matches(":hover")) {
      console.log(`Delay hover collapse: ${stepElement.id}`);
      scheduleStepCollapse(stepElement, STEP_COLLAPSE_HOVER_DELAY_MS);
      return;
    }

    console.log(`Collapse step: ${stepElement.id}`);
    stepElement.classList.remove("expanded");
  }, delayMs);

  // Store the timeout ID
  stepElement.setAttribute("data-collapse-timeout-id", String(timeoutId));
}

function setupProcessStepHandlers(stepElement, stepHeader) {
  if (!stepElement.hasAttribute("data-step-handlers")) {
    stepElement.setAttribute("data-step-handlers", "true");

    stepElement.addEventListener(
      "click",
      function handler() {
        stepElement.dataset.clicked = "true";
        console.log(`Step clicked: ${stepElement.id}`);
      },
      { once: true },
    );
  }

  if (stepHeader && !stepHeader.hasAttribute("data-expand-handler")) {
    stepHeader.setAttribute("data-expand-handler", "true");
    stepHeader.addEventListener("click", (e) => {
      e.stopPropagation();
      cancelStepCollapse(stepElement);
      stepElement.dataset.clicked = "true";
      stepElement.classList.toggle("expanded");
    });
  }
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
 * Convert icon://name[Optional Tooltip] into a material icon span.
 * Tooltip supports escaped brackets inside, e.g. [Tooltip of \[brackets\]].
 */
export function convertIcons(html, classes = "") {
  if (html == null) return "";

  return String(html).replace(
    /icon:\/\/([a-zA-Z0-9_]+)(\[(?:\\.|[^\]])*\])?/g,
    (match, iconName, tooltipBlock) => {
      if (!tooltipBlock) {
        return `<span class="icon material-symbols-outlined ${classes}">${iconName}</span>`;
      }

      const tooltipRaw = tooltipBlock
        .slice(1, -1)
        .replace(/\\\[/g, "[")
        .replace(/\\\]/g, "]")
        .replace(/\\\\/g, "\\");

      const tooltip = escapeHTML(tooltipRaw);

      return `<span class="icon material-symbols-outlined ${classes}" title="${tooltip}" data-bs-placement="top" data-bs-trigger="hover">${iconName}</span>`;
    },
  );
}

/**
 * Clean step title by removing icon:// prefixes and status phrases
 * Preserves agent markers (A1:, A2:, etc.) so users can see which subordinate agent is executing
 */
function cleanStepTitle(text, maxLength = 100) {
  if (!text) return "";
  let cleaned = String(text);

  // Remove icon:// patterns (e.g., "icon://network_intelligence" or "icon://network_intelligence[Tooltip]")
  cleaned = cleaned.replace(/icon:\/\/[a-zA-Z0-9_]+(\[(?:\\.|[^\]])*\])?\s*/g, "");

  // Trim whitespace
  cleaned = cleaned.trim();

  return truncateText(cleaned, maxLength);
}

/**
 * Update process group header with step count, status, and metrics
 */
function updateProcessGroupHeader(group) {
  const header = group.querySelector(".process-group-header");
  const steps = group.querySelectorAll(".process-step");
  const titleEl = header.querySelector(".group-title");
  const badgeEl = header.querySelector(".step-badge");
  const metricsEl = header.querySelector(".group-metrics");
  const isCompleted = isProcessGroupComplete(group);
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
    // set end badge
    badgeEl.outerHTML = `<span class="step-badge END">END</span>`;
    // remove shine from any steps
    group.querySelectorAll(".step-title.shiny-text").forEach((el) => {
      el.classList.remove("shiny-text");
    });
  } else {
    // if not complete, clone the last step badge
    if (badgeEl && steps.length > 0) {
      const lastStep = steps[steps.length - 1];
      const code = lastStep.getAttribute("data-step-code");
      badgeEl.outerHTML = `<span class="step-badge ${code}">${code}</span>`;
    }
  }

  // Update step count in metrics - All GEN steps from all agents per process group
  const stepMetricContainerEl = metricsEl?.querySelector(".metric-steps");
  const stepsMetricValEl = stepMetricContainerEl?.querySelector(".metric-value");
  if (stepsMetricValEl) {
    let genSteps = group.querySelectorAll('.process-step[data-log-type="agent"]').length;
    genSteps -= 1; // don't count response as step
    stepsMetricValEl.textContent = genSteps.toString();
    if (genSteps <= 0) stepMetricContainerEl.classList.add("display-none"); // hide when no steps
    else stepMetricContainerEl.classList.remove("display-none");
  }

  // Update time metric
  const timeMetricContainerEl = metricsEl?.querySelector(".metric-time");
  const timeMetricEl = metricsEl?.querySelector(".metric-time .metric-value");
  const startTimestamp = group.getAttribute("data-start-timestamp");
  if (timeMetricEl && startTimestamp) {
    const date = new Date(parseFloat(startTimestamp) * 1000);
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    timeMetricEl.textContent = `${hours}:${minutes}`;
    if (timeMetricContainerEl) {
      const fullDateTime = date.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
      timeMetricContainerEl.title = timeMetricContainerEl.dataset.bsOriginalTitle =
        fullDateTime;
    }
  }

  const firstTimestampMs = parseInt(
    steps[0]?.getAttribute("data-timestamp") || "0",
    10,
  );
  const lastTimestampMs = parseInt(
    steps[steps.length - 1]?.getAttribute("data-timestamp") || "0",
    10,
  );
  const durationText =
    isCompleted &&
    metricsEl &&
    steps.length > 0 &&
    firstTimestampMs > 0 &&
    lastTimestampMs > 0 &&
    formatDuration(Math.max(0, lastTimestampMs - firstTimestampMs));

  const durationMetricContainerEl = metricsEl?.querySelector(".metric-duration");
  const durationMetricValEl = durationMetricContainerEl?.querySelector(".metric-value");
  if (durationMetricContainerEl && durationMetricValEl && durationText) {
    durationMetricValEl.textContent = durationText;
    durationMetricContainerEl.classList.remove("display-none");
  } else if (durationMetricContainerEl) {
    durationMetricContainerEl.classList.add("display-none");
  }

  if (notificationsEl) {
    const counts = { warning: 0, info: 0 };
    steps.forEach((step) => {
      const stepType = step.getAttribute("data-log-type");
      if (Object.prototype.hasOwnProperty.call(counts, stepType)) {
        counts[stepType] += 1;
      }
    });

    const totalNotifications = counts.warning + counts.info;
    const countEl = notificationsEl.querySelector(".metric-value");
    notificationsEl.classList.remove("status-wrn", "status-inf");

    if (totalNotifications > 0) {
      if (countEl) {
        countEl.textContent = totalNotifications.toString();
      }
      if (counts.warning > 0) {
        notificationsEl.classList.add("status-wrn");
      } else if (counts.info > 0) {
        notificationsEl.classList.add("status-inf");
      }
      notificationsEl.hidden = false;
      notificationsEl.title = `Warnings: ${counts.warning}, Info: ${counts.info}`;
    } else {
      notificationsEl.hidden = true;
    }
  }
}

function isProcessGroupComplete(group) {
  // manually closed group
  if (group?.hasAttribute?.("data-group-complete")) return true;
  // naturally completed group
  const response = group.querySelector(".process-group-response");
  return !!response;
}

// manually complete last process group
export function completeLastProcessGroup() {
  const group = getLastProcessGroup();
  if (!group || isProcessGroupComplete(group)) return;
  group.setAttribute("data-group-complete", "true");
  updateProcessGroupHeader(group);
}

function getStepProcessGroup(step) {
  return step?.closest(".process-group");
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

// Setup collapsible message with expand button and action buttons
function setupCollapsible(messageDiv, containerSelector, initialExpanded, actionButtons = []) {
  messageDiv.classList.add("message-collapsible");
  messageDiv.classList.toggle("expanded", initialExpanded);

  const container = ensureChild(messageDiv, containerSelector, "div", "step-action-buttons");
  container.textContent = "";

  const btn = ensureChild(container, ".expand-btn", "button", "expand-btn");
  const syncBtn = () => {
    const exp = messageDiv.classList.contains("expanded");
    btn.textContent = exp ? "Show less" : "Show more";
    btn.classList.toggle("show-less-btn", exp);
    btn.classList.toggle("show-more-btn", !exp);
  };
  syncBtn();
  btn.onclick = () => {
    messageDiv.classList.toggle("expanded");
    syncBtn();
    messageDiv.classList.contains("expanded")
      || (messageDiv.querySelector(".message-body").scrollTop = 0);
  };

  actionButtons.filter(Boolean).forEach((b) => container.appendChild(b));

  // Detect overflow after render
  requestAnimationFrame(() => {
    const body = messageDiv.querySelector(".message-body");
    const fontSize = parseFloat(getComputedStyle(body || document.documentElement).fontSize || "16");
    const maxHeight = messageDiv.classList.contains("expanded")
      ? fontSize * 15
      : (body?.clientHeight || 0);
    messageDiv.classList.toggle("has-overflow", (body?.scrollHeight || 0) > maxHeight);
  });
}

// returns true if this is the initial render of a chat eg. when reloading window, switching chat or catching up after a break
// returns false when already in a rendered chat and adding messages regurarly
function isMassRender() {
  return _massRender;
}

// smooth fade in animation for new chunks when streaming
function smoothRender(element, newContent, delay = 350) {
  // skip on mass render
  if (isMassRender()) {
    element.innerHTML = newContent; 
    return;
  }

  element.dataset.smoothPendingHtml = newContent;

  if (element.dataset.smoothTimeoutId) return;

  const timeoutId = window.setTimeout(() => {
    const pending = element.dataset.smoothPendingHtml || "";
    delete element.dataset.smoothPendingHtml;
    delete element.dataset.smoothTimeoutId;

    const existing = element.querySelector(
      ":scope > div.smooth-render-visible",
    );
    if (existing) {
      existing.classList.remove("smooth-render-visible");
      existing.classList.add("smooth-render-invisible");

      existing.addEventListener("animationend", () => existing.remove(), {
        once: true,
      });
    }

    const nextLayer = document.createElement("div");
    nextLayer.className = "smooth-render-visible";
    nextLayer.innerHTML = pending;
    element.appendChild(nextLayer);

    // Keep container height stable while layers are absolute
    element.style.height = `${nextLayer.scrollHeight}px`;
  }, delay);

  element.dataset.smoothTimeoutId = String(timeoutId);
}
