import { createStore } from "/js/AlpineStore.js";

const model = {
  loading: false,
  sending: false,
  drafts: [],
  inbound: [],
  toNumber: "",
  body: "",
  autoSend: false,
  showThread: false,
  selectedThread: null,
  shortcutsEnabled: true,
  _shortcutsBound: false,
  _shortcutsHandler: null,
  newContact: "",
  tagFilter: "",
  tagPresets: [],
  newPresetName: "",

  async init() {
    this.loadAutoSend();
    this.loadShortcuts();
    this.loadTagPresets();
    await this.refresh();
    await this.loadInbound();
    this.registerShortcuts();
  },

  loadAutoSend() {
    const fields = this._getSettingsFields();
    const field = fields.find((entry) => entry.id === "google_voice_auto_send");
    if (field) {
      this.autoSend = Boolean(field.value);
    }
  },

  updateField(id, value) {
    const field = this._getSettingsFields().find((entry) => entry.id === id);
    if (field) {
      field.value = value;
    }
  },

  toggleAutoSend(value) {
    this.autoSend = Boolean(value);
    this.updateField("google_voice_auto_send", this.autoSend);
  },

  loadShortcuts() {
    const fields = this._getSettingsFields();
    const field = fields.find((entry) => entry.id === "google_voice_shortcuts");
    if (field) {
      this.shortcutsEnabled = Boolean(field.value);
    }
  },

  loadTagPresets() {
    const fields = this._getSettingsFields();
    const field = fields.find((entry) => entry.id === "google_voice_tag_filters");
    if (field) {
      try {
        this.tagPresets = JSON.parse(field.value || "[]");
      } catch (error) {
        this.tagPresets = [];
      }
    }
  },

  saveTagPresets() {
    const fields = this._getSettingsFields();
    const field = fields.find((entry) => entry.id === "google_voice_tag_filters");
    if (field) {
      field.value = JSON.stringify(this.tagPresets, null, 2);
    }
  },

  toggleShortcuts(value) {
    this.shortcutsEnabled = Boolean(value);
    this.updateField("google_voice_shortcuts", this.shortcutsEnabled);
    if (this.shortcutsEnabled) {
      this.registerShortcuts();
    } else {
      this.unregisterShortcuts();
    }
  },

  registerShortcuts() {
    if (this._shortcutsBound) {
      return;
    }
    this._shortcutsHandler = (event) => {
      if (!this.shortcutsEnabled) {
        return;
      }
      if (event.target && ["INPUT", "TEXTAREA"].includes(event.target.tagName)) {
        return;
      }
      if (event.key === "a") {
        const draft = this.drafts.find((item) => item.status === "draft");
        if (draft) {
          event.preventDefault();
          this.approveDraft(draft.id);
        }
      }
      if (event.key === "A" && event.shiftKey) {
        event.preventDefault();
        this.approveAllDrafts();
      }
      if (event.key === "r") {
        const inbound = this.inbound[0];
        if (inbound) {
          event.preventDefault();
          this.openThread(inbound);
        }
      }
      if (event.key === "Escape" && this.showThread) {
        event.preventDefault();
        this.closeThread();
      }
    };
    window.addEventListener("keydown", this._shortcutsHandler);
    this._shortcutsBound = true;
  },

  unregisterShortcuts() {
    if (this._shortcutsHandler) {
      window.removeEventListener("keydown", this._shortcutsHandler);
    }
    this._shortcutsBound = false;
  },

  async refresh() {
    this.loading = true;
    try {
      const token = Alpine.store("csrfStore")?.token || "";
      const response = await fetch("/google_voice_outbound_list", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
        body: JSON.stringify({}),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Failed to load drafts");
      }
      this.drafts = data.messages || [];
    } catch (error) {
      console.error("Google Voice drafts load failed:", error);
      window.toastFrontendError?.("Failed to load Google Voice drafts", "Google Voice");
    } finally {
      this.loading = false;
    }
  },

  async loadInbound() {
    try {
      const token = Alpine.store("csrfStore")?.token || "";
      const response = await fetch("/google_voice_inbound_list", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
        body: JSON.stringify({ limit: 50 }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Failed to load inbound");
      }
      this.inbound = data.messages || [];
    } catch (error) {
      console.error("Google Voice inbound load failed:", error);
      window.toastFrontendError?.("Failed to load inbound SMS", "Google Voice");
    }
  },

  filteredInbound() {
    const filter = (this.tagFilter || "").trim().toLowerCase();
    if (!filter) {
      return this.inbound;
    }
    const rules = this.getContactRules();
    return this.inbound.filter((item) => {
      const rule = this._normalizeRule(rules[item.from_number]);
      return rule.tags.some((tag) => tag.toLowerCase().includes(filter));
    });
  },

  addTagPreset() {
    const name = (this.newPresetName || "").trim();
    const tag = (this.tagFilter || "").trim();
    if (!name || !tag) {
      window.toastFrontendError?.("Preset name and tag are required", "Google Voice");
      return;
    }
    this.tagPresets.push({ name, tag });
    this.saveTagPresets();
    this.newPresetName = "";
  },

  applyTagPreset(preset) {
    if (preset && preset.tag) {
      this.tagFilter = preset.tag;
    }
  },

  removeTagPreset(index) {
    if (index < 0 || index >= this.tagPresets.length) {
      return;
    }
    this.tagPresets.splice(index, 1);
    this.saveTagPresets();
  },

  async createReplyDraft(item) {
    const replyText = (item.replyText || "").trim();
    if (!replyText) {
      window.toastFrontendError?.("Reply message is required", "Google Voice");
      return;
    }
    this.sending = true;
    try {
      const token = Alpine.store("csrfStore")?.token || "";
      const response = await fetch("/google_voice_outbound_create", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
        body: JSON.stringify({
          to_number: item.from_number,
          body: replyText,
          auto_send: this.isAutoSendContact(item.from_number),
        }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Reply draft failed");
      }
      item.replyText = "";
      await this.refresh();
      window.toastFrontendInfo?.("Reply draft created", "Google Voice");
    } catch (error) {
      console.error("Reply draft failed:", error);
      window.toastFrontendError?.("Failed to create reply draft", "Google Voice");
    } finally {
      this.sending = false;
    }
  },

  async createReplyAndApprove(item) {
  async createReplyAndApprove(item) {
    const replyText = (item.replyText || "").trim();
    if (!replyText) {
      window.toastFrontendError?.("Reply message is required", "Google Voice");
      return;
    }
    this.sending = true;
    try {
      const token = Alpine.store("csrfStore")?.token || "";
      const response = await fetch("/google_voice_outbound_create", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
        body: JSON.stringify({
          to_number: item.from_number,
          body: replyText,
          force_manual: true,
        }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Reply draft failed");
      }
      item.replyText = "";
      await this.approveDraft(data.message.id);
      this.scrollToDrafts();
    } catch (error) {
      console.error("Reply & approve failed:", error);
      window.toastFrontendError?.("Failed to reply & approve", "Google Voice");
    } finally {
      this.sending = false;
    }
  },

  async approveAllDrafts() {
    const drafts = this.drafts.filter((item) => item.status === "draft");
    if (drafts.length === 0) {
      window.toastFrontendInfo?.("No drafts to approve", "Google Voice");
      return;
    }
    this.sending = true;
    try {
      for (const draft of drafts) {
        await this.approveDraft(draft.id);
      }
      await this.refresh();
      window.toastFrontendInfo?.("All drafts approved", "Google Voice");
    } catch (error) {
      console.error("Bulk approve failed:", error);
      window.toastFrontendError?.("Bulk approve failed", "Google Voice");
    } finally {
      this.sending = false;
    }
  },

  scrollToDrafts() {
    const target = document.getElementById("google-voice-drafts");
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  },

  openThread(item) {
    this.selectedThread = item;
    this.showThread = true;
  },

  closeThread() {
    this.showThread = false;
    this.selectedThread = null;
  },

  getContactRules() {
    const fields = this._getSettingsFields();
    const field = fields.find((entry) => entry.id === "google_voice_contact_rules");
    if (!field || !field.value) {
      return {};
    }
    try {
      return JSON.parse(field.value);
    } catch (error) {
      return {};
    }
  },

  saveContactRules(rules) {
    const fields = this._getSettingsFields();
    const field = fields.find((entry) => entry.id === "google_voice_contact_rules");
    if (field) {
      field.value = JSON.stringify(rules, null, 2);
    }
  },

  _normalizeRule(rule) {
    if (!rule) {
      return { auto_send: true, notes: "", tags: [] };
    }
    if (typeof rule === "boolean") {
      return { auto_send: rule, notes: "", tags: [] };
    }
    return {
      auto_send: Boolean(rule.auto_send),
      notes: rule.notes || "",
      tags: Array.isArray(rule.tags) ? rule.tags : [],
    };
  },

  isAutoSendContact(number) {
    const rules = this.getContactRules();
    const rule = this._normalizeRule(rules[number]);
    return Boolean(rule.auto_send);
  },

  toggleContactAutoSend(number) {
    const rules = this.getContactRules();
    const rule = this._normalizeRule(rules[number]);
    rule.auto_send = !rule.auto_send;
    rules[number] = rule;
    this.saveContactRules(rules);
  },

  addContactRule(number) {
    const value = (number || "").trim();
    if (!value) {
      return;
    }
    const rules = this.getContactRules();
    rules[value] = this._normalizeRule(rules[value] || true);
    this.saveContactRules(rules);
    this.newContact = "";
  },

  removeContactRule(number) {
    const rules = this.getContactRules();
    if (rules[number]) {
      delete rules[number];
      this.saveContactRules(rules);
    }
  },

  updateContactNotes(number, notes) {
    const rules = this.getContactRules();
    const rule = this._normalizeRule(rules[number]);
    rule.notes = notes || "";
    rules[number] = rule;
    this.saveContactRules(rules);
  },

  updateContactTags(number, tagsValue) {
    const rules = this.getContactRules();
    const rule = this._normalizeRule(rules[number]);
    const tags = String(tagsValue || "")
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
    rule.tags = tags;
    rules[number] = rule;
    this.saveContactRules(rules);
  },

  async syncInbound() {
    this.loading = true;
    try {
      const token = Alpine.store("csrfStore")?.token || "";
      const response = await fetch("/google_voice_inbound_sync", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
        body: JSON.stringify({ limit: 10 }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Inbound sync failed");
      }
      await this.loadInbound();
      window.toastFrontendInfo?.("Inbound SMS synced", "Google Voice");
    } catch (error) {
      console.error("Google Voice inbound sync failed:", error);
      window.toastFrontendError?.("Failed to sync inbound SMS", "Google Voice");
    } finally {
      this.loading = false;
    }
  },

  async startSession() {
    this.sending = true;
    try {
      const token = Alpine.store("csrfStore")?.token || "";
      const response = await fetch("/google_voice_session_start", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
        body: JSON.stringify({}),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Session start failed");
      }
      window.toastFrontendInfo?.("Google Voice session started", "Google Voice");
    } catch (error) {
      console.error("Google Voice session start failed:", error);
      window.toastFrontendError?.("Failed to start Google Voice session", "Google Voice");
    } finally {
      this.sending = false;
    }
  },

  async createDraft() {
    if (!this.toNumber || !this.body) {
      window.toastFrontendError?.("Phone number and message are required", "Google Voice");
      return;
    }
    this.sending = true;
    try {
      const token = Alpine.store("csrfStore")?.token || "";
      const response = await fetch("/google_voice_outbound_create", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
        body: JSON.stringify({ to_number: this.toNumber, body: this.body }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Draft creation failed");
      }
      this.toNumber = "";
      this.body = "";
      await this.refresh();
      window.toastFrontendInfo?.("Draft queued for approval", "Google Voice");
    } catch (error) {
      console.error("Google Voice draft failed:", error);
      window.toastFrontendError?.("Failed to create draft", "Google Voice");
    } finally {
      this.sending = false;
    }
  },

  async approveDraft(messageId) {
    this.sending = true;
    try {
      const token = Alpine.store("csrfStore")?.token || "";
      const response = await fetch("/google_voice_outbound_approve", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
        body: JSON.stringify({ message_id: messageId }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "Send failed");
      }
      await this.refresh();
      window.toastFrontendInfo?.("Message sent via Google Voice", "Google Voice");
    } catch (error) {
      console.error("Google Voice send failed:", error);
      window.toastFrontendError?.("Failed to send via Google Voice", "Google Voice");
    } finally {
      this.sending = false;
    }
  },

  _getSettingsFields() {
    try {
      return settingsModalProxy.settings.sections.flatMap((section) => section.fields);
    } catch (error) {
      return [];
    }
  },
};

const store = createStore("googleVoiceManager", model);

export { store };
