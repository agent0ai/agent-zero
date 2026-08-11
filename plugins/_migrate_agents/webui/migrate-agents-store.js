import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";
import { closeModal } from "/js/modals.js";
import { setContext } from "/index.js";
import {
  toastFrontendError,
  toastFrontendInfo,
  toastFrontendSuccess,
  toastFrontendWarning,
} from "/components/notifications/notification-store.js";

const PREVIEW_API = "/api/plugins/_migrate_agents/migration_preview";
const IMPORT_API = "/api/plugins/_migrate_agents/migration_import";

export const sources = [
  {
    id: "openclaw",
    name: "OpenClaw",
    logo: "/plugins/_migrate_agents/webui/assets/openclaw.svg",
    accent: "coral",
    hint: "Chats, projects, memory, instructions and skills",
    guideTitle: "Create an OpenClaw backup",
    guideLabel: "Run in a terminal",
    command: "openclaw backup create --verify",
    guideNote: "Choose the generated .tar.gz file below. Credentials inside the backup are detected and excluded.",
  },
  {
    id: "hermes",
    name: "Hermes Agent",
    logo: "/plugins/_migrate_agents/webui/assets/hermes.svg",
    accent: "gold",
    hint: "Chats, projects, memory, instructions and skills",
    guideTitle: "Export your Hermes sessions",
    guideLabel: "Run in a terminal",
    command: "hermes sessions export backup.jsonl --redact",
    guideNote: "To include memory and skills, also select the relevant files or folders from your Hermes data directory.",
  },
  {
    id: "opencode",
    name: "OpenCode",
    logo: "/plugins/_migrate_agents/webui/assets/opencode.svg",
    accent: "mint",
    hint: "Chats, projects, AGENTS.md and skills",
    guideTitle: "Export an OpenCode session",
    guideLabel: "Run in a terminal",
    command: "opencode export <session-id> > session.json",
    guideNote: "Repeat for other sessions. You can also add AGENTS.md and skill folders when selecting files.",
  },
  {
    id: "claude",
    name: "Claude Code",
    logo: "/plugins/_migrate_agents/webui/assets/claude.svg",
    accent: "violet",
    hint: "Chats, projects, CLAUDE.md, memory and skills",
    guideTitle: "Find your Claude Code data",
    guideLabel: "Folder to select",
    command: "~/.claude/projects",
    guideNote: "Add any CLAUDE.md, memory files, and skill folders you want to bring over.",
  },
  {
    id: "codex",
    name: "Codex",
    logo: "/plugins/_migrate_agents/webui/assets/codex.svg",
    accent: "sky",
    hint: "Chats, projects, AGENTS.md, memory and skills",
    guideTitle: "Find your Codex data",
    guideLabel: "Folders to select",
    command: "$CODEX_HOME/sessions and $CODEX_HOME/archived_sessions",
    guideNote: "CODEX_HOME is usually ~/.codex. Add AGENTS.md, memory files, and skill folders separately if needed.",
  },
];

async function responseJson(response) {
  const text = await response.text();
  if (!response.ok) throw new Error(text || `Request failed (${response.status})`);
  return text ? JSON.parse(text) : {};
}

export const store = createStore("migrationParty", {
  sources,
  source: "openclaw",
  files: [],
  preview: null,
  busy: false,
  includeChats: true,
  includeProjects: true,
  includeMemories: true,
  includeInstructions: true,
  includeSkills: true,
  reviewed: false,
  dragActive: false,
  copied: false,
  copyTimer: null,

  get selectedSource() {
    return sources.find((item) => item.id === this.source) || sources[0];
  },

  get totalBytes() {
    return this.files.reduce((total, file) => total + (file.size || 0), 0);
  },

  get canImport() {
    return Boolean(
      this.preview &&
      this.reviewed &&
      !this.busy &&
      this.selectedItemCount > 0,
    );
  },

  get selectedItemCount() {
    const summary = this.preview?.summary || {};
    return (
      (this.includeChats ? summary.chats || 0 : 0) +
      (this.includeProjects ? summary.projects || 0 : 0) +
      (this.includeMemories ? summary.memories || 0 : 0) +
      (this.includeInstructions ? summary.instructions || 0 : 0) +
      (this.includeSkills ? summary.skills || 0 : 0)
    );
  },

  get primaryDisabled() {
    return this.busy || (this.preview ? !this.canImport : !this.files.length);
  },

  get primaryLabel() {
    if (this.busy) return this.preview ? "Importing…" : "Checking export…";
    if (this.preview) return "Import selected data";
    return this.files.length ? "Review selected data" : "Select an export to continue";
  },

  onOpen() {
    this.reset();
  },

  cleanup() {
    this.dragActive = false;
    if (this.copyTimer) clearTimeout(this.copyTimer);
  },

  reset() {
    this.files = [];
    this.preview = null;
    this.reviewed = false;
    this.busy = false;
    this.dragActive = false;
    this.copied = false;
    this.includeChats = true;
    this.includeProjects = true;
    this.includeMemories = true;
    this.includeInstructions = true;
    this.includeSkills = true;
  },

  chooseSource(source) {
    if (source === this.source) return;
    this.source = source;
    this.files = [];
    this.preview = null;
    this.reviewed = false;
    this.copied = false;
  },

  acceptFiles(fileList) {
    const incoming = Array.from(fileList || []);
    if (!incoming.length) return;
    const byKey = new Map(this.files.map((file) => [`${file.webkitRelativePath || file.name}:${file.size}`, file]));
    for (const file of incoming) byKey.set(`${file.webkitRelativePath || file.name}:${file.size}`, file);
    this.files = [...byKey.values()];
    this.preview = null;
    this.reviewed = false;
  },

  handleFiles(event) {
    this.acceptFiles(event?.target?.files);
    if (event?.target) event.target.value = "";
  },

  onDrop(event) {
    this.dragActive = false;
    this.acceptFiles(event?.dataTransfer?.files);
  },

  removeFile(index) {
    this.files = this.files.filter((_, position) => position !== index);
    this.preview = null;
    this.reviewed = false;
  },

  clearFiles() {
    this.files = [];
    this.preview = null;
    this.reviewed = false;
  },

  formatBytes(value) {
    if (!value) return "0 B";
    const units = ["B", "KiB", "MiB", "GiB"];
    const power = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
    return `${(value / 1024 ** power).toFixed(power ? 1 : 0)} ${units[power]}`;
  },

  async copyExportValue() {
    try {
      await navigator.clipboard.writeText(this.selectedSource.command);
      this.copied = true;
      if (this.copyTimer) clearTimeout(this.copyTimer);
      this.copyTimer = setTimeout(() => { this.copied = false; }, 1600);
      void toastFrontendInfo("Copied to the clipboard.", "Migrate Agents");
    } catch {
      void toastFrontendError("Could not copy. Select the text and copy it manually.", "Migrate Agents");
    }
  },

  formData(includeOptions = false) {
    const data = new FormData();
    data.append("source", this.source);
    for (const file of this.files) {
      data.append("files[]", file, file.webkitRelativePath || file.name);
    }
    if (includeOptions) {
      data.append("include_chats", String(this.includeChats));
      data.append("include_projects", String(this.includeProjects));
      data.append("include_memories", String(this.includeMemories));
      data.append("include_instructions", String(this.includeInstructions));
      data.append("include_skills", String(this.includeSkills));
    }
    return data;
  },

  async inspect() {
    if (!this.files.length) {
      void toastFrontendWarning("Choose an export file, archive, or folder first.", "Migrate Agents");
      return;
    }
    this.busy = true;
    this.preview = null;
    this.reviewed = false;
    try {
      const response = await fetchApi(PREVIEW_API, {
        method: "POST",
        credentials: "same-origin",
        body: this.formData(),
      });
      this.preview = await responseJson(response);
      const found = this.preview?.summary || {};
      this.includeChats = Boolean(found.chats);
      this.includeProjects = Boolean(found.projects);
      this.includeMemories = Boolean(found.memories);
      this.includeInstructions = Boolean(found.instructions);
      this.includeSkills = Boolean(found.skills);
      void toastFrontendInfo(
        `Found ${found.chats || 0} chats, ${found.projects || 0} projects, ${found.memories || 0} memories, ${found.instructions || 0} instructions, and ${found.skills || 0} skills.`,
        "Migrate Agents",
      );
      if (this.preview?.warnings?.length) {
        void toastFrontendWarning(`${this.preview.warnings.length} item(s) need review.`, "Migrate Agents");
      }
    } catch (error) {
      void toastFrontendError(error instanceof Error ? error.message : String(error), "Migrate Agents");
    } finally {
      this.busy = false;
    }
  },

  async migrate() {
    if (!this.canImport) return;
    this.busy = true;
    try {
      const response = await fetchApi(IMPORT_API, {
        method: "POST",
        credentials: "same-origin",
        body: this.formData(true),
      });
      const result = await responseJson(response);
      const summary = result.summary || {};
      void toastFrontendSuccess(
        `Imported ${summary.chats || 0} chats, ${summary.projects || 0} projects, ${summary.memories || 0} memories, ${summary.instructions || 0} instructions, and ${summary.skills || 0} skills.`,
        "Migrate Agents",
      );
      if (result.warnings?.length) {
        void toastFrontendWarning(`${result.warnings.length} item(s) were skipped with warnings.`, "Migrate Agents");
      }
      if (result.ctxids?.[0]) setContext(result.ctxids[0]);
      closeModal("/plugins/_migrate_agents/webui/main.html");
    } catch (error) {
      void toastFrontendError(error instanceof Error ? error.message : String(error), "Migrate Agents");
    } finally {
      this.busy = false;
    }
  },

  primaryAction() {
    return this.preview ? this.migrate() : this.inspect();
  },

  close() {
    closeModal("/plugins/_migrate_agents/webui/main.html");
  },
});
