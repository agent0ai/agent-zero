import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, fetchApi } from "/js/api.js";
import { openModal } from "/js/modals.js";

const endpoint = "team_project_files";
const modal = "projects/project-files.html";
const join = (directory, name) => directory ? `${directory}/${name}` : name;

export const store = createStore("projectFiles", {
  project: "",
  area: "workspace",
  directory: "",
  entries: [],
  editor: null,
  latest: null,
  newKind: "",
  newName: "",
  busy: false,
  error: "",

  async open(project, area = "workspace") {
    if (this.project || this.busy) return;
    this.project = project;
    this.area = area;
    this.directory = "";
    this.entries = [];
    this.editor = null;
    this.latest = null;
    this.error = "";
    this.newKind = "";
    try {
      await this.navigate("");
      await openModal(modal);
    } finally {
      this.project = "";
      this.entries = [];
      this.editor = null;
      this.latest = null;
    }
  },

  params(action, path) {
    return { action, project: this.project, area: this.area, path };
  },

  async refresh(directory = this.directory, area = this.area) {
    const result = await callJsonApi(endpoint, { ...this.params("list", directory), area });
    if (directory !== this.directory || area !== this.area) this.closeEditor();
    this.directory = directory;
    this.area = area;
    this.entries = result.entries;
  },

  navigate(directory, area = this.area) {
    return this.run(() => this.refresh(directory, area));
  },

  openEntry(entry) {
    if (entry.directory) return this.navigate(entry.path);
    return this.run(async () => {
      const file = await callJsonApi(endpoint, this.params("read", entry.path));
      this.editor = { path: entry.path, ...file };
      this.latest = null;
    });
  },

  closeEditor() {
    this.editor = null;
    this.latest = null;
  },

  beginNew(kind) {
    this.newKind = kind;
    this.newName = "";
  },

  createEntry() {
    const name = this.newName.trim();
    return this.run(async () => {
      if (!name || name.includes("/")) throw new Error("Enter a single file or folder name.");
      const path = join(this.directory, name);
      if (this.newKind === "folder") {
        await callJsonApi(endpoint, this.params("mkdir", path));
        await this.refresh();
      } else {
        this.editor = { path, content: "", revision: null };
        this.latest = null;
      }
      this.newKind = "";
    });
  },

  save() {
    return this.run(async () => {
      const { path, content, revision } = this.editor;
      const result = await callJsonApi(endpoint, { ...this.params("save", path), content, revision });
      this.editor.revision = result.revision;
      this.latest = null;
      await this.refresh();
    });
  },

  inspectLatest() {
    return this.run(async () => {
      const result = await callJsonApi(endpoint, this.params("read", this.editor.path));
      this.latest = result;
    });
  },

  useLatestRevision() {
    this.editor.revision = this.latest.revision;
    this.latest = null;
  },

  remove() {
    return this.run(async () => {
      const { path, revision } = this.editor;
      await callJsonApi(endpoint, { ...this.params("delete", path), revision });
      this.closeEditor();
      await this.refresh();
    });
  },

  upload(event) {
    const input = event.currentTarget;
    const file = input.files[0];
    if (!file) return;
    return this.run(async () => {
      const form = new FormData();
      for (const [key, value] of Object.entries(this.params("upload", join(this.directory, file.name)))) {
        form.append(key, value);
      }
      form.append("file", file);
      const response = await fetchApi(endpoint, { method: "POST", body: form });
      input.value = "";
      if (!response.ok) throw new Error(await response.text());
      await this.refresh();
    });
  },

  download(entry) {
    return this.run(async () => {
      const response = await fetchApi(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.params("download", entry.path)),
      });
      if (!response.ok) throw new Error(await response.text());
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = entry.name;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
  },

  async run(action) {
    if (this.busy) return;
    this.busy = true;
    this.error = "";
    try {
      await action();
    } catch (error) {
      this.error = error.message || "Could not access project files.";
    } finally {
      this.busy = false;
    }
  },
});
