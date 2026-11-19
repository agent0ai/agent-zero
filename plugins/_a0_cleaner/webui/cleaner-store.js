import { createStore } from '/js/AlpineStore.js';
import { callJsonApi } from '/js/api.js';
import { store as schedulerStore } from '/plugins/_scheduler/webui/scheduler/scheduler-store.js';

const model = {
  report: null, activity: [], scheduled: null, schedule: null, config: null,
  selected: [], tab: 'overview', busy: false, operation: '', externalBusy: false,
  preview: null, folderPath: '', folderDays: 30, mounted: false, _timer: null, _generation: 0,

  async api(action, data = {}) {
    const response = await callJsonApi('/plugins/_a0_cleaner/cleaner', { action, ...data });
    if (!response?.ok) throw new Error(response?.error || 'A0Cleaner could not complete this action.');
    return response;
  },
  toast(message, type = 'error') { globalThis.justToast?.(message, type, 5000, 'a0-cleaner'); },
  bytes(value = 0) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB']; let i = 0;
    while (value >= 1024 && i < units.length - 1) { value /= 1024; i++; }
    return `${value.toLocaleString(undefined, { maximumFractionDigits: i ? 1 : 0 })} ${units[i]}`;
  },
  date(stamp) { return stamp ? new Date(typeof stamp === 'number' ? stamp * 1000 : stamp).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : 'Not run yet'; },
  fileCount(count = 0) { return `${count.toLocaleString()} ${count === 1 ? 'file' : 'files'}`; },
  groups(automatic = null) { return (this.report?.groups || []).filter(g => g.kind !== 'custom' && (automatic === null || g.auto_supported === automatic)); },
  customGroups() { return (this.report?.groups || []).filter(g => g.kind === 'custom'); },
  selectedBytes() { return (this.report?.groups || []).filter(g => this.selected.includes(g.id)).reduce((sum, g) => sum + g.bytes, 0); },
  selectedFiles() { return (this.report?.groups || []).filter(g => this.selected.includes(g.id)).reduce((sum, g) => sum + g.files, 0); },
  disabled() { return this.busy || this.externalBusy; },
  diskPercent() { return this.report?.disk?.total ? Math.round(this.report.disk.used / this.report.disk.total * 100) : 0; },
  applyReport(report) {
    if (!report || this.report?.id === report.id || (this.report && report.at < this.report.at)) return;
    this.report = report;
    this.selected = report.groups.filter(g => g.automatic && g.files && !g.blocked).map(g => g.id);
    this.preview = null;
  },
  async mount() {
    this.mounted = true; const generation = ++this._generation;
    try {
      await this.refresh();
      if (this.mounted && generation === this._generation && !this.externalBusy && (!this.report || Date.now()/1000-this.report.at > 3600)) await this.scan();
    } catch (error) { this.toast(error.message); }
    this.poll();
  },
  unmount() { this.mounted = false; ++this._generation; clearTimeout(this._timer); this._timer = null; },
  poll() {
    clearTimeout(this._timer);
    if (!this.mounted) return;
    this._timer = setTimeout(async () => {
      if (!this.busy) { try { await this.refresh(); } catch (error) { console.warn('A0Cleaner status:', error.message); } }
      this.poll();
    }, this.externalBusy ? 2000 : 15000);
  },
  async refresh() {
    const generation = this._generation;
    const state = await this.api('status');
    if (generation !== this._generation) return;
    this.applyReport(state.report); this.activity = state.activity; this.scheduled = state.scheduled;
    this.schedule = state.schedule; this.config = state.config;
    this.externalBusy = Boolean(state.status?.operation);
    if (!this.busy) this.operation = state.status?.operation || '';
  },
  async perform(label, action) {
    if (this.disabled()) return;
    this.busy = true; this.operation = label;
    try { await action(); } catch (error) { this.toast(error.message); }
    finally { this.busy = false; this.operation = ''; }
  },
  async scan() {
    await this.perform('Scanning', async () => {
      const result = await this.api('scan'); this.applyReport(result.report); await this.refresh();
    });
  },
  async review() {
    if (!this.selectedFiles()) return;
    await this.perform('Preparing cleanup', async () => {
      const response = await this.api('preview', { scan_id: this.report.id, groups: [...this.selected] });
      this.preview = response.preview;
    });
  },
  async clean() {
    const preview = this.preview;
    if (!preview) return;
    await this.perform('Cleaning', async () => {
      const response = await this.api('clean', { scan_id: preview.id, groups: preview.groups.map(g => g.id), confirmed: true });
      this.preview = null; this.applyReport(response.report); await this.refresh();
      this.toast(`${this.bytes(response.result.bytes)} cleaned${response.result.skipped ? ` · ${response.result.skipped} files skipped` : ''}`, 'success');
    });
  },
  async saveConfig(config) {
    const response = await this.api('settings', { settings: config }); this.config = response.config;
    this.preview = null; this.selected = [];
    const scan = await this.api('scan'); this.applyReport(scan.report);
  },
  async automaticChanged(value) {
    await this.perform('Saving', async () => { await this.saveConfig({ ...this.config, automatic: value }); });
  },
  async automaticAreaChanged(id, enabled) {
    await this.perform('Saving', async () => {
      const areas = this.config.automatic_areas.filter(area => area !== id);
      if (enabled) areas.push(id);
      await this.saveConfig({ ...this.config, automatic_areas: areas });
    });
  },
  async setAge(key, raw) {
    await this.perform('Saving', async () => { await this.saveConfig({ ...this.config, [key]: Number(raw) }); });
  },
  async addFolder() {
    await this.perform('Adding folder', async () => {
      await this.saveConfig({ ...this.config, custom_folders: [...this.config.custom_folders, { path: this.folderPath.trim(), days: Number(this.folderDays) }] });
      this.folderPath = '';
    });
  },
  async removeFolder(index) {
    await this.perform('Removing folder', async () => {
      await this.saveConfig({ ...this.config, custom_folders: this.config.custom_folders.filter((_, i) => i !== index) });
    });
  },
  async changeSchedule(cadence) {
    await this.perform('Saving schedule', async () => { this.schedule = (await this.api('schedule', { cadence })).schedule; });
  },
  async openSchedule() {
    if (this.schedule?.task?.uuid) {
      await schedulerStore.fetchTasks();
      schedulerStore.showTaskDetail(this.schedule.task.uuid);
    }
  },
  closePreview() {
    if (this.busy) return;
    this.preview = null;
    globalThis.document?.querySelector('.a0c-clean')?.focus();
  },
  trapFocus(event) {
    const buttons = [...event.currentTarget.querySelectorAll('button:not(:disabled), summary')];
    if (!buttons.length) return;
    const index = buttons.indexOf(globalThis.document.activeElement);
    buttons[(index + (event.shiftKey ? -1 : 1) + buttons.length) % buttons.length].focus();
  },
};
export const store = createStore('a0Cleaner', model);
