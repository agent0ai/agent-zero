import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";
import { getCurrentUserDateString } from "/js/time-utils.js";

const SAVE_MESSAGE_MS = 1800;
const DESKTOP_DOCUMENT_EXTENSIONS = new Set(["odt", "ods", "odp", "docx", "xlsx", "pptx"]);

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

function normalizeDocument(doc = {}) {
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

function documentLabel(document = {}) {
  return document.title || document.basename || basename(document.path);
}

async function callOffice(action, payload = {}) {
  return await callJsonApi("/plugins/_office/office_session", {
    action,
    ctxid: currentContextId(),
    ...payload,
  });
}

const model = {
  status: null,
  loading: false,
  error: "",
  message: "",
  _root: null,
  _mode: "modal",
  _initialized: false,
  _saveMessageTimer: null,
  _headerCleanup: null,

  async init() {
    if (this._initialized) return;
    this._initialized = true;
    await this.refresh();
  },

  async onMount(element = null, options = {}) {
    await this.init();
    if (element) this._root = element;
    this._mode = options?.mode === "canvas" ? "canvas" : "modal";
    if (this._mode === "modal") this.setupDocumentModal(element);
  },

  async onOpen(payload = {}) {
    await this.init();
    await this.refresh();
    if (payload?.path || payload?.file_id) {
      await this.openSession({
        path: payload.path || "",
        file_id: payload.file_id || "",
        refresh: payload.refresh === true,
        source: payload.source || "",
      });
    }
  },

  cleanup() {
    this._headerCleanup?.();
    this._headerCleanup = null;
    if (this._mode === "modal") this._root = null;
  },

  async refresh() {
    try {
      const status = await callOffice("status");
      this.status = status || {};
      this.error = "";
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    }
  },

  async create(kind = "document", format = "") {
    const fmt = String(format || (kind === "spreadsheet" ? "ods" : kind === "presentation" ? "odp" : "odt")).toLowerCase();
    const title = this.defaultTitle(kind, fmt);
    await this.openSession({
      action: "create",
      kind,
      format: fmt,
      title,
    });
  },

  async openFileBrowser() {
    let workdirPath = "/a0/usr/workdir";
    try {
      const response = await callJsonApi("settings_get", null);
      workdirPath = response?.settings?.workdir_path || workdirPath;
    } catch {
      try {
        const home = await callOffice("home");
        workdirPath = home?.path || workdirPath;
      } catch {
        // Keep the configured default path when the home lookup is unavailable.
      }
    }
    await fileBrowserStore.open(workdirPath);
  },

  async openPath(path) {
    await this.openSession({ path: String(path || "") });
  },

  async openSession(payload = {}) {
    this.loading = true;
    this.error = "";
    try {
      const response = await callOffice(payload.action || "open", payload);
      if (response?.ok === false) {
        this.error = response.error || "Document could not be opened.";
        return null;
      }
      if (response?.requires_desktop || this.isDesktopDocument(response)) {
        const document = normalizeDocument(response.document || response);
        this.setMessage(`${documentLabel(document)} is ready. Use Open in Desktop to edit it.`);
        await this.refresh();
        return response;
      }
      await this.refresh();
      return response;
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      return null;
    } finally {
      this.loading = false;
    }
  },

  setMessage(value) {
    this.message = value;
    if (this._saveMessageTimer) globalThis.clearTimeout(this._saveMessageTimer);
    this._saveMessageTimer = globalThis.setTimeout(() => {
      this.message = "";
      this._saveMessageTimer = null;
    }, SAVE_MESSAGE_MS);
  },

  isDesktopDocument(tab = {}) {
    const ext = String(tab?.extension || tab?.document?.extension || "").toLowerCase();
    return DESKTOP_DOCUMENT_EXTENSIONS.has(ext);
  },

  defaultTitle(kind, fmt) {
    const date = getCurrentUserDateString();
    if (fmt === "odt") return `Writer ${date}`;
    if (fmt === "docx") return `DOCX ${date}`;
    if (kind === "spreadsheet") return `Spreadsheet ${date}`;
    if (kind === "presentation") return `Presentation ${date}`;
    return `Document ${date}`;
  },

  async runNewMenuAction(action = "") {
    const normalized = String(action || "").trim().toLowerCase();
    if (normalized === "open") return await this.openFileBrowser();
    if (normalized === "writer") return await this.create("document", "odt");
    if (normalized === "spreadsheet") return await this.create("spreadsheet", "ods");
    if (normalized === "presentation") return await this.create("presentation", "odp");
    return null;
  },

  installHeaderNewMenu(header = null) {
    if (!header || header.querySelector(".office-header-actions")) return () => {};

    const root = document.createElement("div");
    root.className = "office-header-actions";
    root.innerHTML = `
      <button type="button" class="office-header-new-button" aria-haspopup="menu" aria-expanded="false">
        <span class="material-symbols-outlined" aria-hidden="true">add</span>
        <span>New</span>
        <span class="material-symbols-outlined office-new-chevron" aria-hidden="true">expand_more</span>
      </button>
      <div class="office-new-menu" role="menu" hidden>
        <button type="button" class="office-new-menu-item" role="menuitem" data-office-new-action="open">
          <span class="material-symbols-outlined" aria-hidden="true">folder_open</span>
          <span>Open</span>
        </button>
        <button type="button" class="office-new-menu-item" role="menuitem" data-office-new-action="writer">
          <span class="material-symbols-outlined" aria-hidden="true">description</span>
          <span>Writer</span>
        </button>
        <button type="button" class="office-new-menu-item" role="menuitem" data-office-new-action="spreadsheet">
          <span class="material-symbols-outlined" aria-hidden="true">table_chart</span>
          <span>Spreadsheet</span>
        </button>
        <button type="button" class="office-new-menu-item" role="menuitem" data-office-new-action="presentation">
          <span class="material-symbols-outlined" aria-hidden="true">co_present</span>
          <span>Presentation</span>
        </button>
      </div>
    `;

    const button = root.querySelector(".office-header-new-button");
    const menu = root.querySelector(".office-new-menu");
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
    const onDocumentClick = (event) => {
      if (!root.contains(event.target)) setOpen(false);
    };
    const onDocumentKeydown = (event) => {
      if (event.key === "Escape") setOpen(false);
    };

    button?.addEventListener("click", onButtonClick);
    for (const item of root.querySelectorAll("[data-office-new-action]")) {
      item.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();
        const action = event.currentTarget?.dataset?.officeNewAction || "";
        setOpen(false);
        await this.runNewMenuAction(action);
      });
    }
    document.addEventListener("click", onDocumentClick);
    document.addEventListener("keydown", onDocumentKeydown);

    const firstHeaderAction = header.querySelector(".modal-close");
    if (firstHeaderAction) {
      firstHeaderAction.insertAdjacentElement("beforebegin", root);
    } else {
      header.appendChild(root);
    }

    setOpen(false);
    return () => {
      button?.removeEventListener("click", onButtonClick);
      document.removeEventListener("click", onDocumentClick);
      document.removeEventListener("keydown", onDocumentKeydown);
      root.remove();
    };
  },

  setupDocumentModal(element = null) {
    const root = element || document.querySelector(".office-panel");
    const inner = root?.closest?.(".modal-inner");
    const header = inner?.querySelector?.(".modal-header");
    if (!inner || !header || inner.dataset.officeModalReady === "1") return;
    inner.dataset.officeModalReady = "1";
    inner.classList.add("office-modal");
    this._headerCleanup = () => {
      delete inner.dataset.officeModalReady;
      inner.classList.remove("office-modal");
    };
    const menuCleanup = this.installHeaderNewMenu(header);
    const previousCleanup = this._headerCleanup;
    this._headerCleanup = () => {
      menuCleanup?.();
      previousCleanup?.();
    };
  },
};

export const store = createStore("office", model);
