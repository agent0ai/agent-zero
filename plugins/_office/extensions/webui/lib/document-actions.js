import { showButtonFeedback } from "/components/messages/action-buttons/simple-action-buttons.js";
import { open as openSurface } from "/js/surfaces.js";

const DESKTOP_FORMATS = ["md", "odt", "ods", "odp", "docx", "xlsx", "pptx"];

function basename(path = "") {
  const value = String(path || "").split("?")[0].split("#")[0];
  return value.split("/").filter(Boolean).pop() || "document";
}

function extensionFromPath(path = "") {
  const name = basename(path);
  const index = name.lastIndexOf(".");
  return index > 0 ? name.slice(index + 1).toLowerCase() : "";
}

function parseMaybeJson(value) {
  if (!value) return null;
  if (typeof value === "object") return value;
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed.startsWith("{")) return null;
  try {
    const parsed = JSON.parse(trimmed);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function truthy(value) {
  if (value === true) return true;
  if (value === false || value == null) return false;
  if (typeof value === "number") return value !== 0;
  return ["1", "true", "yes", "y", "on"].includes(String(value).trim().toLowerCase());
}

function firstValue(...values) {
  for (const value of values) {
    if (value != null && String(value).trim() !== "") return value;
  }
  return "";
}

export function parseDocumentResult(content) {
  return parseMaybeJson(content) || {};
}

export function normalizeDocumentMetadata(args = {}, result = {}) {
  const kvps = parseMaybeJson(args?.kvps) || args?.kvps || {};
  const document = result?.document && typeof result.document === "object"
    ? result.document
    : {};
  const path = String(firstValue(
    result.path,
    kvps.path,
    args.path,
    document.path,
  ));
  const title = String(firstValue(
    result.title,
    kvps.title,
    kvps.basename,
    args.title,
    document.basename,
    basename(path),
  ));
  const format = String(firstValue(
    result.format,
    result.extension,
    kvps.format,
    kvps.extension,
    args.format,
    document.extension,
    extensionFromPath(path),
  )).toLowerCase().replace(/^\./, "");

  return {
    action: String(firstValue(result.action, kvps.action, args.action)).toLowerCase(),
    file_id: String(firstValue(result.file_id, kvps.file_id, args.file_id, document.file_id)),
    path,
    title,
    format,
    extension: format,
    size: firstValue(result.size, kvps.size, document.size),
    version: firstValue(result.version, kvps.version, args.version, document.version),
    last_modified: firstValue(result.last_modified, kvps.last_modified, args.last_modified, document.last_modified),
    exists: firstValue(result.exists, kvps.exists, document.exists),
    open_in_canvas: truthy(firstValue(result.open_in_canvas, kvps.open_in_canvas, args.open_in_canvas)),
    open_in_desktop: truthy(firstValue(result.open_in_desktop, kvps.open_in_desktop, args.open_in_desktop)),
  };
}

export function documentFromLog(args = {}, result = {}) {
  return normalizeDocumentMetadata(args, result);
}

export async function openDocumentInDesktop(document = {}) {
  await openSurface("desktop", {
    path: document.path || "",
    file_id: document.file_id || "",
    refresh: true,
    source: "message-action",
  });
}

export async function openDocumentArtifact(document = {}) {
  await openDocumentInDesktop(document);
}

function usesDesktop(doc = {}) {
  const format = String(doc.format || doc.extension || "").toLowerCase();
  return DESKTOP_FORMATS.includes(format);
}

function canvasActionTitle(doc = {}) {
  const format = String(doc.format || doc.extension || "").toLowerCase();
  if (["odt", "docx"].includes(format)) return "Open in canvas with Writer";
  if (["ods", "xlsx"].includes(format)) return "Open in canvas with Calc";
  if (["odp", "pptx"].includes(format)) return "Open in canvas with Impress";
  if (format === "md") return "Open Markdown in canvas";
  return "Open in canvas";
}

function documentIcon(doc = {}) {
  const format = String(doc.format || doc.extension || "").toLowerCase();
  if (["ods", "xlsx"].includes(format)) return "table_chart";
  if (["odp", "pptx"].includes(format)) return "slideshow";
  if (format === "md") return "article";
  return usesDesktop(doc) ? "description" : "draft";
}

function statusLine(doc = {}) {
  const parts = [];
  if (doc.path) parts.push(doc.path);
  if (doc.version) parts.push(`v${doc.version}`);
  return parts.join(" | ");
}

export function buildDocumentFileCard(document = {}) {
  const card = globalThis.document.createElement("span");
  card.className = "document-file-card";
  card.setAttribute("role", "button");
  card.setAttribute("tabindex", "0");
  card.setAttribute("aria-label", canvasActionTitle(document));
  card.setAttribute("title", canvasActionTitle(document));

  const icon = globalThis.document.createElement("span");
  icon.className = "material-symbols-outlined document-file-card-icon";
  icon.textContent = documentIcon(document);
  card.appendChild(icon);

  const meta = globalThis.document.createElement("span");
  meta.className = "document-file-card-meta";

  const name = globalThis.document.createElement("span");
  name.className = "document-file-card-name";
  name.textContent = document.title || basename(document.path);
  meta.appendChild(name);

  const detail = globalThis.document.createElement("span");
  detail.className = "document-file-card-path";
  detail.textContent = statusLine(document) || "Document artifact";
  meta.appendChild(detail);
  card.appendChild(meta);

  if (document.format) {
    const badge = globalThis.document.createElement("span");
    badge.className = "document-file-card-badge";
    badge.textContent = String(document.format).toUpperCase();
    card.appendChild(badge);
  }

  if (document.path || document.file_id) {
    card.addEventListener("click", () => openDocumentArtifact(document));
    card.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      void openDocumentArtifact(document);
    });
  } else {
    card.setAttribute("aria-disabled", "true");
    card.removeAttribute("tabindex");
  }

  return card;
}

export function downloadDocument(doc = {}) {
  const path = String(doc.path || "");
  if (!path) return;
  const link = globalThis.document.createElement("a");
  link.href = `/api/download_work_dir_file?path=${encodeURIComponent(path)}`;
  link.download = String(doc.title || basename(path));
  globalThis.document.body.appendChild(link);
  link.click();
  globalThis.document.body.removeChild(link);
}

export function createDocumentActionButton(icon, label, handler = null, options = {}) {
  const button = globalThis.document.createElement("button");
  button.type = "button";
  button.className = ["action-button", "document-file-action", options.className]
    .filter(Boolean)
    .join(" ");
  button.setAttribute("aria-label", options.ariaLabel || options.title || label);
  button.setAttribute("title", options.title || label);

  if (icon) {
    const iconEl = globalThis.document.createElement("span");
    iconEl.className = "material-symbols-outlined";
    iconEl.textContent = icon;
    button.appendChild(iconEl);
  }

  if (typeof handler === "function") {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const iconEl = button.querySelector(".material-symbols-outlined");
      const originalIcon = iconEl?.textContent || "";
      try {
        await handler();
        if (originalIcon) showButtonFeedback(button, true, originalIcon);
      } catch (err) {
        console.error("Document action failed:", err);
        if (originalIcon) showButtonFeedback(button, false, originalIcon);
      }
    });
  }

  return button;
}

export function buildDocumentFileActionButtons(document = {}) {
  const hasTarget = Boolean(document?.path || document?.file_id);
  const buttons = [];
  if (hasTarget) {
    buttons.push(
      createDocumentActionButton(
        "open_in_new",
        "Open in canvas",
        () => openDocumentArtifact(document),
        {
          className: "document-file-action-primary",
          title: canvasActionTitle(document),
          ariaLabel: canvasActionTitle(document),
        },
      ),
    );
  }
  if (document?.path) {
    buttons.push(
      createDocumentActionButton("download", "Download", () => downloadDocument(document)),
    );
  }
  return buttons;
}
