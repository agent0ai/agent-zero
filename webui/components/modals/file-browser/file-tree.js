import { fetchApi } from "/js/api.js";

// Each host owns its tree so opening an Editor picker cannot reset it.
export function createFileTree(onOpen) {
  return {
    shown: false,
    root: null,
    selectedPath: "",
    directory: "",
    query: "",
    generation: 0,

    async toggle(path) {
      this.shown = !this.shown;
      if (this.shown) await this.follow(path);
    },

    async follow(path = "", selectedPath = path) {
      if (!this.shown) return;
      const target = path || "$WORK_DIR";
      if (this.directory === target && this.selectedPath === selectedPath && this.root) return;
      this.directory = target;
      this.selectedPath = selectedPath;
      const expanded = (node) => node?.expanded && (node.path === target || node.children?.some(expanded));
      if (expanded(this.root)) return;
      await this.loadRoot(target);
    },

    async loadRoot(path) {
      this.generation += 1;
      this.query = "";
      this.root = { path, name: path, is_dir: true, expanded: true, children: null };
      await this.load(this.root);
    },

    async load(node) {
      if (node.loading) return;
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
          node.name = node.path;
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

    get rows() {
      const query = this.query.trim().toLowerCase();
      const visit = (nodes, depth) => (nodes || []).flatMap(node => {
        const children = (node.expanded || query) ? visit(node.children, depth + 1) : [];
        if (query && !node.name.toLowerCase().includes(query) && !children.length) return [];
        return [{ node, depth }, ...children];
      });
      return visit(this.root?.children, 0);
    },
  };
}
