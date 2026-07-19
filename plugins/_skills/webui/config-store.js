import * as API from "/js/api.js";
import { store as markdownModalStore } from "/components/modals/markdown/markdown-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { toastFrontendError } from "/components/notifications/notification-store.js";

const CATALOG_API = "/plugins/_skills/skills_catalog";

function normalizeEntry(entry) {
  if (!entry) return null;
  if (typeof entry === "string") {
    const trimmed = entry.trim();
    if (!trimmed) return null;
    return trimmed.includes("/")
      ? { path: trimmed.replace(/\/+$/, "") }
      : { name: trimmed };
  }

  if (typeof entry !== "object") return null;
  const name = String(entry.name || "").trim();
  const path = String(entry.path || "").trim().replace(/\/+$/, "");
  if (!name && !path) return null;
  return {
    ...(name ? { name } : {}),
    ...(path ? { path } : {}),
  };
}

function entryKey(entry) {
  if (!entry) return "";
  return String(entry.path || entry.name || "").trim().toLowerCase();
}

function entryKeys(entry) {
  return [entry?.path, entry?.name]
    .map((value) => String(value || "").trim().toLowerCase())
    .filter(Boolean);
}

function entriesMatch(left, right) {
  const rightKeys = new Set(entryKeys(right));
  if (rightKeys.size === 0) return false;
  return entryKeys(left).some((key) => rightKeys.has(key));
}

function ensureConfig(config) {
  if (!config || typeof config !== "object") return;
  const hiddenSkills = Array.isArray(config.hidden_skills) ? config.hidden_skills : [];

  config.hidden_skills = compactEntries(hiddenSkills);
}

function compactEntries(entries, limit = null) {
  const normalized = [];
  const seen = new Set();

  for (const item of entries || []) {
    const entry = normalizeEntry(item);
    const key = entryKey(entry);
    if (!entry || !key || seen.has(key)) continue;
    seen.add(key);
    normalized.push({
      ...(entry.name ? { name: entry.name } : {}),
      ...(entry.path ? { path: entry.path } : {}),
    });
    if (limit !== null && normalized.length >= limit) break;
  }

  return normalized;
}

window.createSkillsConfigModel = (context, config) => ({
  loadingCatalog: false,
  mutatingChat: false,
  catalog: [],
  search: "",
  selectedSkills: [],
  hiddenSkills: [],
  chatContextAvailable: false,

  initDefaults() {
    ensureConfig(config);
    this.selectedSkills = [];
    this.hiddenSkills = [...this.hiddenEntries];
  },

  get isChatMode() {
    return context?.openOptions?.focus === "chat";
  },

  get hiddenEntries() {
    ensureConfig(config);
    return config.hidden_skills;
  },

  get catalogMap() {
    const byKey = new Map();
    for (const skill of this.catalog) {
      byKey.set(entryKey(skill), skill);
      if (skill.name) {
        byKey.set(String(skill.name).trim().toLowerCase(), skill);
      }
    }
    return byKey;
  },

  get filteredCatalog() {
    const query = this.search.trim().toLowerCase();
    if (!query) return this.catalog;

    return this.catalog.filter((skill) => {
      const haystack = [
        skill.name,
        skill.description,
        skill.path,
        skill.origin,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  },

  entryKey(entry) {
    return entryKey(entry);
  },

  pinnedSubtitle() {
    return "These skills are loaded into the current chat history.";
  },

  allSkillsSubtitle() {
    return this.isChatMode
      ? "Check a skill to load it into this chat. Use the eye control to hide or show it in this chat."
      : "Check a skill to load it into the current chat. Use the eye control to hide or show it in this scope.";
  },

  hiddenStateLabel() {
    return this.isChatMode ? "Hidden in this chat" : "Hidden by default";
  },

  visibilityButtonTitle(skill) {
    if (this.isHidden(skill)) {
      return this.isChatMode ? "Show in this chat" : "Show by default";
    }
    return this.isChatMode ? "Hide in this chat" : "Hide by default";
  },

  visibilityButtonIcon(skill) {
    return this.isHidden(skill) ? "visibility_off" : "visibility";
  },

  isHidden(skill) {
    return this.hiddenSkills.some((entry) => entriesMatch(entry, skill));
  },

  isSelected(skill) {
    return this.selectedSkills.some((entry) => entriesMatch(entry, skill));
  },

  isPinDisabled(skill) {
    return this.mutatingChat || !this.chatContextAvailable || this.isSelected(skill);
  },

  isVisibilityDisabled() {
    return this.mutatingChat || (this.isChatMode && !this.chatContextAvailable);
  },

  isEntryMissing(entry) {
    const key = entryKey(entry);
    if (!key) return false;
    if (this.catalogMap.has(key)) return false;
    if (entry.name && this.catalogMap.has(String(entry.name).trim().toLowerCase())) return false;
    return true;
  },

  labelForEntry(entry) {
    const skill = this._resolveEntry(entry);
    if (skill?.name) return skill.name;
    return entry?.name || "(unnamed skill)";
  },

  secondaryLabelForEntry(entry) {
    const skill = this._resolveEntry(entry);
    if (skill) return `${skill.origin} | ${skill.path}`;
    if (entry?.path) return `Not visible in the current list | ${entry.path}`;
    return "Not visible in the current list";
  },

  _resolveEntry(entry) {
    const key = entryKey(entry);
    if (key && this.catalogMap.has(key)) {
      return this.catalogMap.get(key);
    }
    const name = String(entry?.name || "").trim().toLowerCase();
    return name ? this.catalogMap.get(name) || null : null;
  },

  _setSelectedSkills(entries) {
    const normalized = [];
    const seen = new Set();

    for (const entry of entries) {
      const item = normalizeEntry(entry);
      const key = entryKey(item);
      if (!item || !key || seen.has(key)) continue;
      seen.add(key);
      normalized.push(item);
    }

    this.selectedSkills = normalized;
  },

  _setHiddenSkills(entries, { writeConfig = true } = {}) {
    const normalized = compactEntries(entries);
    this.hiddenSkills = normalized;
    if (writeConfig) {
      config.hidden_skills = normalized;
    }
  },

  async toggleSkillVisibility(skill, selected) {
    const previous = [...this.hiddenSkills];
    const nextEntries = this.hiddenSkills.filter((entry) => !entriesMatch(entry, skill));

    if (!selected) {
      nextEntries.push({
        name: String(skill.name || "").trim(),
        path: String(skill.path || "").trim(),
      });
    }

    this._setHiddenSkills(nextEntries, { writeConfig: !this.isChatMode });

    if (this.isChatMode && this.chatContextAvailable) {
      const ok = await this.submitChatAction(selected ? "show" : "hide", skill);
      if (!ok) {
        this._setHiddenSkills(previous, { writeConfig: false });
      }
    }
  },

  async toggleVisibility(skill) {
    await this.toggleSkillVisibility(skill, this.isHidden(skill));
  },

  async togglePinnedSkill(skill, selected) {
    if (!selected || this.isSelected(skill)) {
      await this.loadCatalog();
      return;
    }

    if (!this.chatContextAvailable) {
      await toastFrontendError("Open a chat before loading a skill.", "Skills");
      await this.loadCatalog();
      return;
    }

    await this.submitChatAction("activate", skill);
  },

  applyCatalogState(response) {
    this.chatContextAvailable = !!response?.context_available;
    const activeFromChat = Array.isArray(response?.active_skills) ? response.active_skills : null;
    const hiddenFromChat = Array.isArray(response?.hidden_skills) ? response.hidden_skills : null;
    const hiddenFromConfig = this.hiddenEntries;

    this._setSelectedSkills(
      activeFromChat || [],
    );
    this._setHiddenSkills(
      this.isChatMode ? hiddenFromChat || [] : hiddenFromConfig,
      { writeConfig: !this.isChatMode },
    );
  },

  async loadCatalog() {
    this.loadingCatalog = true;
    try {
      const response = await API.callJsonApi(CATALOG_API, {
        action: "list",
        project_name: context.projectName || "",
        context_id: chatsStore.selectedContext?.id || "",
      });

      if (!response?.ok) {
        throw new Error(response?.error || "Failed to load skills");
      }

      this.catalog = Array.isArray(response.skills) ? response.skills : [];
      this.applyCatalogState(response);
    } catch (error) {
      this.catalog = [];
      ensureConfig(config);
      this.chatContextAvailable = false;
      this._setSelectedSkills([]);
      this._setHiddenSkills(this.hiddenEntries);
      await toastFrontendError(error?.message || "Failed to load skills", "Skills");
    } finally {
      this.loadingCatalog = false;
    }
  },

  async submitChatAction(action, skill = null) {
    this.mutatingChat = true;
    try {
      const response = await API.callJsonApi(CATALOG_API, {
        action,
        context_id: chatsStore.selectedContext?.id || "",
        project_name: context.projectName || "",
        ...(skill
          ? {
              skill: {
                name: String(skill.name || "").trim(),
                path: String(skill.path || "").trim(),
              },
            }
          : {}),
      });

      if (!response?.ok) {
        throw new Error(response?.error || "Failed to update skills");
      }

      this.catalog = Array.isArray(response.skills) ? response.skills : this.catalog;
      this.chatContextAvailable = !!response.context_available;
      this.applyCatalogState(response);
      return true;
    } catch (error) {
      await toastFrontendError(error?.message || "Failed to update skills", "Skills");
      return false;
    } finally {
      this.mutatingChat = false;
    }
  },

  async openSkill(skill) {
    try {
      const response = await API.callJsonApi(CATALOG_API, {
        action: "get_doc",
        context_id: chatsStore.selectedContext?.id || "",
        project_name: context.projectName || "",
        skill: {
          name: String(skill?.name || "").trim(),
          path: String(skill?.path || "").trim(),
        },
      });

      if (!response?.ok) {
        throw new Error(response?.error || "Failed to open skill");
      }
      if (!markdownModalStore?.open) {
        throw new Error("Markdown viewer is unavailable");
      }

      markdownModalStore.open(response.filename || "SKILL.md", response.content || "", {
        viewer: "ace",
      });
      window.openModal?.("components/modals/markdown/markdown-modal.html");
    } catch (error) {
      await toastFrontendError(error?.message || "Failed to open skill", "Skills");
    }
  },
});

export {};
