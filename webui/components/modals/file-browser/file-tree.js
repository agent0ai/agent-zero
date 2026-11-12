import { fetchApi } from "/js/api.js";

// Each host owns its tree so opening an Editor picker cannot reset it.
export function createFileTree(onOpen, getRootPath = () => "/a0") {
  const pendingLoads = new WeakMap();
  return {
    shown: false,
    root: null,
    selectedPath: "",
    directory: "",
    startingPath: "",
    query: "",
    generation: 0,

    async toggle(path) {
      this.shown = !this.shown;
      if (this.shown) await this.follow(path);
    },

    async follow(path = "", selectedPath = path) {
      if (!this.shown) return;
      const requested = path || "$WORK_DIR";
      const startingPath = getRootPath();
      if (this.directory === requested && this.selectedPath === selectedPath && this.startingPath === startingPath && this.root) return;
      this.directory = requested;
      this.startingPath = startingPath;
      this.selectedPath = selectedPath;
      let target = requested;
      if (!target.startsWith("/") || /^\/@ssh(?:\/|$)/.test(target)) {
        await this.loadRoot(target);
        if (this.directory !== requested || this.root.error) return;
        target = this.root.path === "/@ssh" ? "/@connections" : this.root.path;
      }
      const rootPath = /^\/@connections(?:\/|$)/.test(target) ? "/@connections" : startingPath;
      if (this.root?.path !== rootPath) await this.loadRoot(rootPath);
      const root = this.root;
      let node = root;
      while (node && this.directory === requested && this.root === root) {
        node.expanded = true;
        if (!node.children) await this.load(node);
        if (node.path === target) return;
        node = node.children?.find(child => child.is_dir &&
          (child.path === target || target.startsWith(child.path + "/")));
      }
    },

    async loadRoot(path) {
      this.generation += 1;
      this.query = "";
      this.root = { path, name: path, is_dir: true, expanded: true, children: null };
      await this.load(this.root);
    },

    load(node) {
      if (!pendingLoads.has(node)) {
        const pending = this.loadDirectory(node).finally(() => pendingLoads.delete(node));
        pendingLoads.set(node, pending);
      }
      return pendingLoads.get(node);
    },

    async loadDirectory(node) {
      const generation = this.generation;
      node.loading = true;
      node.error = "";
      try {
        const response = await fetchApi(`/get_work_dir_files?path=${encodeURIComponent(node.path)}`);
        const data = await response.json();
        if (!response.ok || data.error || data.data?.error || !data.data?.current_path) {
          throw new Error(data.error || data.data?.error || "Directory not accessible");
        }
        if (generation !== this.generation) return;
        node.children = (data.data.entries || []).map(entry => ({ ...entry, path: `/${entry.path.replace(/^\/+/, "")}`, expanded: false, children: null }))
          .sort((a, b) => Number(b.is_dir) - Number(a.is_dir) || a.name.localeCompare(b.name, undefined, { numeric: true }));
        if (node === this.root) {
          node.path = data.data.current_path;
          node.name = node.path === "/@connections" ? "Remote folders" : node.path;
          node.parentPath = data.data.parent_path;
        }
      } catch (error) {
        if (generation !== this.generation) return;
        node.error = error.message || "Could not load directory";
        globalThis.toastFrontendError?.(node.error, "File Tree");
      } finally {
        node.loading = false;
      }
    },

    async expand(node) {
      node.expanded = !node.expanded;
      if (node.expanded && !node.children) await this.load(node);
    },

    async open(node) {
      if (node.is_dir && !node.expanded) await this.expand(node);
      await onOpen(node);
    },

    scrollToSelected(element) {
      const selected = element?.querySelector(".file-tree-row.is-selected");
      if (this.shown && selected?.checkVisibility()) {
        selected.scrollIntoView({ block: "center", inline: "nearest" });
      }
    },

    get rows() {
      const query = this.query.trim().toLowerCase();
      const visit = (nodes, depth) => (nodes || []).flatMap(node => {
        const children = (node.expanded || query) ? visit(node.children, depth + 1) : [];
        if (query && !node.name.toLowerCase().includes(query) && !children.length) return [];
        return [{ node, depth }, ...children];
      });
      return visit(this.root ? [this.root] : [], 0);
    },
  };
}
