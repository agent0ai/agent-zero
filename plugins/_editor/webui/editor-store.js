import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getNamespacedClient } from "/js/websocket.js";
import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";
import {
  openLatest as openLatestSurface,
  placeSurfaceModalHeaderAction,
  registerUrlHandler,
  setupFloatingSurfaceModalChrome,
} from "/js/surfaces.js";
import {
  buildMarkdownPages,
  isExternalHref,
  isMarkdownPath,
  renderEditorPreviewMarkdown,
  resolveDocumentRelativePath,
  slugifyHeading,
  splitHref,
} from "/plugins/_editor/webui/editor-preview.js";

const editorSocket = getNamespacedClient("/ws");
editorSocket.addHandlers(["ws_webui"]);

const SAVE_MESSAGE_MS = 1800;
const INPUT_PUSH_DELAY_MS = 650;
const MAX_HISTORY = 80;
const SOURCE_MODE = "source";
const PREVIEW_MODE = "preview";
const EDITOR_TEXT_EXTENSIONS = new Set(["md", "txt"]);

function currentContextId() {
  try {
    return globalThis.getContext?.() || "";
  } catch {
    return "";
  }
}

function basename(path = "") {
  const value = String(path || "").split("?")[0].split("#")[0];
  return value.split("/").filter(Boolean).pop() || "Untitled";
}

function extensionOf(path = "") {
  const name = basename(path).toLowerCase();
  const index = name.lastIndexOf(".");
  return index >= 0 ? name.slice(index + 1) : "";
}

function parentPath(path = "") {
  const normalized = String(path || "").split("?")[0].split("#")[0].replace(/\/+$/, "");
  const index = normalized.lastIndexOf("/");
  if (index <= 0) return "/";
  return normalized.slice(0, index);
}

function textDocumentFilename(path = "", fallback = "Untitled.md") {
  const name = basename(path || fallback || "Untitled.md");
  const ext = extensionOf(name);
  if (EDITOR_TEXT_EXTENSIONS.has(ext)) return name;
  return `${name.replace(/\.+$/, "") || "Untitled"}.md`;
}

function textDocumentDefaultExtension(path = "") {
  const ext = extensionOf(path);
  return EDITOR_TEXT_EXTENSIONS.has(ext) ? ext : "md";
}

function editorIntent(url = "") {
  const raw = String(url || "").trim();
  if (!raw) return null;
  try {
    const parsed = new URL(raw);
    if (parsed.protocol !== "a0-editor:") return null;
    if (parsed.hostname === "open") {
      return { path: parsed.searchParams.get("path") || "" };
    }
    return null;
  } catch {
    return null;
  }
}

function uniqueTabId(session = {}) {
  return String(session.file_id || session.session_id || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`);
}

function editorContainsFocus(element) {
  const active = document.activeElement;
  return Boolean(element && active && (element === active || element.contains(active)));
}

function placeCaretAtEnd(element) {
  if (!element) return;
  if (element.tagName === "TEXTAREA" || element.tagName === "INPUT") {
    const length = element.value?.length || 0;
    element.selectionStart = length;
    element.selectionEnd = length;
    return;
  }
  const selection = globalThis.getSelection?.();
  const range = document.createRange?.();
  if (!selection || !range) return;
  range.selectNodeContents(element);
  range.collapse(false);
  selection.removeAllRanges();
  selection.addRange(range);
}

function normalizeTextDocument(doc = {}) {
  const path = doc.path || "";
  const extension = String(doc.extension || extensionOf(path)).toLowerCase();
  return {
    ...doc,
    extension,
    title: doc.title || doc.basename || basename(path),
    basename: doc.basename || basename(path),
    path,
  };
}

function normalizeSession(payload = {}) {
  const document = normalizeTextDocument(payload.document || payload);
  return {
    ...payload,
    document,
    extension: String(payload.extension || document.extension || "").toLowerCase(),
    file_id: payload.file_id || document.file_id || "",
    path: document.path || payload.path || "",
    title: payload.title || document.title || document.basename || basename(document.path),
    tab_id: uniqueTabId(payload),
    text: String(payload.text || ""),
    dirty: Boolean(payload.dirty),
    active: Boolean(payload.active),
  };
}

function documentLabel(document = {}) {
  return document.title || document.basename || basename(document.path);
}

function escapeRegExp(value = "") {
  return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function textNodesUnder(root, skipSelector = "") {
  const nodes = [];
  if (!root) return nodes;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue) return NodeFilter.FILTER_REJECT;
      if (skipSelector && node.parentElement?.closest(skipSelector)) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  while (walker.nextNode()) nodes.push(walker.currentNode);
  return nodes;
}

function aceModeForLanguage(language = "") {
  const value = String(language || "").toLowerCase();
  const aliases = {
    bash: "sh",
    shell: "sh",
    zsh: "sh",
    py: "python",
    js: "javascript",
    jsx: "javascript",
    ts: "typescript",
    md: "markdown",
    yml: "yaml",
  };
  return aliases[value] || value || "text";
}

function taskLineIndexes(markdown = "") {
  const indexes = [];
  String(markdown || "").split("\n").forEach((line, index) => {
    if (/^\s*(?:[-*+]|\d+[.)])\s+\[[ xX]\](?:\s+|$)/.test(line)) indexes.push(index);
  });
  return indexes;
}

async function callEditor(action, payload = {}) {
  const explicitContextId = String(payload.ctxid || payload.context_id || "").trim();
  return await callJsonApi("/plugins/_editor/editor_session", {
    action,
    ...payload,
    ctxid: explicitContextId || currentContextId(),
  });
}

async function requestEditor(eventType, payload = {}, timeoutMs = 5000) {
  const explicitContextId = String(payload.ctxid || payload.context_id || "").trim();
  const response = await editorSocket.request(eventType, {
    ...payload,
    ctxid: explicitContextId || currentContextId(),
  }, { timeoutMs });
  const results = Array.isArray(response?.results) ? response.results : [];
  const first = results.find((item) => item?.ok === true && isEditorSocketData(item?.data))
    || results.find((item) => item?.ok === true);
  if (!first) {
    const error = results.find((item) => item?.error)?.error;
    throw new Error(error?.error || error?.code || `${eventType} failed`);
  }
  if (first.data?.editor_error) {
    const error = first.data.editor_error;
    throw new Error(error.error || error.code || `${eventType} failed`);
  }
  return first.data || {};
}

function isEditorSocketData(data) {
  if (!data || typeof data !== "object") return false;
  return (
    Object.prototype.hasOwnProperty.call(data, "editor_error")
    || Object.prototype.hasOwnProperty.call(data, "ok")
    || Object.prototype.hasOwnProperty.call(data, "session_id")
    || Object.prototype.hasOwnProperty.call(data, "document")
  );
}

const model = {
  status: null,
  tabs: [],
  activeTabId: "",
  session: null,
  loading: false,
  saving: false,
  dirty: false,
  error: "",
  message: "",
  pendingClose: null,
  viewMode: SOURCE_MODE,
  searchOpen: false,
  searchQuery: "",
  searchMatches: [],
  searchIndex: -1,
  activePageIndex: 0,
  previewEditing: false,
  previewEditDirty: false,
  previewEditText: "",
  previewEditPageIndex: -1,
  aceUnavailable: false,
  editorText: "",
  sourceEditor: null,
  _root: null,
  _mode: "modal",
  _initialized: false,
  _saveMessageTimer: null,
  _inputTimer: null,
  _history: [],
  _historyIndex: -1,
  _historyPushedAt: 0,
  _pendingFocus: false,
  _pendingFocusEnd: true,
  _focusAttempts: 0,
  _headerCleanup: null,
  _settingSourceEditorValue: false,
  _sourceEditorChangeHandler: null,
  _previewEnhanceTimer: null,
  _staticHighlightPromise: null,
  _pendingPreviewFragment: "",

  async init() {
    if (this._initialized) return;
    this._initialized = true;
    await this.refresh();
  },

  async onMount(element = null, options = {}) {
    await this.init();
    if (element && element !== this._root) {
      if (this.sourceEditor && !element.contains?.(this.sourceEditor.container)) {
        this.destroySourceEditor();
      }
      this._root = element;
    }
    this._mode = options?.mode === "canvas" ? "canvas" : "modal";
    if (this._mode === "modal") {
      this.setupMarkdownModal(element);
    }
    this.scheduleSourceEditorInit();
  },

  async onOpen(payload = {}) {
    await this.init();
    await this.refresh();
    if (payload?.path || payload?.file_id) {
      const contextId = String(payload.ctxid || payload.context_id || "").trim();
      await this.openSession({
        path: payload.path || "",
        file_id: payload.file_id || "",
        ctxid: contextId,
        context_id: contextId,
        refresh: payload.refresh === true,
        source: payload.source || "",
      });
      return;
    }
  },

  beforeHostHidden() {
    this.flushInput();
  },

  cleanup() {
    this.flushInput();
    this.destroySourceEditor();
    if (this._previewEnhanceTimer) globalThis.clearTimeout(this._previewEnhanceTimer);
    this._previewEnhanceTimer = null;
    this._headerCleanup?.();
    this._headerCleanup = null;
    if (this._mode === "modal") this._root = null;
  },

  beginSurfaceHandoff() {
    this.flushInput();
  },

  async refresh() {
    try {
      const status = await callEditor("status");
      this.status = status || {};
      this.error = "";
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    }
  },

  isSourceMode() {
    return this.viewMode === SOURCE_MODE;
  },

  isPreviewMode() {
    return this.viewMode === PREVIEW_MODE;
  },

  async setViewMode(mode) {
    const next = mode === PREVIEW_MODE && this.isTextDocument() ? PREVIEW_MODE : SOURCE_MODE;
    if (this.viewMode === next) return;
    this.applyPreviewEdit({ silent: true });
    this.syncEditorText();
    this.viewMode = next;
    this.cancelPendingClose();
    if (next === SOURCE_MODE) {
      this.setSourceEditorText(this.editorText);
      this.scheduleSourceEditorInit();
      this.refreshSourceEditorLayout();
      this.queueRender({ focus: Boolean(this.session), end: false });
      return;
    }
    this.clampActivePage();
    this.schedulePreviewEnhance();
  },

  async toggleViewMode() {
    if (!this.isTextDocument()) return;
    await this.setViewMode(this.isPreviewMode() ? SOURCE_MODE : PREVIEW_MODE);
  },

  viewModeIcon() {
    return this.isPreviewMode() ? "code" : "article";
  },

  viewModeTitle() {
    return this.isPreviewMode() ? "Source edit" : "Preview";
  },

  pages() {
    if (!this.isTextDocument()) return [];
    return buildMarkdownPages(this.editorText, this.tabTitle(this.session || {}));
  },

  currentPage() {
    const pages = this.pages();
    const index = Math.max(0, Math.min(this.activePageIndex, pages.length - 1));
    return pages[index] || pages[0] || { title: this.tabTitle(this.session || {}), markdown: "" };
  },

  pageTitle() {
    return this.currentPage().title || this.tabTitle(this.session || {});
  },

  previewHtml() {
    if (!this.isTextDocument()) return "";
    return renderEditorPreviewMarkdown(this.currentPage().markdown || "", this.editorText);
  },

  startPreviewEdit() {
    if (!this.session || !this.isTextDocument() || !this.isPreviewMode()) return;
    const page = this.currentPage();
    this.previewEditing = true;
    this.previewEditDirty = false;
    this.previewEditPageIndex = this.activePageIndex;
    this.previewEditText = page.markdown || "";
    globalThis.requestAnimationFrame?.(() => {
      const editor = this._root?.querySelector?.("[data-editor-preview-source]");
      editor?.focus?.({ preventScroll: true });
    });
  },

  onPreviewEditInput() {
    if (this.previewEditing) this.previewEditDirty = true;
  },

  cancelPreviewEdit() {
    this.previewEditing = false;
    this.previewEditDirty = false;
    this.previewEditText = "";
    this.previewEditPageIndex = -1;
    this.schedulePreviewEnhance();
  },

  applyPreviewEdit(options = {}) {
    if (!this.previewEditing) return false;
    if (!this.previewEditDirty && options.force !== true) {
      this.cancelPreviewEdit();
      return false;
    }
    const pages = this.pages();
    const index = Math.max(0, Math.min(
      this.previewEditPageIndex >= 0 ? this.previewEditPageIndex : this.activePageIndex,
      pages.length - 1,
    ));
    const page = pages[index];
    if (!page) {
      this.cancelPreviewEdit();
      return false;
    }

    let replacement = String(this.previewEditText || "");
    this.previewEditing = false;
    this.previewEditDirty = false;
    this.previewEditText = "";
    this.previewEditPageIndex = -1;

    return this.replacePageMarkdown(page, replacement, {
      message: "Document updated",
      silent: options.silent,
    });
  },

  replacePageMarkdown(page = null, markdown = "", options = {}) {
    if (!page) return false;
    const source = String(this.editorText || "");
    const start = Math.max(0, Number(page.start || 0));
    const end = Math.max(start, Number(page.end ?? source.length));
    const before = source.slice(0, start);
    const after = source.slice(end);
    let replacement = String(markdown || "");
    if (replacement && after && !replacement.endsWith("\n")) replacement += "\n";
    const next = before + replacement + after;
    if (next === source) {
      this.schedulePreviewEnhance();
      return false;
    }

    this.editorText = next;
    this.setSourceEditorText(next);
    if (this.session) {
      this.session.text = next;
      this.session.dirty = true;
    }
    this.dirty = true;
    this.pushHistory(next);
    this.scheduleInputPush();
    this.clampActivePage();
    this.schedulePreviewEnhance();
    if (!options.silent && options.message) this.setMessage(options.message);
    return true;
  },

  togglePreviewTask(taskIndex, checked) {
    if (!this.session || !this.isTextDocument() || !this.isPreviewMode() || this.previewEditing) return false;
    const page = this.currentPage();
    const lines = String(page.markdown || "").split("\n");
    const indexes = taskLineIndexes(page.markdown || "");
    const lineIndex = indexes[Number(taskIndex)];
    if (lineIndex == null || !lines[lineIndex]) return false;
    const nextLine = lines[lineIndex].replace(
      /^(\s*(?:[-*+]|\d+[.)])\s+\[)[ xX](\](?:\s+|$))/,
      `$1${checked ? "x" : " "}$2`,
    );
    if (nextLine === lines[lineIndex]) return false;
    lines[lineIndex] = nextLine;
    return this.replacePageMarkdown(page, lines.join("\n"));
  },

  clampActivePage() {
    const pages = this.pages();
    this.activePageIndex = Math.max(0, Math.min(this.activePageIndex, Math.max(0, pages.length - 1)));
  },

  schedulePreviewEnhance() {
    if (!this.isTextDocument() || !this.isPreviewMode()) return;
    if (this._previewEnhanceTimer) globalThis.clearTimeout(this._previewEnhanceTimer);
    this._previewEnhanceTimer = globalThis.setTimeout(() => {
      this._previewEnhanceTimer = null;
      this.enhancePreview();
    }, 0);
  },

  enhancePreview() {
    const root = this._root?.querySelector?.("[data-editor-preview]");
    if (!root) return;
    this.addHeadingIds(root);
    this.enhanceTables(root);
    this.enhanceTaskLists(root);
    this.enhanceImages(root);
    this.enhanceLinks(root);
    this.enhanceCodeBlocks(root);
    this.renderMath(root);
    this.applySearchHighlights(root);
    this.scrollPendingFragment(root);
  },

  addHeadingIds(root) {
    const used = new Map();
    root.querySelectorAll("h1,h2,h3,h4,h5,h6").forEach((heading) => {
      if (!heading.id) heading.id = slugifyHeading(heading.textContent || "", used);
    });
  },

  enhanceTables(root) {
    root.querySelectorAll("table").forEach((table) => {
      if (table.parentElement?.classList.contains("editor-table-wrap")) return;
      const wrapper = document.createElement("div");
      wrapper.className = "editor-table-wrap";
      table.parentNode?.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    });
  },

  enhanceTaskLists(root) {
    root.querySelectorAll('input[type="checkbox"]').forEach((checkbox, index) => {
      if (checkbox.dataset.editorTaskEnhanced === "true") return;
      checkbox.dataset.editorTaskEnhanced = "true";
      checkbox.dataset.editorTaskIndex = String(index);
      checkbox.disabled = false;
      checkbox.removeAttribute("disabled");
      checkbox.addEventListener("change", (event) => {
        const target = event.currentTarget;
        this.togglePreviewTask(Number(target?.dataset?.editorTaskIndex || 0), Boolean(target?.checked));
      });
    });
  },

  enhanceImages(root) {
    const docPath = this.session?.path || this.session?.document?.path || "";
    root.querySelectorAll("img[src]").forEach((image) => {
      const src = image.getAttribute("src") || "";
      if (!src || isExternalHref(src) || src.startsWith("data:") || src.startsWith("/api/image_get")) return;
      const resolved = resolveDocumentRelativePath(docPath, src);
      image.setAttribute("src", `/api/image_get?path=${encodeURIComponent(resolved)}`);
      image.setAttribute("loading", "lazy");
    });
  },

  enhanceLinks(root) {
    const docPath = this.session?.path || this.session?.document?.path || "";
    root.querySelectorAll("a[href]").forEach((anchor) => {
      const href = anchor.getAttribute("href") || "";
      if (!href || isExternalHref(href)) return;
      const { path, fragment } = splitHref(href);
      if (!path && fragment) {
        anchor.dataset.editorFragment = fragment;
        return;
      }
      if (!isMarkdownPath(path)) return;
      anchor.dataset.editorMarkdownPath = resolveDocumentRelativePath(docPath, path);
      anchor.dataset.editorFragment = fragment;
    });
  },

  async enhanceCodeBlocks(root) {
    root.querySelectorAll("pre > code").forEach((code) => {
      const pre = code.parentElement;
      if (!pre || pre.parentElement?.classList.contains("editor-code-block")) return;
      const wrapper = document.createElement("div");
      wrapper.className = "editor-code-block";
      const header = document.createElement("div");
      header.className = "editor-code-header";
      const language = this.codeLanguage(code);
      const label = document.createElement("span");
      label.className = "editor-code-language";
      label.textContent = language || "text";
      const button = document.createElement("button");
      button.type = "button";
      button.className = "editor-code-copy";
      button.textContent = "Copy";
      button.addEventListener("click", async () => {
        await navigator.clipboard?.writeText(code.textContent || "");
        button.textContent = "Copied";
        globalThis.setTimeout(() => { button.textContent = "Copy"; }, 1200);
      });
      header.append(label, button);
      pre.parentNode?.insertBefore(wrapper, pre);
      wrapper.append(header, pre);
      this.highlightCodeBlock(code, language);
    });
  },

  codeLanguage(code) {
    for (const className of code.classList || []) {
      if (className.startsWith("language-")) return className.slice("language-".length);
      if (className.startsWith("lang-")) return className.slice("lang-".length);
    }
    return "";
  },

  async highlightCodeBlock(code, language) {
    if (!language || !globalThis.ace?.require) return;
    const source = code.textContent || "";
    try {
      const highlighter = await this.loadAceStaticHighlighter();
      const darkMode = globalThis.localStorage?.getItem("darkMode");
      const theme = darkMode !== "false" ? "ace/theme/github_dark" : "ace/theme/github";
      const mode = `ace/mode/${aceModeForLanguage(language)}`;
      highlighter.render(source, mode, theme, 1, true, (result) => {
        code.innerHTML = result.html;
        code.classList.add("is-highlighted");
      });
    } catch {
      // Fenced code still renders as preformatted text if highlighting is unavailable.
    }
  },

  loadAceStaticHighlighter() {
    if (this._staticHighlightPromise) return this._staticHighlightPromise;
    this._staticHighlightPromise = new Promise((resolve, reject) => {
      let existing = null;
      try {
        existing = globalThis.ace?.require?.("ace/ext/static_highlight");
      } catch {
        existing = null;
      }
      if (existing?.render) {
        resolve(existing);
        return;
      }
      const script = document.createElement("script");
      script.src = "/vendor/ace-min/ext-static_highlight.js";
      script.onload = () => {
        const loaded = globalThis.ace?.require?.("ace/ext/static_highlight");
        loaded?.render ? resolve(loaded) : reject(new Error("ACE highlighter unavailable"));
      };
      script.onerror = () => reject(new Error("ACE highlighter failed to load"));
      document.head.appendChild(script);
    });
    return this._staticHighlightPromise;
  },

  renderMath(root) {
    if (!globalThis.katex?.render) return;
    for (const node of textNodesUnder(root, "code,pre,.katex,.editor-code-block")) {
      this.replaceMathInTextNode(node);
    }
  },

  replaceMathInTextNode(node) {
    const text = node.nodeValue || "";
    const pattern = /(\$\$[^$]+\$\$|\$[^$\n]+\$)/g;
    if (!pattern.test(text)) return;
    pattern.lastIndex = 0;
    const fragment = document.createDocumentFragment();
    let lastIndex = 0;
    let match;
    while ((match = pattern.exec(text))) {
      if (match.index > lastIndex) fragment.append(document.createTextNode(text.slice(lastIndex, match.index)));
      const raw = match[0];
      const displayMode = raw.startsWith("$$");
      const expression = raw.slice(displayMode ? 2 : 1, displayMode ? -2 : -1);
      const span = document.createElement(displayMode ? "div" : "span");
      span.className = displayMode ? "editor-math-display" : "editor-math-inline";
      try {
        globalThis.katex.render(expression, span, { throwOnError: false, displayMode });
      } catch {
        span.textContent = raw;
      }
      fragment.append(span);
      lastIndex = match.index + raw.length;
    }
    if (lastIndex < text.length) fragment.append(document.createTextNode(text.slice(lastIndex)));
    node.parentNode?.replaceChild(fragment, node);
  },

  openSearch() {
    if (!this.isTextDocument()) return;
    if (!this.isPreviewMode()) {
      this.setViewMode(PREVIEW_MODE);
    }
    this.searchOpen = true;
    this.runSearch();
    globalThis.requestAnimationFrame?.(() => {
      this._root?.querySelector?.("[data-editor-search]")?.focus?.();
    });
  },

  closeSearch() {
    this.searchOpen = false;
    this.searchQuery = "";
    this.searchMatches = [];
    this.searchIndex = -1;
    this.schedulePreviewEnhance();
  },

  searchCountLabel() {
    if (!this.searchQuery) return "";
    if (!this.searchMatches.length) return "0 of 0";
    return `${this.searchIndex + 1} of ${this.searchMatches.length}`;
  },

  runSearch() {
    const query = String(this.searchQuery || "");
    if (!query) {
      this.searchMatches = [];
      this.searchIndex = -1;
      this.schedulePreviewEnhance();
      return;
    }
    const lower = query.toLowerCase();
    const matches = [];
    for (const page of this.pages()) {
      const text = this.renderedTextForPage(page);
      let index = 0;
      let occurrence = 0;
      while ((index = text.toLowerCase().indexOf(lower, index)) >= 0) {
        matches.push({ pageIndex: page.index, occurrence, offset: index });
        occurrence += 1;
        index += Math.max(1, lower.length);
      }
    }
    this.searchMatches = matches;
    this.searchIndex = matches.length ? 0 : -1;
    this.goToCurrentSearchMatch();
  },

  nextSearchMatch() {
    if (!this.searchMatches.length) return;
    this.searchIndex = (this.searchIndex + 1) % this.searchMatches.length;
    this.goToCurrentSearchMatch();
  },

  previousSearchMatch() {
    if (!this.searchMatches.length) return;
    this.searchIndex = (this.searchIndex - 1 + this.searchMatches.length) % this.searchMatches.length;
    this.goToCurrentSearchMatch();
  },

  goToCurrentSearchMatch() {
    const match = this.searchMatches[this.searchIndex];
    if (!match) {
      this.schedulePreviewEnhance();
      return;
    }
    this.activePageIndex = match.pageIndex;
    this.schedulePreviewEnhance();
  },

  renderedTextForPage(page) {
    const html = renderEditorPreviewMarkdown(page.markdown || "", this.editorText);
    const doc = new DOMParser().parseFromString(html, "text/html");
    return doc.body.textContent || "";
  },

  applySearchHighlights(root) {
    root.querySelectorAll("mark.editor-search-mark").forEach((mark) => {
      mark.replaceWith(document.createTextNode(mark.textContent || ""));
    });
    const query = String(this.searchQuery || "");
    if (!query || !this.searchMatches.length) return;
    const regex = new RegExp(escapeRegExp(query), "gi");
    const current = this.searchMatches[this.searchIndex];
    let occurrence = 0;
    for (const node of textNodesUnder(root, "script,style")) {
      const text = node.nodeValue || "";
      if (!regex.test(text)) continue;
      regex.lastIndex = 0;
      const fragment = document.createDocumentFragment();
      let lastIndex = 0;
      let match;
      while ((match = regex.exec(text))) {
        if (match.index > lastIndex) fragment.append(document.createTextNode(text.slice(lastIndex, match.index)));
        const mark = document.createElement("mark");
        mark.className = "editor-search-mark";
        if (current?.pageIndex === this.activePageIndex && current.occurrence === occurrence) {
          mark.classList.add("is-current");
        }
        mark.textContent = match[0];
        fragment.append(mark);
        occurrence += 1;
        lastIndex = match.index + match[0].length;
      }
      if (lastIndex < text.length) fragment.append(document.createTextNode(text.slice(lastIndex)));
      node.parentNode?.replaceChild(fragment, node);
    }
    root.querySelector("mark.editor-search-mark.is-current")?.scrollIntoView?.({ block: "center" });
  },

  async handlePreviewClick(event) {
    const anchor = event.target?.closest?.("a[href]");
    if (!anchor) return;
    const markdownPath = anchor.dataset.editorMarkdownPath || "";
    const fragment = anchor.dataset.editorFragment || "";
    if (!markdownPath && fragment) {
      event.preventDefault();
      this.navigateToFragment(fragment);
      return;
    }
    if (!markdownPath) return;
    event.preventDefault();
    this._pendingPreviewFragment = fragment;
    const opened = await this.openSession({ path: markdownPath, refresh: true, source: "editor-preview-link" });
    if (!opened) return;
    if (this.isPreviewMode() && fragment) {
      this.navigateToFragment(fragment);
    }
  },

  navigateToFragment(fragment = "") {
    const target = String(fragment || "").replace(/^#/, "");
    if (!target) return;
    const pages = this.pages();
    const normalized = target.toLowerCase();
    for (const page of pages) {
      const doc = new DOMParser().parseFromString(renderEditorPreviewMarkdown(page.markdown || "", this.editorText), "text/html");
      const used = new Map();
      const headings = [...doc.body.querySelectorAll("h1,h2,h3,h4,h5,h6")];
      if (headings.some((heading) => (heading.id || slugifyHeading(heading.textContent || "", used)) === normalized)) {
        this.activePageIndex = page.index;
        this._pendingPreviewFragment = target;
        this.schedulePreviewEnhance();
        return;
      }
    }
    this._pendingPreviewFragment = target;
    this.schedulePreviewEnhance();
  },

  scrollPendingFragment(root) {
    const fragment = this._pendingPreviewFragment;
    if (!fragment) return;
    const target = root.querySelector(`#${CSS.escape(fragment)}`);
    if (target) {
      target.scrollIntoView({ block: "start" });
      this._pendingPreviewFragment = "";
    }
  },

  handleEditorKeydown(event) {
    if (!(event.metaKey || event.ctrlKey) || !this.isTextDocument()) return;
    const key = event.key.toLowerCase();
    const historyAction = key === "y" || (key === "z" && event.shiftKey) ? "redo" : key === "z" ? "undo" : "";
    const nativeEditing = event.target?.matches?.("input, textarea, [contenteditable='true']")
      && !event.target.closest?.("[data-editor-ace], [data-editor-source]");
    if (nativeEditing) return;
    if (historyAction && !this.previewEditing) {
      event.preventDefault();
      event.stopPropagation();
      this[historyAction]();
      return;
    }
    if (key === "f") {
      event.preventDefault();
      this.openSearch();
    }
  },

  async create(kind = "document", format = "") {
    const requested = String(format || "md").toLowerCase().replace(/^\./, "");
    const fmt = EDITOR_TEXT_EXTENSIONS.has(requested) ? requested : "md";
    const title = this.defaultTitle(kind, fmt);
    return await this.openSession({
      action: "create",
      kind: "document",
      format: fmt,
      title,
    });
  },

  async openFileBrowser() {
    let workdirPath = "/a0/usr/workdir";
    try {
      const home = await callEditor("home");
      if (home?.path) {
        workdirPath = home.path;
      } else {
        const response = await callJsonApi("settings_get", null);
        workdirPath = response?.settings?.workdir_path || workdirPath;
      }
    } catch {
      try {
        const response = await callJsonApi("settings_get", null);
        workdirPath = response?.settings?.workdir_path || workdirPath;
      } catch {
        // The file browser can still open with the static fallback.
      }
    }
    await fileBrowserStore.openTextPicker(workdirPath, async ({ selectedFiles = [] } = {}) => {
      const files = selectedFiles.filter((file) => file?.path);
      if (!files.length) return false;
      for (const file of files) {
        const session = await this.openPath(fileBrowserStore.normalizePath(file.path), { source: "file-browser", refresh: true });
        if (!session || session.ok === false) {
          throw new Error(this.error || `Could not open ${file.name || file.path}`);
        }
      }
      return true;
    });
  },

  async openPath(path, options = {}) {
    return await this.openSession({
      path: String(path || ""),
      source: options?.source || "",
      refresh: options?.refresh === true,
    });
  },

  async openSession(payload = {}) {
    this.loading = true;
    this.error = "";
    try {
      const response = await callEditor(payload.action || "open", payload);
      if (response?.ok === false) {
        this.error = response.error || "Text document could not be opened.";
        return null;
      }
      if (response?.requires_desktop) {
        const document = normalizeTextDocument(response.document || response);
        this.setMessage(`${documentLabel(document)} uses the Desktop surface.`);
        await this.refresh();
        return response;
      }
      const session = normalizeSession(response);
      this.installSession(session);
      await this.refresh();
      return session;
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      return null;
    } finally {
      this.loading = false;
    }
  },

  installSession(session) {
    const existingIndex = this.tabs.findIndex((tab) => (
      (session.file_id && tab.file_id === session.file_id)
      || (session.path && tab.path === session.path)
    ));
    if (existingIndex >= 0) {
      const tabId = this.tabs[existingIndex].tab_id;
      const wasActive = this.activeTabId === tabId || this.session?.tab_id === tabId;
      const merged = { ...this.tabs[existingIndex], ...session, tab_id: tabId };
      this.tabs.splice(existingIndex, 1, merged);
      this.activeTabId = tabId;
      if (wasActive) {
        this.hydrateActiveSession(merged, { preservePage: true, focus: false });
        return;
      }
    } else {
      this.tabs.push(session);
      this.activeTabId = session.tab_id;
    }
    this.selectTab(this.activeTabId);
  },

  hydrateActiveSession(tab, options = {}) {
    this.session = tab || null;
    this.activeTabId = tab?.tab_id || "";
    this.editorText = String(tab?.text || "");
    this.dirty = Boolean(tab?.dirty);
    if (this.previewEditing) this.cancelPreviewEdit();
    if (!options.preservePage) {
      this.activePageIndex = 0;
    } else {
      this.clampActivePage();
    }
    this.searchMatches = [];
    this.searchIndex = -1;
    this.resetHistory(this.editorText);
    this.setSourceEditorText(this.editorText);
    this.updateSourceEditorMode();
    if (tab?.session_id) {
      requestEditor("editor_activate", { session_id: tab.session_id }, 2500).catch(() => {});
    }
    if (this.searchOpen && this.searchQuery) this.runSearch();
    else if (this.isSourceMode()) this.scheduleSourceEditorInit();
    else this.schedulePreviewEnhance();
    this.refreshSourceEditorLayout();
    this.queueRender({ focus: this.isSourceMode() && Boolean(tab) && options.focus !== false, end: false });
  },

  selectTab(tabId, options = {}) {
    this.applyPreviewEdit({ silent: true });
    this.syncEditorText();
    const tab = this.tabs.find((item) => item.tab_id === tabId) || this.tabs[0] || null;
    this.previewEditing = false;
    this.previewEditDirty = false;
    this.previewEditText = "";
    this.previewEditPageIndex = -1;
    this.hydrateActiveSession(tab, { preservePage: false, focus: options.focus !== false });
  },

  ensureActiveTab() {
    if (this.session && this.tabs.some((tab) => tab.tab_id === this.session.tab_id)) return;
    if (this.tabs.length) this.selectTab(this.tabs[0].tab_id, { focus: false });
  },

  isActiveTab(tab) {
    return Boolean(tab && tab.tab_id === this.activeTabId);
  },

  isTabDirty(tab) {
    return Boolean(tab?.dirty || (this.isActiveTab(tab) && (this.dirty || this.previewEditDirty)));
  },

  hasPendingClose() {
    return Boolean(this.pendingClose);
  },

  pendingCloseTitle() {
    const pending = this.pendingClose;
    if (!pending) return "";
    if (pending.kind === "all") {
      return `Close ${pending.totalCount || 0} open files?`;
    }
    const tab = this.tabs.find((item) => item.tab_id === pending.tabId);
    return `Close ${this.tabTitle(tab || {})}?`;
  },

  pendingCloseMessage() {
    const pending = this.pendingClose;
    if (!pending) return "";
    const dirtyCount = Number(pending.dirtyCount || 0);
    if (pending.kind === "all") {
      if (dirtyCount === 0) return "All open text files will be closed.";
      return `${dirtyCount} open ${dirtyCount === 1 ? "file has" : "files have"} unsaved changes.`;
    }
    if (dirtyCount > 0) return "This file has unsaved changes.";
    return "This file will be closed.";
  },

  pendingCloseHasDirty() {
    return Number(this.pendingClose?.dirtyCount || 0) > 0;
  },

  pendingCloseDiscardLabel() {
    return this.pendingCloseHasDirty() ? "Discard" : "Close";
  },

  beginCloseConfirmation(kind, tabIds = []) {
    const ids = tabIds.filter(Boolean);
    const tabs = ids.map((id) => this.tabs.find((tab) => tab.tab_id === id)).filter(Boolean);
    const dirtyCount = tabs.filter((tab) => this.isTabDirty(tab)).length;
    this.pendingClose = {
      kind,
      tabId: kind === "single" ? ids[0] || "" : "",
      tabIds: ids,
      totalCount: tabs.length,
      dirtyCount,
    };
    if (kind === "single" && ids[0] && this.activeTabId !== ids[0]) {
      this.selectTab(ids[0], { focus: false });
    }
  },

  cancelPendingClose() {
    this.pendingClose = null;
  },

  async confirmPendingClose(options = {}) {
    const pending = this.pendingClose;
    if (!pending || this.loading) return;
    this.pendingClose = null;
    const save = options.save === true;
    if (pending.kind === "all") {
      await this.closeAllFiles({ confirm: false, save, tabIds: pending.tabIds || [] });
      return;
    }
    await this.closeTab(pending.tabId, { confirm: false, save });
  },

  async closeTab(tabId, options = {}) {
    const tab = this.tabs.find((item) => item.tab_id === tabId);
    if (!tab) return;
    if (this.isTabDirty(tab) && options.confirm !== false) {
      this.beginCloseConfirmation("single", [tab.tab_id]);
      return;
    }
    await this.closeTabNow(tab, { save: options.save === true });
  },

  async closeTabNow(tab, options = {}) {
    if (!tab || this.loading) return false;
    const tabId = tab.tab_id;
    if (options.save === true && this.isTabDirty(tab)) {
      const saved = await this.saveTab(tab);
      if (!saved) return false;
    }
    if (this.activeTabId === tabId && this.previewEditing) this.cancelPreviewEdit();
    try {
      if (tab.session_id) {
        await requestEditor("editor_close", { session_id: tab.session_id }, 2500).catch(() => null);
      }
      await callEditor("close", {
        session_id: tab.session_id || "",
        store_session_id: tab.store_session_id || "",
        file_id: tab.file_id || "",
      });
    } catch (error) {
      console.warn("Editor close skipped", error);
    }
    this.tabs = this.tabs.filter((item) => item.tab_id !== tabId);
    if (this.pendingClose?.tabId === tabId || this.pendingClose?.tabIds?.includes(tabId)) {
      this.pendingClose = null;
    }
    if (this.activeTabId === tabId) {
      this.session = null;
      this.activeTabId = "";
      this.editorText = "";
      this.dirty = false;
      this.ensureActiveTab();
    }
    this.ensureActiveTab();
    await this.refresh();
    return true;
  },

  async closeActiveFile() {
    if (!this.session || this.loading) return;
    await this.closeTab(this.session.tab_id);
  },

  async closeAllFiles(options = {}) {
    if (this.loading) return;
    const requestedIds = Array.isArray(options.tabIds) && options.tabIds.length
      ? options.tabIds
      : this.visibleTabs().map((tab) => tab.tab_id);
    const tabs = requestedIds.map((id) => this.tabs.find((tab) => tab.tab_id === id)).filter(Boolean);
    if (!tabs.length) return;

    const dirtyTabs = tabs.filter((tab) => this.isTabDirty(tab));
    if (dirtyTabs.length && options.confirm !== false) {
      this.beginCloseConfirmation("all", tabs.map((tab) => tab.tab_id));
      return;
    }

    this.pendingClose = null;
    for (const tab of [...tabs]) {
      const current = this.tabs.find((item) => item.tab_id === tab.tab_id);
      if (!current) continue;
      const closed = await this.closeTabNow(current, {
        save: options.save === true && this.isTabDirty(current),
      });
      if (!closed) break;
    }
  },

  scheduleSourceEditorInit() {
    if (!this.isSourceMode()) return;
    globalThis.requestAnimationFrame?.(() => {
      globalThis.requestAnimationFrame?.(() => this.initSourceEditor());
    });
  },

  initSourceEditor() {
    if (!this.isSourceMode() || !this._root) return;
    const container = this._root.querySelector?.("[data-editor-ace]");
    if (this.sourceEditor && !this._root.contains?.(this.sourceEditor.container)) {
      this.destroySourceEditor();
    }
    if (!container || this.sourceEditor) return;
    if (!globalThis.ace?.edit) {
      this.aceUnavailable = true;
      return;
    }

    const editor = globalThis.ace.edit(container);
    const darkMode = globalThis.localStorage?.getItem("darkMode");
    const theme = darkMode !== "false" ? "ace/theme/github_dark" : "ace/theme/github";
    editor.setTheme(theme);
    editor.session.setMode(this.sourceEditorMode());
    editor.session.setUseWrapMode(true);
    editor.setOptions({
      fontSize: "13px",
      showGutter: false,
      showPrintMargin: false,
      useWorker: false,
    });
    editor.renderer.setShowGutter(false);
    editor.renderer.setScrollMargin(14, 14, 0, 0);
    editor.setValue(this.editorText || "", -1);
    this._sourceEditorChangeHandler = () => {
      if (this._settingSourceEditorValue) return;
      this.editorText = editor.getValue();
      this.onSourceInput();
    };
    editor.session.on("change", this._sourceEditorChangeHandler);
    this.sourceEditor = editor;
    this.aceUnavailable = false;
    this.updateSourceEditorMode();
    this.queueRender({ focus: Boolean(this.session), end: false });
  },

  sourceEditorMode(tab = this.session) {
    return this.isMarkdown(tab) ? "ace/mode/markdown" : "ace/mode/text";
  },

  updateSourceEditorMode(tab = this.session) {
    try {
      this.sourceEditor?.session?.setMode(this.sourceEditorMode(tab));
    } catch {}
  },

  destroySourceEditor() {
    if (this.sourceEditor?.session && this._sourceEditorChangeHandler) {
      this.sourceEditor.session.off?.("change", this._sourceEditorChangeHandler);
    }
    const container = this.sourceEditor?.container;
    this.sourceEditor?.destroy?.();
    if (container) container.textContent = "";
    this.sourceEditor = null;
    this._sourceEditorChangeHandler = null;
  },

  setSourceEditorText(text = "") {
    if (!this.sourceEditor) return;
    const value = String(text || "");
    if (this.sourceEditor.getValue() === value) return;
    this._settingSourceEditorValue = true;
    this.sourceEditor.setValue(value, -1);
    this._settingSourceEditorValue = false;
    this.refreshSourceEditorLayout();
  },

  refreshSourceEditorLayout() {
    const editor = this.sourceEditor;
    if (!editor) return;
    const refresh = () => {
      editor.resize?.(true);
      editor.renderer?.updateFull?.();
      editor.renderer?.updateText?.();
    };
    if (globalThis.requestAnimationFrame) {
      globalThis.requestAnimationFrame(() => globalThis.requestAnimationFrame(refresh));
    } else {
      globalThis.setTimeout(refresh, 0);
    }
  },

  async save() {
    if (!this.session || this.saving || !this.isTextDocument()) return;
    this.applyPreviewEdit({ silent: true });
    this.syncEditorText();
    this.saving = true;
    this.error = "";
    try {
      let response;
      const payload = { session_id: this.session.session_id, text: this.editorText };
      try {
        response = await requestEditor("editor_save", payload, 10000);
      } catch (_socketError) {
        response = await callEditor("save", payload);
      }
      if (response?.ok === false) throw new Error(response.error || "Save failed.");
      const document = normalizeTextDocument(response.document || this.session.document || {});
      const updated = {
        ...this.session,
        text: this.editorText,
        dirty: false,
        document,
        path: document.path || this.session.path,
        file_id: document.file_id || this.session.file_id,
        extension: document.extension || this.session.extension,
        version: document.version || response.version || this.session.version,
      };
      this.replaceActiveSession(updated);
      this.dirty = false;
      this.setMessage("Saved");
      await this.refresh();
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    } finally {
      this.saving = false;
    }
  },

  async downloadActiveFile() {
    if (!this.session || this.saving || !this.isTextDocument()) return;
    if (this.dirty) await this.save();
    if (this.dirty) return;
    const path = this.session.path || this.session.document?.path;
    if (path) fileBrowserStore.downloadFile({ path, name: this.tabTitle() });
  },

  async saveAs() {
    if (!this.session || this.saving || !this.isTextDocument()) return;
    this.applyPreviewEdit({ silent: true });
    this.syncEditorText();

    let startPath = parentPath(this.session.path || this.session.document?.path || "");
    if (!startPath || startPath === "/") {
      try {
        const home = await callEditor("home");
        startPath = home?.path || startPath || "/a0/usr/workdir";
      } catch {
        startPath = "/a0/usr/workdir";
      }
    }

    await fileBrowserStore.openSaveAsPicker(startPath, {
      filename: textDocumentFilename(this.session.path || this.session.title || "Untitled.md"),
      defaultExtension: textDocumentDefaultExtension(this.session.path || this.session.title || "Untitled.md"),
      onConfirm: async ({ path } = {}) => {
        if (!path) return false;
        await this.saveAsPath(path);
        return true;
      },
    });
  },

  async saveAsPath(path) {
    if (!this.session || this.saving || !this.isTextDocument()) return null;
    this.saving = true;
    this.error = "";
    try {
      const payload = {
        session_id: this.session.session_id,
        store_session_id: this.session.store_session_id || "",
        path,
        text: this.editorText,
      };
      const response = await callEditor("save_as", payload);
      if (response?.ok === false) throw new Error(response.error || "Save As failed.");
      const document = normalizeTextDocument(response.document || this.session.document || {});
      const updated = {
        ...this.session,
        text: this.editorText,
        dirty: false,
        document,
        title: document.title || document.basename || basename(document.path),
        path: document.path || path,
        file_id: document.file_id || this.session.file_id,
        extension: document.extension || this.session.extension,
        store_session_id: response.store_session_id || this.session.store_session_id,
        version: document.version || response.version || this.session.version,
      };
      this.replaceActiveSession(updated);
      this.dirty = false;
      this.setMessage("Saved As");
      await this.refresh();
      return updated;
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      throw error;
    } finally {
      this.saving = false;
    }
  },

  async saveTab(tab) {
    if (!tab || this.saving || !this.isTextDocument(tab)) return false;
    if (this.isActiveTab(tab)) {
      this.applyPreviewEdit({ silent: true });
      this.syncEditorText();
    }
    this.saving = true;
    this.error = "";
    try {
      let response;
      const payload = {
        session_id: tab.session_id,
        text: this.isActiveTab(tab) ? this.editorText : String(tab.text || ""),
      };
      try {
        response = await requestEditor("editor_save", payload, 10000);
      } catch (_socketError) {
        response = await callEditor("save", payload);
      }
      if (response?.ok === false) throw new Error(response.error || "Save failed.");
      const document = normalizeTextDocument(response.document || tab.document || {});
      const updated = {
        ...tab,
        text: payload.text,
        dirty: false,
        document,
        path: document.path || tab.path,
        file_id: document.file_id || tab.file_id,
        extension: document.extension || tab.extension,
        version: document.version || response.version || tab.version,
      };
      this.replaceSession(tab, updated);
      if (this.isActiveTab(updated)) {
        this.dirty = false;
      }
      this.setMessage("Saved");
      await this.refresh();
      return true;
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      return false;
    } finally {
      this.saving = false;
    }
  },

  async renameActiveFile() {
    if (!this.session || this.saving) return;
    this.applyPreviewEdit({ silent: true });
    const session = this.session;
    const path = session.path || session.document?.path || "";
    if (!path) {
      this.error = "This document does not have a file path to rename.";
      return;
    }
    const name = basename(path || session.title || "");
    const extension = extensionOf(name);
    await fileBrowserStore.openRenameModal(
      {
        name,
        path,
        is_dir: false,
        size: session.document?.size || 0,
        modified: session.document?.last_modified || "",
        type: "document",
      },
      {
        currentPath: parentPath(path),
        validateName: (newName) => {
          if (!extension) return true;
          return extensionOf(newName) === extension || `Keep the .${extension} extension for this open document.`;
        },
        performRename: async ({ path: renamedPath }) => {
          const payload = {
            file_id: session.file_id || "",
            path: renamedPath,
          };
          if (this.isTextDocument(session)) {
            this.syncEditorText();
            payload.text = this.session?.tab_id === session.tab_id ? this.editorText : session.text || "";
          }
          return await callEditor("renamed", payload);
        },
        onRenamed: async ({ path: renamedPath, response }) => {
          await this.handleActiveFileRenamed(session, renamedPath, response);
        },
      },
    );
  },

  async handleActiveFileRenamed(session, renamedPath, renameResponse = null) {
    const response = renameResponse || await callEditor("renamed", {
      file_id: session.file_id || "",
      path: renamedPath,
    });
    if (response?.ok === false) throw new Error(response.error || "Rename failed.");

    const document = normalizeTextDocument(response.document || session.document || {});
    const updated = {
      ...session,
      document,
      title: document.title || document.basename || basename(document.path),
      path: document.path || renamedPath,
      extension: document.extension || session.extension,
      file_id: document.file_id || session.file_id,
      version: document.version || response.version || session.version,
      text: this.session?.tab_id === session.tab_id ? this.editorText : session.text,
      dirty: false,
    };
    this.replaceSession(session, updated);
    this.dirty = false;
    this.setMessage("Renamed");
    await this.refresh();
  },

  replaceActiveSession(next) {
    if (!this.session) return;
    this.replaceSession(this.session, next);
  },

  replaceSession(previous, next) {
    const wasActive = this.activeTabId === (previous?.tab_id || next.tab_id);
    if (wasActive) {
      this.session = next;
      this.updateSourceEditorMode(next);
    }
    const index = this.tabs.findIndex((tab) => tab.tab_id === (previous?.tab_id || next.tab_id));
    if (index >= 0) this.tabs.splice(index, 1, next);
  },

  setMessage(value) {
    this.message = value;
    if (this._saveMessageTimer) globalThis.clearTimeout(this._saveMessageTimer);
    this._saveMessageTimer = globalThis.setTimeout(() => {
      this.message = "";
      this._saveMessageTimer = null;
    }, SAVE_MESSAGE_MS);
  },

  resetHistory(text) {
    this._history = [String(text || "")];
    this._historyIndex = 0;
    this._historyPushedAt = 0;
  },

  pushHistory(text, coalesce = false) {
    const value = String(text || "");
    if (this._history[this._historyIndex] === value) return;
    const now = Date.now();
    if (
      coalesce
      && this._historyPushedAt
      && now - this._historyPushedAt <= INPUT_PUSH_DELAY_MS
      && this._historyIndex === this._history.length - 1
      && this._historyIndex > 0
    ) {
      this._history[this._historyIndex] = value;
      this._historyPushedAt = now;
      return;
    }
    this._history = this._history.slice(0, this._historyIndex + 1);
    this._history.push(value);
    if (this._history.length > MAX_HISTORY) this._history.shift();
    this._historyIndex = this._history.length - 1;
    this._historyPushedAt = coalesce ? now : 0;
  },

  undo() {
    if (this._historyIndex <= 0) return;
    this._historyPushedAt = 0;
    this._historyIndex -= 1;
    this.applyEditorText(this._history[this._historyIndex], true);
  },

  redo() {
    if (this._historyIndex >= this._history.length - 1) return;
    this._historyPushedAt = 0;
    this._historyIndex += 1;
    this.applyEditorText(this._history[this._historyIndex], true);
  },

  canUndo() {
    return this._historyIndex > 0;
  },

  canRedo() {
    return this._historyIndex < this._history.length - 1;
  },

  applyEditorText(text, markDirty = false) {
    this.editorText = String(text || "");
    this.setSourceEditorText(this.editorText);
    if (this.session) {
      this.session.text = this.editorText;
      this.session.dirty = markDirty || this.session.dirty;
    }
    if (markDirty) this.markDirty();
    this.queueRender({ focus: true });
  },

  markDirty() {
    this.dirty = true;
    if (this.session) this.session.dirty = true;
  },

  onSourceInput() {
    this.markDirty();
    this.pushHistory(this.editorText, true);
    this.scheduleInputPush();
  },

  syncEditorText() {
    if (!this.session) return;
    if (this.previewEditing) return;
    if (this.sourceEditor && this.isSourceMode()) {
      this.editorText = this.sourceEditor.getValue();
    }
    this.session.text = this.editorText;
  },

  scheduleInputPush() {
    if (!this.session?.session_id || !this.isTextDocument()) return;
    if (this._inputTimer) globalThis.clearTimeout(this._inputTimer);
    this._inputTimer = globalThis.setTimeout(() => {
      this._inputTimer = null;
      this.flushInput();
    }, INPUT_PUSH_DELAY_MS);
  },

  flushInput() {
    if (!this.session?.session_id || !this.isTextDocument()) return;
    if (this.previewEditing) return;
    this.syncEditorText();
    requestEditor("editor_input", {
      session_id: this.session.session_id,
      text: this.editorText,
    }, 3000).catch(() => {});
  },

  format(command) {
    if (!this.session || !this.isTextDocument()) return;
    if (this.sourceEditor && this.isSourceMode()) {
      const selected = this.sourceEditor.getSelectedText();
      const replacement = this.formatReplacement(command, selected);
      if (replacement === selected) return;
      this.sourceEditor.session.replace(this.sourceEditor.getSelectionRange(), replacement);
      this.editorText = this.sourceEditor.getValue();
      this.onSourceInput();
      this.sourceEditor.focus();
      return;
    }
    const textarea = this._root?.querySelector?.("[data-editor-source]");
    if (!textarea) return;
    const start = textarea.selectionStart || 0;
    const end = textarea.selectionEnd || start;
    const selected = this.editorText.slice(start, end);
    const replacement = this.formatReplacement(command, selected);
    if (replacement === selected) return;
    this.editorText = `${this.editorText.slice(0, start)}${replacement}${this.editorText.slice(end)}`;
    this.onSourceInput();
    globalThis.requestAnimationFrame?.(() => {
      textarea.focus();
      textarea.selectionStart = start;
      textarea.selectionEnd = start + replacement.length;
    });
  },

  formatReplacement(command, selected = "") {
    if (command === "bold") return `**${selected || "text"}**`;
    if (command === "italic") return `*${selected || "text"}*`;
    if (command === "list") return (selected || "item").split("\n").map((line) => `- ${line.replace(/^[-*]\s+/, "")}`).join("\n");
    if (command === "numbered") return (selected || "item").split("\n").map((line, index) => `${index + 1}. ${line.replace(/^\d+\.\s+/, "")}`).join("\n");
    if (command === "table") return "| Column | Value |\n| --- | --- |\n|  |  |";
    return selected;
  },

  queueRender(options = {}) {
    if (options.focus) {
      this._pendingFocus = true;
      this._pendingFocusEnd = options.end !== false;
      this._focusAttempts = 0;
    }
    const render = () => {
      if (this._pendingFocus && this.focusEditor({ end: this._pendingFocusEnd })) {
        this._pendingFocus = false;
        this._focusAttempts = 0;
      } else if (this._pendingFocus && this._focusAttempts < 6) {
        this._focusAttempts += 1;
        globalThis.setTimeout(render, 45);
      }
    };
    if (globalThis.requestAnimationFrame) {
      globalThis.requestAnimationFrame(render);
    } else {
      globalThis.setTimeout(render, 0);
    }
  },

  focusEditor(options = {}) {
    if (!this.session || !this.isTextDocument()) return false;
    if (this.sourceEditor && this.isSourceMode()) {
      this.sourceEditor.focus();
      if (options.end !== false) {
        const session = this.sourceEditor.session;
        const row = Math.max(0, session.getLength() - 1);
        const column = session.getLine(row).length;
        this.sourceEditor.moveCursorTo(row, column);
      }
      return true;
    }
    const source = this._root?.querySelector?.("[data-editor-source]");
    if (!source) return false;
    source.focus?.({ preventScroll: true });
    if (!editorContainsFocus(source)) return false;
    if (options.end !== false) placeCaretAtEnd(source);
    return true;
  },

  isMarkdown(tab = this.session) {
    const ext = String(tab?.extension || tab?.document?.extension || "").toLowerCase();
    return ext === "md";
  },

  isTextDocument(tab = this.session) {
    const ext = String(tab?.extension || tab?.document?.extension || "").toLowerCase();
    return EDITOR_TEXT_EXTENSIONS.has(ext);
  },

  hasActiveFile(tab = this.session) {
    return Boolean(tab && this.isTextDocument(tab));
  },

  visibleTabs() {
    return this.tabs.filter((tab) => this.hasActiveFile(tab));
  },

  defaultTitle(kind, fmt) {
    const date = new Date().toISOString().slice(0, 10);
    if (fmt === "md") return `Markdown ${date}`;
    if (fmt === "txt") return `Text ${date}`;
    return `Text ${date}`;
  },

  tabTitle(tab = {}) {
    tab = tab || {};
    return tab.title || tab.document?.basename || basename(tab.path);
  },

  tabLabel(tab = {}) {
    tab = tab || {};
    const title = this.tabTitle(tab);
    return tab.dirty ? `${title} unsaved` : title;
  },

  tabIcon(tab = {}) {
    tab = tab || {};
    const ext = String(tab.extension || tab.document?.extension || "").toLowerCase();
    if (ext === "md") return "article";
    if (ext === "txt") return "description";
    return "draft";
  },

  async runNewMenuAction(action = "") {
    const normalized = String(action || "").trim().toLowerCase();
    if (normalized === "open") return await this.openFileBrowser();
    if (normalized === "markdown") return await this.create("document", "md");
    if (normalized === "text") return await this.create("document", "txt");
    return null;
  },

  installHeaderNewMenu(header = null) {
    if (!header || header.querySelector(".editor-header-actions")) return () => {};

    const root = document.createElement("div");
    root.className = "editor-header-actions surface-modal-new-action";
    root.innerHTML = `
      <button type="button" class="editor-header-new-button surface-modal-new-button" aria-haspopup="menu" aria-expanded="false">
        <span class="material-symbols-outlined" aria-hidden="true">add</span>
        <span>New</span>
        <span class="material-symbols-outlined editor-new-chevron" aria-hidden="true">expand_more</span>
      </button>
      <div class="editor-new-menu" role="menu" hidden>
        <button type="button" class="editor-new-menu-item" role="menuitem" data-editor-new-action="open">
          <span class="material-symbols-outlined" aria-hidden="true">folder_open</span>
          <span>Open</span>
        </button>
        <button type="button" class="editor-new-menu-item" role="menuitem" data-editor-new-action="markdown">
          <span class="material-symbols-outlined" aria-hidden="true">article</span>
          <span>Markdown</span>
        </button>
        <button type="button" class="editor-new-menu-item" role="menuitem" data-editor-new-action="text">
          <span class="material-symbols-outlined" aria-hidden="true">description</span>
          <span>Text</span>
        </button>
      </div>
    `;

    const button = root.querySelector(".editor-header-new-button");
    const menu = root.querySelector(".editor-new-menu");
    const setOpen = (open) => {
      root.classList.toggle("is-open", open);
      button?.setAttribute("aria-expanded", open.toString());
      if (menu) menu.hidden = !open;
    };
    const onButtonClick = (event) => {
      event.preventDefault();
      event.stopPropagation();
      setOpen(!root.classList.contains("is-open"));
    };
    const onMarkdownClick = (event) => {
      if (!root.contains(event.target)) setOpen(false);
    };
    const onMarkdownKeydown = (event) => {
      if (event.key === "Escape") setOpen(false);
    };

    button?.addEventListener("click", onButtonClick);
    for (const item of root.querySelectorAll("[data-editor-new-action]")) {
      item.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();
        const action = event.currentTarget?.dataset?.editorNewAction || "";
        setOpen(false);
        await this.runNewMenuAction(action);
      });
    }
    document.addEventListener("click", onMarkdownClick);
    document.addEventListener("keydown", onMarkdownKeydown);

    placeSurfaceModalHeaderAction(header, root, "new");

    setOpen(false);
    return () => {
      button?.removeEventListener("click", onButtonClick);
      document.removeEventListener("click", onMarkdownClick);
      document.removeEventListener("keydown", onMarkdownKeydown);
      root.remove();
    };
  },

  setupMarkdownModal(element = null) {
    const root = element || document.querySelector(".editor-panel");
    const inner = root?.closest?.(".modal-inner");
    const header = inner?.querySelector?.(".modal-header");
    if (!inner || !header || inner.dataset.editorModalReady === "1") return;
    inner.dataset.editorModalReady = "1";
    inner.classList.add("editor-modal");
    const floatingCleanup = setupFloatingSurfaceModalChrome({
      root,
      modalClass: "editor-modal",
      focusButtonClass: "editor-modal-focus-button",
      minWidth: 640,
      minHeight: 460,
      onBoundsChange: () => this.refreshSourceEditorLayout(),
      onFocusChange: () => this.refreshSourceEditorLayout(),
    });
    const menuCleanup = this.installHeaderNewMenu(header);
    this._headerCleanup = () => {
      menuCleanup?.();
      floatingCleanup?.();
      delete inner.dataset.editorModalReady;
      inner.classList.remove("editor-modal", "is-focus-mode");
    };
  },

  async handleEditorUrlIntent(intent = {}) {
    const editor = editorIntent(intent?.url || "");
    if (!editor) return false;
    await openLatestSurface("editor", {
      path: editor.path,
      refresh: true,
      source: intent?.source || "desktop-open",
    });
    return true;
  },
};

export const store = createStore("editor", model);

registerUrlHandler((intent) => model.handleEditorUrlIntent(intent));
