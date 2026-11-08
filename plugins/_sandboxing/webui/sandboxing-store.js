import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import {
  toastFrontendError,
  toastFrontendSuccess,
} from "/components/notifications/notification-store.js";

const API_PATH = "/plugins/_sandboxing/sandboxes";

const model = {
  sandboxes: [],
  images: [],
  diagnostics: [],
  sharedDir: "",
  defaults: { name: "default", sandbox_type: "temporary", network: "host", image: "" },
  imageCleanupDays: 30,
  loading: false,
  busy: false,
  busyNames: {},
  busyImages: {},
  pollTimer: null,
  formInitialized: false,
  form: { name: "", sandbox_type: "temporary", network: "host", image: "" },
  imageForm: { reference: "" },

  async onOpen() {
    await this.refresh();
    this.pollTimer = globalThis.setInterval(() => {
      if (!this.busy) this.refresh(true);
    }, 5000);
  },

  onClose() {
    if (this.pollTimer) globalThis.clearInterval(this.pollTimer);
    this.pollTimer = null;
  },

  async refresh(silent = false) {
    if (!silent) this.loading = true;
    try {
      const response = await callJsonApi(API_PATH, { action: "list" });
      if (!response?.ok) throw new Error(response?.error || "Could not list sandboxes.");
      this.sandboxes = Array.isArray(response.sandboxes) ? response.sandboxes : [];
      this.images = Array.isArray(response.images) ? response.images : [];
      this.sharedDir = response.shared_dir || "";
      this.defaults = response.defaults || this.defaults;
      this.imageCleanupDays = Number(response.image_cleanup_days || 30);
      if (!this.formInitialized) {
        this.form.sandbox_type = this.defaults.sandbox_type || "temporary";
        this.form.network = this.defaults.network || "host";
        this.form.image = this.defaults.image || "";
        this.formInitialized = true;
      }
      if (!this.imageForm.reference) this.imageForm.reference = this.defaults.image || "";
    } catch (error) {
      if (!silent) toastFrontendError(error?.message || "Could not list sandboxes.");
    } finally {
      if (!silent) this.loading = false;
    }
  },

  async doctor() {
    this.busy = true;
    try {
      const response = await callJsonApi(API_PATH, { action: "doctor" });
      this.diagnostics = Array.isArray(response?.diagnostics) ? response.diagnostics : [];
      if (response?.ok) toastFrontendSuccess("Sandbox runtime checks passed.");
      else toastFrontendError("Sandbox runtime needs attention. Review the diagnostics.");
    } catch (error) {
      toastFrontendError(error?.message || "Sandbox doctor failed.");
    } finally {
      this.busy = false;
    }
  },

  async createSandbox() {
    const name = this.form.name.trim();
    if (!name) return;
    this.busy = true;
    try {
      const response = await callJsonApi(API_PATH, {
        action: "create",
        name,
        sandbox_type: this.form.sandbox_type,
        network: this.form.network,
        image: this.form.image || this.defaults.image,
      });
      if (!response?.ok) throw new Error(response?.error || "Could not create sandbox.");
      this.form.name = "";
      toastFrontendSuccess(`Sandbox ${name} created.`);
      await this.refresh(true);
    } catch (error) {
      toastFrontendError(error?.message || "Could not create sandbox.");
    } finally {
      this.busy = false;
    }
  },

  async perform(action, sandbox) {
    const name = sandbox?.name || "";
    if (!name || this.isBusy(name)) return;
    this.busyNames[name] = true;
    try {
      const response = await callJsonApi(API_PATH, {
        action,
        name,
        confirm: action === "delete",
      });
      if (!response?.ok) throw new Error(response?.error || `Could not ${action} sandbox.`);
      const completed = { start: "started", stop: "stopped", save: "saved", delete: "deleted" }[action] || action;
      toastFrontendSuccess(`Sandbox ${name} ${completed}.`);
      await this.refresh(true);
    } catch (error) {
      toastFrontendError(error?.message || `Could not ${action} sandbox.`);
    } finally {
      delete this.busyNames[name];
    }
  },

  async pullImage() {
    const reference = this.imageForm.reference.trim();
    if (!reference || this.busy) return;
    this.busy = true;
    try {
      const response = await callJsonApi(API_PATH, {
        action: "pull_image",
        image: reference,
      });
      if (!response?.ok) throw new Error(response?.error || "Could not pull image.");
      toastFrontendSuccess(`Image ${reference} is ready.`);
      await this.refresh(true);
    } catch (error) {
      toastFrontendError(error?.message || "Could not pull image.");
    } finally {
      this.busy = false;
    }
  },

  async deleteImage(image) {
    const digest = image?.digest || "";
    if (!digest || this.busyImages[digest]) return;
    this.busyImages[digest] = true;
    try {
      const response = await callJsonApi(API_PATH, {
        action: "delete_image",
        digest,
        confirm: true,
      });
      if (!response?.ok) throw new Error(response?.error || "Could not delete image.");
      toastFrontendSuccess(`Image ${this.shortDigest(digest)} deleted.`);
      await this.refresh(true);
    } catch (error) {
      toastFrontendError(error?.message || "Could not delete image.");
    } finally {
      delete this.busyImages[digest];
    }
  },

  async cleanupImages() {
    if (this.busy) return;
    this.busy = true;
    try {
      const response = await callJsonApi(API_PATH, { action: "cleanup_images" });
      if (!response?.ok) throw new Error(response?.error || "Image cleanup failed.");
      const count = Array.isArray(response.deleted_images) ? response.deleted_images.length : 0;
      toastFrontendSuccess(`Removed ${count} unused image${count === 1 ? "" : "s"}.`);
      await this.refresh(true);
    } catch (error) {
      toastFrontendError(error?.message || "Image cleanup failed.");
    } finally {
      this.busy = false;
    }
  },

  isBusy(name) {
    return Boolean(this.busyNames[name]);
  },

  shortDigest(digest) {
    const value = String(digest || "");
    return value.length > 22 ? `${value.slice(0, 19)}…` : value;
  },

  formatSize(bytes) {
    let value = Number(bytes || 0);
    const units = ["B", "KiB", "MiB", "GiB", "TiB"];
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value /= 1024;
      unit += 1;
    }
    return unit === 0 ? `${Math.round(value)} B` : `${value.toFixed(1)} ${units[unit]}`;
  },

  formatDate(value) {
    if (!value) return "Not yet";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  },
};

export const store = createStore("sandboxingStore", model);
