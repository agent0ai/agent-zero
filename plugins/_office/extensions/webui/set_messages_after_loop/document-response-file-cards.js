import {
  buildDocumentFileActionButtons,
  buildDocumentFileCard,
  documentFromLog,
  parseDocumentResult,
} from "../lib/document-actions.js";

const PENDING_TTL_MS = 2 * 60 * 1000;
const RESPONSE_CARD_ACTIONS = new Set([
  "create",
  "edit",
  "export",
  "open",
  "patch",
  "restore_version",
  "update",
]);

let pendingContextId = "";
let pendingDocuments = [];

export default async function injectDocumentCardsIntoFinalResponses(context) {
  if (!context?.results?.length) return;

  const contextId = currentContextId();
  if (pendingContextId !== contextId || context.historyEmpty) {
    pendingContextId = contextId;
    pendingDocuments = [];
  }
  prunePendingDocuments();

  for (const entry of context.results) {
    if (String(entry.args?.type || "") === "user") {
      pendingDocuments = [];
      continue;
    }

    const documentEntry = documentEntryFromToolResult(entry.args);
    if (documentEntry) {
      addPendingDocument(documentEntry);
      continue;
    }

    if (!isPrimaryResponse(entry.args, entry.result)) continue;
    if (!pendingDocuments.length) {
      refreshResponseFileActions(entry.result.element);
      continue;
    }

    injectResponseFileCards(entry.result.element, pendingDocuments);
    pendingDocuments = [];
  }
}

function documentEntryFromToolResult(args = {}) {
  if (String(args?.type || "") !== "tool") return null;
  const result = parseDocumentResult(String(args.content ?? ""));
  const document = documentFromLog(args, result);
  if (!document.path && !document.file_id) return null;
  if (toolName(args, result) !== "document_artifact") return null;
  if (!isResponseCardAction(document.action)) return null;
  return {
    document,
    log: args,
  };
}

function toolName(args = {}, result = {}) {
  return String(
    args?._tool_name
      || args?.kvps?._tool_name
      || result?._tool_name
      || result?.tool_name
      || "",
  ).trim();
}

function currentContextId() {
  return String(globalThis.getContext?.() || "");
}

function addPendingDocument(entry) {
  const key = documentIdentityKey(entry.document);
  const duplicateIndex = pendingDocuments.findIndex((item) => documentIdentityKey(item.document) === key);
  if (duplicateIndex >= 0) pendingDocuments.splice(duplicateIndex, 1);
  pendingDocuments.push({
    ...entry,
    createdAt: Date.now(),
  });
}

function prunePendingDocuments(now = Date.now()) {
  pendingDocuments = pendingDocuments.filter(
    (entry) => now - (entry.createdAt || now) <= PENDING_TTL_MS,
  );
}

function isPrimaryResponse(args = {}, result = {}) {
  if (String(args?.type || "") !== "response") return false;
  if (Number(args?.agentno || 0) > 0) return false;
  return Boolean(result?.element?.querySelector?.(".message-agent-response"));
}

function injectResponseFileCards(responseElement, entries) {
  const message = responseElement?.querySelector?.(".message-agent-response");
  const body = message?.querySelector?.(".message-body");
  if (!message || !body) return;

  const uniqueEntries = uniqueDocumentEntries(entries);
  if (!uniqueEntries.length) return;

  let wrapper = body.querySelector(":scope > .document-response-file-cards");
  if (!wrapper) {
    wrapper = document.createElement("div");
    wrapper.className = "document-response-file-cards";
    const content = body.querySelector(":scope > .msg-content");
    if (content) content.after(wrapper);
    else body.appendChild(wrapper);
  }
  wrapper.dataset.documents = JSON.stringify(uniqueEntries.map(({ document }) => document));
  wrapper.replaceChildren(...uniqueEntries.map(({ document }) => buildDocumentFileCard(document)));

  injectResponseActionButtons(message, uniqueEntries);
}

function refreshResponseFileActions(responseElement) {
  const message = responseElement?.querySelector?.(".message-agent-response");
  if (!message) return;

  const wrapper = message.querySelector(":scope .document-response-file-cards");
  const documents = parseStoredDocuments(wrapper);
  if (!documents.length) return;

  injectResponseActionButtons(
    message,
    documents.map((document) => ({ document })),
  );
}

function injectResponseActionButtons(message, entries) {
  const bar = message.querySelector(":scope > .step-action-buttons");
  if (!bar) return;

  bar.querySelectorAll(".document-response-file-action").forEach((button) => button.remove());

  const buttons = [];
  for (const entry of entries) {
    for (const button of buildDocumentFileActionButtons(entry.document)) {
      button.classList.add("document-response-file-action");
      buttons.push(button);
    }
  }

  const firstAction = Array.from(bar.children).find((child) => !child.classList.contains("expand-btn"));
  for (const button of buttons) {
    bar.insertBefore(button, firstAction || null);
  }
}

function uniqueDocumentEntries(entries = []) {
  const uniqueByDocument = new Map();
  for (const entry of entries) {
    const key = documentIdentityKey(entry.document);
    if (uniqueByDocument.has(key)) uniqueByDocument.delete(key);
    uniqueByDocument.set(key, entry);
  }
  return Array.from(uniqueByDocument.values());
}

function parseStoredDocuments(wrapper) {
  const raw = wrapper?.dataset?.documents;
  if (!raw) return [];
  try {
    const documents = JSON.parse(raw);
    return Array.isArray(documents) ? documents.filter(Boolean) : [];
  } catch {
    return [];
  }
}

function documentKey(document = {}) {
  return [
    document.file_id || "",
    document.path || "",
    document.version || "",
  ].join(":");
}

function documentIdentityKey(document = {}) {
  const path = String(document.path || "").trim();
  if (path) return `path:${path}`;
  const fileId = String(document.file_id || "").trim();
  if (fileId) return `file:${fileId}`;
  return documentKey(document);
}

function isResponseCardAction(action = "") {
  return RESPONSE_CARD_ACTIONS.has(String(action || "").trim().toLowerCase().replace("-", "_"));
}
