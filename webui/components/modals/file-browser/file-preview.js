import { fetchApi } from "/js/api.js";

export function mediaKind(file) {
  if (!file || file.is_dir) return "";
  const ext = file.name.split(".").pop().toLowerCase();
  if (["bmp", "gif", "ico", "jpg", "jpeg", "png", "webp", "avif"].includes(ext)) return "image";
  if (["mp3", "ogg", "wav", "flac", "m4a", "opus"].includes(ext)) return "audio";
  if (["mp4", "m4v", "webm", "mov"].includes(ext)) return "video";
  return "";
}

export function mediaPreview() {
  return {
    items: [], index: 0, url: "", error: "", originalSize: false, request: null,
    get file() { return this.items[this.index]; },
    get kind() { return mediaKind(this.file); },
    async show(file, entries) {
      this.items = entries.filter(entry => mediaKind(entry) && this.fb.remoteAllowed("download", entry));
      this.index = this.items.findIndex(entry => entry.path === file.path);
      if (this.index < 0) { this.items = [file]; this.index = 0; }
      this.$el.showModal();
      await this.load();
    },
    async step(delta) {
      this.index = (this.index + delta + this.items.length) % this.items.length;
      await this.load();
    },
    clear() {
      this.request?.abort();
      if (this.url) URL.revokeObjectURL(this.url);
      this.url = "";
      this.originalSize = false;
      this.error = "";
    },
    async load() {
      this.clear();
      const request = this.request = new AbortController();
      try {
        const prepared = await fetchApi("/download_work_dir_files", {
          method: "POST", headers: { "Content-Type": "application/json" }, signal: request.signal,
          body: JSON.stringify({ paths: [this.file.path], currentPath: this.fb.browser.currentPath }),
        });
        const result = await prepared.json();
        if (!prepared.ok || !result.download_url) throw new Error(result.error || "Preview unavailable.");
        const response = await fetchApi(result.download_url, { signal: request.signal });
        if (!response.ok) throw new Error("Could not read this file.");
        const blob = await response.blob();
        if (!request.signal.aborted) this.url = URL.createObjectURL(blob);
      } catch (error) {
        if (!request.signal.aborted) this.error = error.message;
      }
    },
    destroy() { this.clear(); },
  };
}
