import { renderSafeMarkdown } from "/js/safe-markdown.js";

const FOOTNOTE_DEF_RE = /^\[\^([^\]]+)\]:\s*(.*)$/;

export function renderEditorPreviewMarkdown(markdown = "", fullMarkdown = markdown) {
  return renderSafeMarkdown(prepareFootnotes(markdown, fullMarkdown), {
    allowDataImages: true,
    allowLatex: true,
    openExternalLinksInNewTab: true,
  });
}

export function buildMarkdownPages(markdown = "", fallbackTitle = "Markdown") {
  const source = String(markdown || "");
  return [{
    index: 0,
    title: fallbackTitle,
    level: 0,
    anchor: slugifyHeading(fallbackTitle),
    start: 0,
    end: source.length,
    markdown: source,
  }];
}

export function slugifyHeading(text = "", used = new Map()) {
  const base = String(text || "")
    .toLowerCase()
    .replace(/<[^>]+>/g, "")
    .replace(/[`*_~[\]()]/g, "")
    .replace(/&[a-z0-9#]+;/gi, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-") || "section";
  const count = used.get(base) || 0;
  used.set(base, count + 1);
  return count ? `${base}-${count + 1}` : base;
}

export function resolveDocumentRelativePath(documentPath = "", target = "") {
  const value = String(target || "").trim();
  if (!value) return "";
  if (value.startsWith("/")) return normalizePath(value);
  const base = parentPath(documentPath);
  return normalizePath(`${base}/${value}`);
}

export function splitHref(href = "") {
  const value = String(href || "").trim();
  const hashIndex = value.indexOf("#");
  if (hashIndex < 0) return { path: value, fragment: "" };
  return {
    path: value.slice(0, hashIndex),
    fragment: decodeURIComponent(value.slice(hashIndex + 1) || ""),
  };
}

export function isExternalHref(href = "") {
  const value = String(href || "").trim();
  return /^[a-zA-Z][a-zA-Z\d+.-]*:/.test(value) || value.startsWith("//");
}

export function isMarkdownPath(path = "") {
  return /\.md(?:own)?$/i.test(String(path || "").split(/[?#]/, 1)[0]);
}

function prepareFootnotes(markdown = "", fullMarkdown = markdown) {
  const definitions = [];
  const body = [];
  for (const line of String(fullMarkdown || "").split("\n")) {
    const match = line.match(FOOTNOTE_DEF_RE);
    if (match) {
      definitions.push({ id: match[1], text: match[2] });
    }
  }
  for (const line of String(markdown || "").split("\n")) {
    if (line.match(FOOTNOTE_DEF_RE)) {
      continue;
    }
    body.push(line);
  }
  if (!definitions.length) return markdown;

  const counts = new Map();
  let prepared = body.join("\n").replace(/\[\^([^\]]+)\]/g, (_all, id) => {
    const number = definitions.findIndex((item) => item.id === id) + 1;
    if (number <= 0) return `[^${id}]`;
    const count = (counts.get(id) || 0) + 1;
    counts.set(id, count);
    const safeId = footnoteId(id);
    return `<sup class="editor-footnote-ref"><a id="fnref-${safeId}-${count}" href="#fn-${safeId}">${number}</a></sup>`;
  });

  prepared += "\n\n<section class=\"editor-footnotes\" aria-label=\"Footnotes\">\n<ol>\n";
  for (const definition of definitions) {
    const safeId = footnoteId(definition.id);
    prepared += `<li id="fn-${safeId}">${escapeHtml(definition.text)} <a class="editor-footnote-backref" href="#fnref-${safeId}-1">Back</a></li>\n`;
  }
  prepared += "</ol>\n</section>";
  return prepared;
}

function footnoteId(id = "") {
  return String(id || "")
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "") || "note";
}

function parentPath(path = "") {
  const normalized = String(path || "").split(/[?#]/, 1)[0].replace(/\/+$/, "");
  const index = normalized.lastIndexOf("/");
  if (index <= 0) return "/";
  return normalized.slice(0, index);
}

function normalizePath(path = "") {
  const absolute = String(path || "").startsWith("/");
  const parts = [];
  for (const part of String(path || "").split("/")) {
    if (!part || part === ".") continue;
    if (part === "..") {
      parts.pop();
      continue;
    }
    parts.push(part);
  }
  return `${absolute ? "/" : ""}${parts.join("/")}`;
}

function escapeHtml(value = "") {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
