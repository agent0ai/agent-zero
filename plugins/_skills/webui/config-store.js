import * as API from "/js/api.js";
import { store as markdownModalStore } from "/components/modals/markdown/markdown-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import {
  toastFrontendError,
  toastFrontendInfo,
} from "/components/notifications/notification-store.js";

const CATALOG_API = "/plugins/_skills/skills_catalog";
const MAX_ACTIVE_SKILLS_FALLBACK = 20;

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

function ensureConfig(config) {
  if (!config || typeof config !== "object") return;
  const activeSkills = Array.isArray(config.active_skills) ? config.active_skills : [];
  const normalized = [];
  const seen = new Set();

  for (const item of activeSkills) {
    const entry = normalizeEntry(item);
    const key = entryKey(entry);
    if (!entry || !key || seen.has(key)) continue;
    seen.add(key);
    normalized.push(entry);
  }

  config.active_skills = normalized;
}

function compactEntries(entries) {
  return entries
    .map((entry) => normalizeEntry(entry))
    .filter(Boolean)
    .map((entry) => ({
      ...(entry.name ? { name: entry.name } : {}),
      ...(entry.path ? { path: entry.path } : {}),
    }));
}

window.createSkillsConfigModel = (context, config) => ({
  loadingCatalog: false,
  mutatingChat: false,
  catalog: [],
  search: "",
  maxActiveSkills: MAX_ACTIVE_SKILLS_FALLBACK,
  selectedSkills: [],
  chatContextAvailable: false,

  initDefaults() {
    ensureConfig(config);
    this.selectedSkills = [...this.activeEntries];
  },

  get activeEntries() {
    ensureConfig(config);
    return config.active_skills;
  },

  get selectedCount() {
    return this.selectedSkills.length;
  },

  get selectedCountLabel() {
    return `${this.selectedCount} / ${this.maxActiveSkills}`;
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

  isSelected(skill) {
    return this.selectedSkills.some((entry) => entryKey(entry) === entryKey(skill));
  },

  isCheckboxDisabled(skill) {
    return this.mutatingChat || (!this.isSelected(skill) && this.selectedCount >= this.maxActiveSkills);
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
      if (normalized.length >= this.maxActiveSkills) break;
    }

    this.selectedSkills = normalized;
    config.active_skills = compactEntries(normalized);
  },

  async toggleSkill(skill, selected) {
    const key = entryKey(skill);
    const nextEntries = this.selectedSkills.filter((entry) => entryKey(entry) !== key);

    if (selected) {
      if (this.selectedCount >= this.maxActiveSkills && !this.isSelected(skill)) {
        await toastFrontendInfo(
          `You can activate at most ${this.maxActiveSkills} skills.`,
          "Skills"
        );
        return;
      }

      nextEntries.push({
        name: String(skill.name || "").trim(),
        path: String(skill.path || "").trim(),
      });
    }

    this._setSelectedSkills(nextEntries);

    if (this.chatContextAvailable) {
      await this.submitChatAction(selected ? "activate" : "deactivate", skill);
    }
  },

  async removeEntry(entry) {
    await this.toggleSkill(entry, false);
  },

  async clearSelections() {
    const previous = [...this.selectedSkills];
    this._setSelectedSkills([]);
    if (this.chatContextAvailable) {
      for (const entry of previous) {
        await this.submitChatAction("deactivate", entry);
      }
    }
  },

  applyCatalogState(response) {
    this.chatContextAvailable = !!response?.context_available;
    const activeFromChat = Array.isArray(response?.active_skills) ? response.active_skills : null;
    const activeFromConfig = this.activeEntries;
    this._setSelectedSkills(activeFromChat || activeFromConfig);
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
      this.maxActiveSkills = Number(response.max_active_skills) || MAX_ACTIVE_SKILLS_FALLBACK;
      this.applyCatalogState(response);
    } catch (error) {
      this.catalog = [];
      this.maxActiveSkills = MAX_ACTIVE_SKILLS_FALLBACK;
      this.chatContextAvailable = false;
      this._setSelectedSkills(this.activeEntries);
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
      this.maxActiveSkills = Number(response.max_active_skills) || this.maxActiveSkills;
      this.chatContextAvailable = !!response.context_available;
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
