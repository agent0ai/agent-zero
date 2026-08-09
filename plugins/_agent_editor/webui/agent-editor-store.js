import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, fetchApi } from "/js/api.js";
import { closeModal, openModal } from "/js/modals.js";
import { showConfirmDialog } from "/js/confirmDialog.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";
import { store as modelConfigStore } from "/plugins/_model_config/webui/model-config-store.js";

const API = "/plugins/_agent_editor/agent_editor";
const AVATAR_API = "/plugins/_agent_editor/agent_editor_avatar";
const MODAL = "/plugins/_agent_editor/webui/main.html";
const SPECIFICS = "agent.system.main.specifics.md";
const LAST_SECTION_KEY = "agent-editor-last-section";
const READY_NOTE_KEY = "agent-editor-ready-note";
const PROFILE_ID = /^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$/;

const clone = (value) => JSON.parse(JSON.stringify(value));
const unique = (values) => [...new Set((values || []).map(String).filter(Boolean))];
const same = (left, right) => JSON.stringify(left) === JSON.stringify(right);

export function slugifyProfileName(value) {
  return String(value || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/[-_]{2,}/g, "-")
    .replace(/^[-_]+|[-_]+$/g, "")
    .slice(0, 64)
    .replace(/[-_]+$/g, "");
}

function policyFromState(value, hasOverride) {
  const policy = value && typeof value === "object" ? value : {};
  const normalized = {
    mode: policy.mode === "custom" ? "custom" : "inherit",
    default: policy.default === "block" ? "block" : "allow",
    allowed: unique(policy.allowed),
    blocked: unique(policy.blocked),
  };
  if (!hasOverride || normalized.mode !== "custom") normalized.mode = "inherit";
  return normalized;
}

function policyAllows(policy, id) {
  if (!policy || policy.mode !== "custom") return true;
  if (policy.blocked.includes(id)) return false;
  if (policy.allowed.includes(id)) return true;
  return policy.default === "allow";
}

function policyBehavior(policy) {
  const value = policy || {};
  if (value.mode !== "custom") {
    return { default: "allow", allowed: [], blocked: [] };
  }
  return {
    default: value.default === "block" ? "block" : "allow",
    allowed: unique(value.allowed).sort(),
    blocked: unique(value.blocked).sort(),
  };
}

function movePolicyItem(policy, id, allow) {
  policy.allowed = policy.allowed.filter((item) => item !== id);
  policy.blocked = policy.blocked.filter((item) => item !== id);
  const exceptions = allow ? "allowed" : "blocked";
  const matchesDefault = allow === (policy.default === "allow");
  if (!matchesDefault) policy[exceptions].push(id);
}

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value || "");
  return element.innerHTML;
}

const model = {
  intent: { view: "create", profileId: "", contextId: "", projectName: "" },
  view: "editor",
  mode: "easy",
  section: "1",
  loading: false,
  saving: false,
  avatarUploading: false,
  error: "",
  state: null,
  projects: [],
  projectName: "",
  profiles: [],
  profileAvailabilitySaving: false,
  duplicatingProfile: "",
  draft: null,
  initialDraft: null,
  selectedPrompt: SPECIFICS,
  promptFileSearch: "",
  promptTextSearch: "",
  comparePrompt: "",
  toolSearch: "",
  toolCategory: "all",
  toolOrigin: "all",
  selectedAllowedTools: [],
  selectedBlockedTools: [],
  skillSearch: "",
  skillOrigin: "all",
  selectedAllowedSkills: [],
  selectedBlockedSkills: [],
  promptEditBaselines: {},
  plan: { written: [], deleted: [], warnings: [] },
  planLoading: false,
  planStatus: "idle",
  pendingMutation: null,
  readyNoteContext: "",
  suppressClosePrompt: false,
  root: null,
  previewObjectUrl: "",

  init() {
    try {
      this.readyNoteContext = sessionStorage.getItem(READY_NOTE_KEY) || "";
    } catch {
      this.readyNoteContext = "";
    }
  },

  async open(options = {}) {
    const contextProject = chatsStore.selectedContext?.project;
    const currentProjectName = typeof contextProject === "object"
      ? String(contextProject?.name || "")
      : String(contextProject || "");
    this.intent = {
      view: options.view || (options.profileId ? "edit" : "create"),
      profileId: String(options.profileId || ""),
      contextId: String(options.contextId || chatsStore.selected || ""),
      projectName: options.projectName === undefined
        ? currentProjectName
        : String(options.projectName || ""),
    };
    this.suppressClosePrompt = false;
    return await openModal(MODAL, () => this.beforeClose());
  },

  async mount(root) {
    this.revokePreview();
    this.root = root;
    this.draft = null;
    this.initialDraft = null;
    this.promptEditBaselines = {};
    this.loading = true;
    this.error = "";
    this.pendingMutation = null;
    this.profileAvailabilitySaving = false;
    this.duplicatingProfile = "";
    this.plan = { written: [], deleted: [], warnings: [] };
    this.planStatus = "idle";
    this.view = this.intent.view === "manage" ? "manage" : "editor";
    this.projectName = this.intent.projectName || "";
    const modalTitle =
      this.view === "manage"
        ? "Manage agents"
        : this.intent.view === "create"
          ? "Create agent"
          : "Edit agent";
    this.setModalTitle(modalTitle);
    const modal = this.root.closest(".modal");
    const titleAfterLoad = (event) => {
      if (event.detail?.modal?.element !== modal) return;
      document.removeEventListener("modal-content-loaded", titleAfterLoad);
      this.setModalTitle(modalTitle);
    };
    document.addEventListener("modal-content-loaded", titleAfterLoad);
    this.mode = "easy";
    this.section = this.savedSection();
    this.syncSurface();
    await this.loadProjects();
    if (this.projectName && this.projects.length
      && !this.projects.some((project) => project.key === this.projectName)) {
      this.projectName = "";
      this.intent = { ...this.intent, projectName: "" };
    }
    await this.loadProfiles();
    if (this.view === "manage") {
      this.loading = false;
      this.setModalTitle("Manage agents");
      return;
    }
    await this.loadEditor(
      this.intent.view === "create" ? "new-agent" : this.intent.profileId,
      this.intent.view === "create",
    );
  },

  async loadProfiles() {
    try {
      const data = await callJsonApi(API, {
        action: "list",
        ...this.scopeInput(),
      });
      this.profiles = data.profiles || [];
    } catch (error) {
      this.error = error.message || String(error);
      this.profiles = [];
    }
  },

  async loadProjects() {
    try {
      const data = await callJsonApi("/projects", { action: "list_options" });
      this.projects = data.ok ? (data.data || []) : [];
    } catch {
      this.projects = [];
    }
  },

  scopeInput() {
    return { project_name: this.projectName || "" };
  },

  get scopeLabel() {
    if (!this.projectName) return "Global";
    return this.projects.find((project) => project.key === this.projectName)?.label
      || this.projectName;
  },

  get inheritedLabel() {
    return this.projectName ? "Inherited" : "Default";
  },

  activeProjectName() {
    const project = chatsStore.selectedContext?.project;
    return typeof project === "object"
      ? String(project?.name || "")
      : String(project || "");
  },

  currentChatUsesScope() {
    return Boolean(
      chatsStore.selected
      && (!this.projectName || this.projectName === this.activeProjectName())
    );
  },

  isProfileActive(profileId) {
    return this.currentChatUsesScope()
      && chatsStore.selectedContext?.agent_profile === profileId;
  },

  activeProfile() {
    return this.profiles.find((profile) => this.isProfileActive(profile.id)) || null;
  },

  async setProfileEnabled(profile, enabled) {
    if (!profile?.id || this.profileAvailabilitySaving) return;
    const previous = !!profile.enabled;
    profile.enabled = enabled;
    this.profileAvailabilitySaving = true;
    try {
      const data = await callJsonApi(API, {
        action: "set_enabled",
        profile_id: profile.id,
        enabled,
        active_context_id: chatsStore.selected || "",
        ...this.scopeInput(),
      });
      if (data.active_profile && chatsStore.selectedContext) {
        chatsStore.selectedContext.agent_profile = data.active_profile;
        chatsStore.selectedContext.agent_profile_label = data.active_profile_label || data.active_profile;
      }
      await modelConfigStore.loadAgentProfiles(true);
    } catch (error) {
      profile.enabled = previous;
      this.error = error.message || String(error);
    } finally {
      this.profileAvailabilitySaving = false;
    }
  },

  async duplicateProfile(profile) {
    if (!profile?.id || this.duplicatingProfile) return;
    this.duplicatingProfile = profile.id;
    this.error = "";
    try {
      const data = await callJsonApi(API, {
        action: "duplicate",
        profile_id: profile.id,
        ...this.scopeInput(),
      });
      this.profiles = data.profiles || [];
      await modelConfigStore.loadAgentProfiles(true);
      globalThis.justToast?.(
        `${data.title || profile.title || profile.id} created.`,
        "success", 1800, "agent-profile-duplicate",
      );
    } catch (error) {
      this.error = error.message || String(error);
    } finally {
      this.duplicatingProfile = "";
    }
  },

  async onScopeChanged() {
    const previous = this.intent.projectName || "";
    const next = this.projectName || "";
    if (previous === next) return;
    if (this.view === "editor" && !this.draft?.creating && this.dirty
      && !window.confirm("Changing project will discard your unsaved changes. Continue?")) {
      this.projectName = previous;
      return;
    }
    this.intent = { ...this.intent, projectName: next };
    this.loading = true;
    this.error = "";
    try {
      await this.loadProfiles();
      if (this.view !== "editor" || !this.draft) return;
      if (!this.draft.creating
        && !this.profiles.some((profile) => profile.id === this.draft.profileId)) {
        this.projectName = previous;
        this.intent = { ...this.intent, projectName: previous };
        await this.loadProfiles();
        throw new Error("This agent is not available in the selected scope.");
      }
      const data = await callJsonApi(API, {
        action: "load",
        profile_id: this.draft.creating ? "new-agent" : this.draft.profileId,
        ...this.scopeInput(),
      });
      this.state = data.state;
      if (!this.draft.creating) this.makeDraft(false);
    } catch (error) {
      if (this.view === "editor" && this.projectName !== previous) {
        this.projectName = previous;
        this.intent = { ...this.intent, projectName: previous };
        await this.loadProfiles();
      }
      this.error = error.message || String(error);
    } finally {
      this.loading = false;
    }
  },

  async loadEditor(profileId, creating = false) {
    this.loading = true;
    this.error = "";
    try {
      const data = await callJsonApi(API, {
        action: "load",
        profile_id: profileId,
        ...this.scopeInput(),
      });
      this.state = data.state;
      this.intent = { ...this.intent, view: creating ? "create" : "edit", profileId };
      this.view = "editor";
      this.makeDraft(creating);
      this.setModalTitle(creating ? "Create agent" : "Edit agent");
      this.mode = "easy";
      this.syncSurface();
      requestAnimationFrame(() => this.root?.querySelector("#agent-editor-name")?.focus());
    } catch (error) {
      this.error = error.message || String(error);
    } finally {
      this.loading = false;
    }
  },

  makeDraft(creating) {
    const metadata = this.state.profile.metadata;
    const prompts = {};
    for (const item of this.state.prompts || []) {
      const value = creating && item.filename === SPECIFICS ? "" : String(item.effective || "");
      prompts[item.filename] = {
        ...item,
        value,
        initialValue: value,
        reset: false,
      };
    }
    if (!prompts[SPECIFICS]) {
      prompts[SPECIFICS] = {
        filename: SPECIFICS,
        group: "2.1",
        group_label: "Agent instructions",
        value: "",
        initialValue: "",
        inherited: "",
        source_chain: [],
        state: "Unavailable",
        reset: false,
      };
    }

    const avatar = metadata.avatar?.effective || null;
    this.draft = {
      creating,
      profileId: creating ? "" : this.state.profile.id,
      title: creating ? "" : String(metadata.title?.effective || this.state.profile.id),
      description: creating ? "" : String(metadata.description?.effective || ""),
      context: creating ? "" : String(metadata.context?.effective || ""),
      metadataResets: [],
      avatar: avatar ? clone(avatar) : null,
      avatarToken: "",
      avatarPreview: this.state.profile.avatar_url || "",
      prompts,
      modelPreset: this.state.model_preset.has_override
        ? String(this.state.model_preset.override || "")
        : "",
      toolPolicy: policyFromState(this.state.tools.policy, this.state.tools.has_override),
      skillPolicy: policyFromState(this.state.skills.policy, this.state.skills.has_override),
    };
    this.initialDraft = clone(this.draft);
    this.selectedPrompt = SPECIFICS;
    this.comparePrompt = "";
    this.planStatus = "idle";
    this.selectedAllowedTools = [];
    this.selectedBlockedTools = [];
    this.selectedAllowedSkills = [];
    this.selectedBlockedSkills = [];
    this.promptEditBaselines = Object.fromEntries(
      Object.values(prompts).map((prompt) => [prompt.filename, {
        value: prompt.value,
        reset: prompt.reset,
      }]),
    );
  },

  get dirty() {
    return Boolean(this.draft && this.initialDraft && !same(this.draft, this.initialDraft));
  },

  get title() {
    return this.draft?.creating ? "Create agent" : "Edit agent";
  },

  get profileConflict() {
    if (!this.draft?.creating || !this.draft.profileId) return null;
    return this.profiles.find((profile) => profile.id === this.draft.profileId) || null;
  },

  get instructions() {
    return this.draft?.prompts?.[SPECIFICS] || null;
  },

  get toolCatalog() {
    return (this.state?.tools?.catalog || []).filter((item) => item.available !== false);
  },

  get toolOrigins() {
    return unique((this.state?.tools?.catalog || []).map((item) => item.origin)).sort();
  },

  get skillOrigins() {
    return unique((this.state?.skills?.catalog || []).map((item) => item.origin)).sort();
  },

  get skillCatalog() {
    return (this.state?.skills?.catalog || []).filter((item) => item.available !== false);
  },

  get promptGroups() {
    const groups = new Map();
    for (const prompt of Object.values(this.draft?.prompts || {})) {
      groups.set(prompt.group, prompt.group_label);
    }
    return [...groups.entries()]
      .map(([id, label]) => ({ id, label }))
      .sort((a, b) => Number(a.id.split(".")[1]) - Number(b.id.split(".")[1]));
  },

  get selectedPromptDraft() {
    return this.draft?.prompts?.[this.selectedPrompt] || null;
  },

  sectionDirty(section) {
    if (!this.draft || !this.initialDraft) return false;
    if (String(section) === "1") {
      return !same(
        [this.draft.title, this.draft.description, this.draft.context, this.draft.avatar, this.draft.avatarToken, this.draft.metadataResets, this.draft.modelPreset],
        [this.initialDraft.title, this.initialDraft.description, this.initialDraft.context, this.initialDraft.avatar, this.initialDraft.avatarToken, this.initialDraft.metadataResets, this.initialDraft.modelPreset],
      );
    }
    if (String(section) === "2") return Object.values(this.draft.prompts).some((prompt) => this.promptDirty(prompt));
    if (String(section) === "3") return !same(this.draft.toolPolicy, this.initialDraft.toolPolicy);
    if (String(section) === "4") return !same(this.draft.skillPolicy, this.initialDraft.skillPolicy);
    return this.dirty;
  },

  beforeClose() {
    if (this.suppressClosePrompt || !this.dirty) return true;
    return window.confirm("You have unsaved changes that will be lost. Continue?");
  },

  setModalTitle(value) {
    const modal = this.root?.closest(".modal") || this.root?.parentElement?.closest(".modal");
    const title = modal?.querySelector(".modal-title");
    if (title) title.textContent = value;
  },

  syncSurface() {
    const inner = this.root?.closest(".modal-inner");
    inner?.classList.toggle("agent-editor-advanced", this.mode === "advanced");
    inner?.classList.toggle("agent-editor-easy", this.mode !== "advanced");
  },

  setMode(mode, section = "", preview = true) {
    this.mode = mode === "advanced" ? "advanced" : "easy";
    if (section) this.setSection(section, preview);
    else if (preview && this.mode === "advanced" && this.section === "5") this.previewPlan();
    this.syncSurface();
    if (this.mode === "advanced") {
      requestAnimationFrame(() => {
        this.root?.querySelector(`[data-agent-editor-section="${this.section}"]`)?.focus();
      });
    }
  },

  setSection(section, preview = true) {
    this.section = String(section || "1");
    try {
      localStorage.setItem(LAST_SECTION_KEY, this.section);
    } catch {}
    if (preview && this.section === "5") this.previewPlan();
  },

  savedSection() {
    try {
      return localStorage.getItem(LAST_SECTION_KEY) || "1";
    } catch {
      return "1";
    }
  },

  onNameInput() {
    if (this.draft?.creating) this.draft.profileId = slugifyProfileName(this.draft.title);
  },

  openConflictingProfile() {
    if (!this.profileConflict) return;
    this.loadEditor(this.profileConflict.id, false);
  },

  initials() {
    const words = String(this.draft?.title || this.draft?.profileId || "Agent")
      .trim().split(/\s+/).filter(Boolean);
    return words.slice(0, 2).map((word) => word[0]).join("").toUpperCase() || "A";
  },

  profileVisual(profile = {}) {
    const id = String(profile.id || profile.key || "");
    const title = String(profile.title || profile.label || id || "Agent");
    const visual = modelConfigStore.getAgentProfileVisual(id, title);
    return {
      ...visual,
      color: profile.avatar?.kind === "color" ? profile.avatar.value : visual.color,
      url: profile.avatar_url || visual.url,
    };
  },

  avatarColor() {
    return this.draft?.avatar?.kind === "color"
      ? this.draft.avatar.value
      : this.profileVisual({ id: this.draft?.profileId, title: this.draft?.title }).color;
  },

  chooseAvatarColor(value) {
    const color = String(value || "").toUpperCase();
    this.revokePreview();
    this.draft.avatar = { kind: "color", value: color };
    this.draft.avatarToken = "";
    this.draft.avatarPreview = "";
    this.draft.metadataResets = this.draft.metadataResets.filter((key) => key !== "avatar");
  },

  resetAvatar() {
    this.revokePreview();
    const inherited = this.state.profile.metadata.avatar?.inherited || null;
    this.draft.avatar = inherited ? clone(inherited) : null;
    this.draft.avatarToken = "";
    this.draft.avatarPreview = "";
    if (!this.draft.metadataResets.includes("avatar")) this.draft.metadataResets.push("avatar");
  },

  async uploadAvatar(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    this.revokePreview();
    this.previewObjectUrl = URL.createObjectURL(file);
    this.draft.avatarPreview = this.previewObjectUrl;
    this.avatarUploading = true;
    this.error = "";
    try {
      const body = new FormData();
      body.append("avatar", file);
      const response = await fetchApi(AVATAR_API, { method: "POST", body });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      this.draft.avatar = { kind: "image", value: "assets/avatar.webp" };
      this.draft.avatarToken = data.token;
      this.draft.metadataResets = this.draft.metadataResets.filter((key) => key !== "avatar");
    } catch (error) {
      this.error = error.message || String(error);
      this.revokePreview();
      this.draft.avatar = clone(this.initialDraft.avatar);
      this.draft.avatarToken = this.initialDraft.avatarToken;
      this.draft.avatarPreview = this.initialDraft.avatarPreview;
      this.draft.metadataResets = clone(this.initialDraft.metadataResets);
    } finally {
      this.avatarUploading = false;
    }
  },

  revokePreview() {
    if (this.previewObjectUrl) URL.revokeObjectURL(this.previewObjectUrl);
    this.previewObjectUrl = "";
  },

  resetMetadata(key) {
    if (!["title", "description", "context"].includes(key)) return;
    this.draft[key] = String(this.state.profile.metadata[key]?.inherited || "");
    if (!this.draft.metadataResets.includes(key)) this.draft.metadataResets.push(key);
  },

  metadataResetPending(key) {
    return Boolean(this.draft?.metadataResets?.includes(key));
  },

  canResetMetadata(key) {
    const metadata = this.state?.profile?.metadata?.[key];
    return Boolean(
      !this.draft?.creating
      && metadata?.has_override
      && !this.metadataResetPending(key)
      && (key !== "title" || String(metadata?.inherited || "").trim()),
    );
  },

  metadataProvenance(key) {
    const metadata = this.state?.profile?.metadata?.[key] || {};
    if (metadata.has_override && !this.metadataResetPending(key)) return "Customized by you";
    if (this.projectName) return "Inherited from Global";
    const match = String(metadata.inherited_source || metadata.source || "")
      .match(/(?:^|\/)agents\/([^/]+)/);
    const sourceId = match?.[1] || "";
    if (!sourceId || sourceId === this.state?.profile?.id) return "Using the default";
    const source = this.profiles.find((profile) => profile.id === sourceId)?.title || sourceId;
    return `Inherited from ${source}`;
  },

  markMetadataSet(key) {
    this.draft.metadataResets = this.draft.metadataResets.filter((item) => item !== key);
  },

  restoreInstructions() {
    const prompt = this.instructions;
    if (!prompt) return;
    prompt.value = String(prompt.inherited || "");
    prompt.reset = true;
    this.acceptPromptEdit(prompt.filename);
  },

  markPromptSet(filename) {
    const prompt = this.draft?.prompts?.[filename];
    if (prompt) {
      prompt.reset = false;
      this.acceptPromptEdit(filename);
    }
  },

  onPromptInput(filename) {
    const prompt = this.draft?.prompts?.[filename];
    if (prompt) prompt.reset = false;
  },

  promptEditPending(prompt) {
    const baseline = this.promptEditBaselines[prompt?.filename];
    return Boolean(
      prompt
      && baseline
      && (prompt.value !== baseline.value || prompt.reset !== baseline.reset),
    );
  },

  acceptPromptEdit(filename) {
    const prompt = this.draft?.prompts?.[filename];
    if (!prompt) return;
    this.promptEditBaselines[filename] = {
      value: prompt.value,
      reset: prompt.reset,
    };
  },

  discardPromptEdit(filename) {
    const prompt = this.draft?.prompts?.[filename];
    const baseline = this.promptEditBaselines[filename];
    if (!prompt || !baseline) return;
    prompt.value = baseline.value;
    prompt.reset = baseline.reset;
  },

  resetPrompt(filename) {
    const prompt = this.draft?.prompts?.[filename];
    if (!prompt) return;
    prompt.value = prompt.inherited;
    prompt.reset = true;
    this.acceptPromptEdit(filename);
  },

  promptDisplayState(prompt) {
    if (prompt?.reset) return this.projectName ? "Will use inherited" : "Will use the default";
    if (prompt?.has_override || this.promptDirty(prompt)) return "Customized by you";
    if (prompt?.state === "Unavailable") return "Unavailable";
    return this.projectName ? "Inherited" : "Default";
  },

  promptSourceChain(prompt) {
    if (!prompt?.reset && (prompt?.has_override || this.promptDirty(prompt))) return "Customized by you";
    if (this.projectName) return "Inherited from Global";
    const source = [...(prompt?.source_chain || [])]
      .filter((item) => item !== "Your override")
      .at(-1);
    const current = String(
      this.state?.profile?.metadata?.title?.effective || this.state?.profile?.id || "",
    );
    return !source || source.toLowerCase() === current.toLowerCase()
      ? "Default"
      : `Inherited from ${source}`;
  },

  selectPrompt(filename) {
    if (!this.draft?.prompts?.[filename]) return;
    this.selectedPrompt = filename;
    this.promptTextSearch = "";
    this.comparePrompt = "";
  },

  filteredPromptFiles(group = "") {
    const query = this.promptFileSearch.trim().toLowerCase();
    return Object.values(this.draft?.prompts || {}).filter((prompt) =>
      (!group || prompt.group === group) && (!query || [prompt.filename, prompt.state, prompt.source]
        .join(" ").toLowerCase().includes(query)),
    );
  },

  promptDirty(prompt) {
    return Boolean(prompt?.reset || prompt?.value !== prompt?.initialValue);
  },

  promptMatchCount() {
    const query = this.promptTextSearch;
    const text = this.selectedPromptDraft?.value || "";
    if (!query) return 0;
    return text.toLowerCase().split(query.toLowerCase()).length - 1;
  },

  findInPrompt(direction = 1) {
    const textarea = this.root?.querySelector("#agent-editor-prompt-text");
    const query = this.promptTextSearch;
    const text = this.selectedPromptDraft?.value || "";
    if (!textarea || !query) return;
    const lower = text.toLowerCase();
    const needle = query.toLowerCase();
    const start = direction > 0 ? textarea.selectionEnd : Math.max(0, textarea.selectionStart - 1);
    let index = direction > 0 ? lower.indexOf(needle, start) : lower.lastIndexOf(needle, start);
    if (index < 0) index = direction > 0 ? lower.indexOf(needle) : lower.lastIndexOf(needle);
    if (index < 0) return;
    textarea.focus();
    textarea.setSelectionRange(index, index + query.length);
  },

  copyPromptPath() {
    const root = this.projectName
      ? `usr/projects/${this.projectName}/.a0proj/agents`
      : "usr/agents";
    const path = `${root}/${this.draft.profileId}/prompts/${this.selectedPrompt}`;
    navigator.clipboard?.writeText(path);
    globalThis.justToast?.("Path copied", "success", 1200, "agent-editor-copy");
  },

  useStandardTools() {
    this.draft.toolPolicy = { mode: "inherit", default: "allow", allowed: [], blocked: [] };
    this.selectedAllowedTools = [];
    this.selectedBlockedTools = [];
  },

  customizePolicy(kind) {
    const key = kind === "tool" ? "toolPolicy" : "skillPolicy";
    if (this.draft[key].mode === "custom") return;
    const state = kind === "tool" ? this.state.tools : this.state.skills;
    this.draft[key] = { mode: "custom", ...policyBehavior(state.effective_policy) };
  },

  chooseTools() {
    this.customizePolicy("tool");
    this.setMode("advanced", "3");
  },

  setEasyToolAllowed(id, allow) {
    this.customizePolicy("tool");
    this.moveTools([id], allow);
    const policy = this.draft.toolPolicy;
    if (this.initialDraft?.toolPolicy.mode !== "custom"
      && same(policyBehavior(policy), policyBehavior(this.state.tools.effective_policy))) {
      this.useStandardTools();
    }
  },

  useStandardSkills() {
    this.draft.skillPolicy = { mode: "inherit", default: "allow", allowed: [], blocked: [] };
    this.selectedAllowedSkills = [];
    this.selectedBlockedSkills = [];
  },

  chooseSkills() {
    this.customizePolicy("skill");
  },

  setPolicyDefault(kind, nextDefault) {
    const policy = kind === "tool" ? this.draft.toolPolicy : this.draft.skillPolicy;
    const catalog = kind === "tool" ? this.state.tools.catalog : this.state.skills.catalog;
    const ids = catalog.map((item) =>
      kind === "tool" ? item.id : item.name,
    );
    const current = new Map(ids.map((id) => [id, policyAllows(policy, id)]));
    policy.default = nextDefault === "block" ? "block" : "allow";
    policy.allowed = [];
    policy.blocked = [];
    for (const [id, allowed] of current) movePolicyItem(policy, id, allowed);
  },

  isToolAllowed(item) {
    const policy = this.draft.toolPolicy.mode === "custom"
      ? this.draft.toolPolicy
      : this.state?.tools?.effective_policy;
    return policyAllows(policy, item.id);
  },

  isSkillAllowed(item) {
    const policy = this.draft.skillPolicy.mode === "custom"
      ? this.draft.skillPolicy
      : this.state?.skills?.effective_policy;
    return policyAllows(policy, item.name);
  },

  filteredTools(allowed) {
    const query = this.toolSearch.trim().toLowerCase();
    return (this.state?.tools?.catalog || []).filter((item) => {
      if (this.draft.toolPolicy.mode !== "custom" && item.available === false) return false;
      if (this.isToolAllowed(item) !== allowed) return false;
      const category = item.id.split(":", 1)[0];
      if (this.toolCategory !== "all" && category !== this.toolCategory) return false;
      if (this.toolOrigin !== "all" && item.origin !== this.toolOrigin) return false;
      return !query || [item.label, item.name, item.id, item.description, item.origin]
        .join(" ").toLowerCase().includes(query);
    });
  },

  moveTools(ids, allow) {
    for (const id of unique(ids)) movePolicyItem(this.draft.toolPolicy, id, allow);
    this.selectedAllowedTools = [];
    this.selectedBlockedTools = [];
  },

  moveAllVisibleTools(allow) {
    return this.confirmBulkMove(
      "tool",
      this.filteredTools(!allow).map((item) => item.id),
      allow,
    );
  },

  filteredSkills(allowed) {
    const query = this.skillSearch.trim().toLowerCase();
    return (this.state?.skills?.catalog || []).filter((item) => {
      if (this.draft.skillPolicy.mode !== "custom" && item.available === false) return false;
      if (this.isSkillAllowed(item) !== allowed) return false;
      if (this.skillOrigin !== "all" && item.origin !== this.skillOrigin) return false;
      return !query || [item.name, item.description, item.origin, ...(item.tags || [])]
        .join(" ").toLowerCase().includes(query);
    });
  },

  moveSkills(ids, allow) {
    for (const id of unique(ids)) movePolicyItem(this.draft.skillPolicy, id, allow);
    this.selectedAllowedSkills = [];
    this.selectedBlockedSkills = [];
  },

  moveAllVisibleSkills(allow) {
    return this.confirmBulkMove(
      "skill",
      this.filteredSkills(!allow).map((item) => item.name),
      allow,
    );
  },

  async confirmBulkMove(kind, ids, allow) {
    if (!ids.length) return;
    const action = allow ? "Allow" : "Block";
    const plural = `${kind}${ids.length === 1 ? "" : "s"}`;
    const confirmed = await showConfirmDialog({
      title: `${action} ${ids.length} shown ${plural}?`,
      message: `<p>This changes every ${kind} currently shown by your filters.</p>`,
      confirmText: `${action} shown ${plural}`,
      type: "warning",
    });
    if (!confirmed) return;
    if (kind === "tool") this.moveTools(ids, allow);
    else this.moveSkills(ids, allow);
  },

  skillWarnings(skill) {
    const warnings = [];
    for (const toolName of skill.allowed_tools || []) {
      const tool = (this.state?.tools?.catalog || []).find((item) => item.name === toolName);
      if (tool && !this.isToolAllowed(tool)) warnings.push(toolName);
    }
    return warnings;
  },

  async openPresetManager() {
    await modelConfigStore.openPresetEditor(this.draft.modelPreset || this.state.model_preset.effective);
    try {
      const data = await callJsonApi(API, {
        action: "load",
        profile_id: this.draft.profileId || "new-agent",
        ...this.scopeInput(),
      });
      this.state.model_presets = data.state.model_presets;
    } catch (error) {
      this.error = error.message || String(error);
    }
  },

  validationIssues() {
    const issues = [];
    if (!this.draft?.title.trim()) {
      issues.push({ key: "name", section: "1", field: "agent-editor-advanced-name", label: "Agent name", message: "Agent name is required." });
    }
    if (this.draft?.creating) {
      if (this.draft.title.trim() && (!this.draft.profileId || !PROFILE_ID.test(this.draft.profileId))) {
        issues.push({ key: "name", section: "1", field: "agent-editor-advanced-name", label: "Agent name", message: "Enter a name that produces a valid profile ID." });
      }
      if (this.profileConflict) {
        issues.push({ key: "name", section: "1", field: "agent-editor-advanced-name", label: "Agent name", message: `An agent with profile ID ${this.draft.profileId} already exists.` });
      }
      if (!this.instructions?.value.trim()) {
        issues.push({ key: "instructions", section: "2", field: "agent-editor-prompt-text", label: "Instructions", message: "Instructions are required for a new agent." });
      }
    }
    if (this.avatarUploading) {
      issues.push({ key: "avatar", section: "1", field: "agent-editor-advanced-name", label: "Avatar", message: "Wait for the avatar upload to finish." });
    }
    return issues;
  },

  validationErrors() {
    return this.validationIssues().map((issue) => issue.message);
  },

  sectionIssues(section) {
    return this.validationIssues().filter((issue) => issue.section === String(section));
  },

  fieldIssue(key) {
    return this.validationIssues().find((issue) => issue.key === key) || null;
  },

  showValidationIssue(issue) {
    if (!issue) return;
    if (issue.key === "instructions") this.selectPrompt(SPECIFICS);
    this.setMode("advanced", issue.section);
  },

  buildPatch() {
    const patch = {
      profile_id: this.draft.profileId,
      creating: this.draft.creating,
      editor_mode: this.mode,
    };
    const metadata = { set: {}, reset: unique(this.draft.metadataResets) };
    for (const key of ["title", "description", "context"]) {
      if (this.draft.creating ? key === "title" : this.draft[key] !== this.initialDraft[key]) {
        if (!metadata.reset.includes(key)) metadata.set[key] = this.draft[key];
      }
    }
    const avatarChanged = !same(
      [this.draft.avatar, this.draft.avatarToken],
      [this.initialDraft.avatar, this.initialDraft.avatarToken],
    );
    if (avatarChanged && !metadata.reset.includes("avatar") && this.draft.avatar) {
      metadata.set.avatar = this.draft.avatar.kind === "image" && this.draft.avatarToken
        ? { kind: "image", token: this.draft.avatarToken }
        : clone(this.draft.avatar);
    }
    if (Object.keys(metadata.set).length || metadata.reset.length) patch.metadata = metadata;

    const prompts = { set: {}, reset: [] };
    for (const prompt of Object.values(this.draft.prompts)) {
      if (prompt.reset) prompts.reset.push(prompt.filename);
      else if ((this.draft.creating && prompt.filename === SPECIFICS) || prompt.value !== prompt.initialValue) {
        prompts.set[prompt.filename] = prompt.value;
      }
    }
    if (Object.keys(prompts.set).length || prompts.reset.length) patch.prompts = prompts;

    if (this.draft.modelPreset !== this.initialDraft.modelPreset) {
      patch.model_preset = this.draft.modelPreset
        ? { mode: "preset", name: this.draft.modelPreset }
        : { mode: "inherit" };
    }
    if (!same(this.draft.toolPolicy, this.initialDraft.toolPolicy)) {
      patch.tool_policy = this.draft.toolPolicy.mode === "inherit"
        ? { mode: "inherit" }
        : clone(this.draft.toolPolicy);
    }
    if (!same(this.draft.skillPolicy, this.initialDraft.skillPolicy)) {
      patch.skill_policy = this.draft.skillPolicy.mode === "inherit"
        ? { mode: "inherit" }
        : clone(this.draft.skillPolicy);
    }
    return patch;
  },

  async previewPlan() {
    if (!this.draft) return false;
    const errors = this.validationErrors();
    if (errors.length) {
      this.error = "";
      this.plan = { written: [], deleted: [], warnings: [] };
      this.planStatus = "blocked";
      return false;
    }
    this.planLoading = true;
    this.planStatus = "loading";
    this.error = "";
    this.pendingMutation = null;
    try {
      const data = await callJsonApi(API, {
        action: "plan",
        patch: this.buildPatch(),
        ...this.scopeInput(),
      });
      this.plan = data;
      this.planStatus = "ready";
      return true;
    } catch (error) {
      this.planStatus = "error";
      this.error = error.message || String(error);
      return false;
    } finally {
      this.planLoading = false;
    }
  },

  async save(test = false) {
    if (this.saving || !this.draft) return false;
    const errors = this.validationErrors();
    if (errors.length) {
      this.error = "";
      return false;
    }
    this.saving = true;
    this.error = "";
    const profileId = this.draft.profileId;
    const creating = this.draft.creating;
    try {
      const data = await callJsonApi(API, {
        action: "save",
        patch: this.buildPatch(),
        ...this.scopeInput(),
      });
      this.plan = data;
      this.initialDraft = clone(this.draft);
      this.revokePreview();
      await modelConfigStore.loadAgentProfiles(true);
      this.suppressClosePrompt = true;
      await closeModal(MODAL);
      if (creating || test) {
        await this.openFreshChat(profileId, creating);
      } else {
        globalThis.justToast?.(
          `Agent saved. <button class="toast-link" type="button" onclick="window.testAgentProfile('${profileId}')">Test in new chat</button>`,
          "success", 8000, "agent-editor-saved",
        );
      }
      return true;
    } catch (error) {
      this.error = error.message || String(error);
      return false;
    } finally {
      this.saving = false;
    }
  },

  async openFreshChat(profileId, showReadyNote = false) {
    try {
      const created = await callJsonApi("/chat_create", {
        current_context: this.intent.contextId || chatsStore.selected || "",
      });
      await callJsonApi("/projects", {
        action: this.projectName ? "activate" : "deactivate",
        context_id: created.ctxid,
        ...(this.projectName ? { name: this.projectName } : {}),
      });
      await callJsonApi("/agent_profile_set", {
        context_id: created.ctxid,
        agent_profile: profileId,
      });
      await callJsonApi("/plugins/_model_config/model_override", {
        action: "clear",
        context_id: created.ctxid,
      });
      if (showReadyNote) {
        this.readyNoteContext = created.ctxid;
        try { sessionStorage.setItem(READY_NOTE_KEY, created.ctxid); } catch {}
      }
      await chatsStore.selectChat(created.ctxid);
      document.dispatchEvent(new CustomEvent("chat-created", { detail: { ctxid: created.ctxid } }));
      return created.ctxid;
    } catch (error) {
      globalThis.toastFetchError?.("Failed to open a test chat", error);
      return "";
    }
  },

  dismissReadyNote() {
    this.readyNoteContext = "";
    try { sessionStorage.removeItem(READY_NOTE_KEY); } catch {}
  },

  readyNoteVisible() {
    return Boolean(this.readyNoteContext && chatsStore.selected === this.readyNoteContext);
  },

  async planRemoval(destructive = false) {
    this.planLoading = true;
    this.error = "";
    try {
      const data = await callJsonApi(API, {
        action: "plan_remove_changes",
        profile_id: this.draft.profileId,
        destructive,
        ...this.scopeInput(),
      });
      this.plan = data;
      this.planStatus = "ready";
      this.pendingMutation = { destructive };
      this.setMode("advanced", "5", false);
    } catch (error) {
      this.error = error.message || String(error);
    } finally {
      this.planLoading = false;
    }
  },

  async applyPendingMutation() {
    if (!this.pendingMutation) return;
    const planned = [
      ["Will update", this.plan.written || []],
      ["Will delete", this.plan.deleted || []],
    ].filter(([, paths]) => paths.length);
    const changes = planned.length
      ? planned.map(([label, paths]) => `<p><strong>${label}</strong></p><ul>${paths.map((path) => `<li><code>${escapeHtml(path)}</code></li>`).join("")}</ul>`).join("")
      : "<p>No files will change.</p>";
    const confirmed = await showConfirmDialog({
      title: this.pendingMutation.destructive ? "Delete all customizations for this profile?" : "Remove my changes?",
      message: `${changes}<p>Agent Zero’s defaults are not touched.</p>`,
      confirmText: this.pendingMutation.destructive ? "Delete planned files" : "Remove planned changes",
      type: "danger",
    });
    if (!confirmed) return;
    try {
      await callJsonApi(API, {
        action: "remove_changes",
        profile_id: this.draft.profileId,
        destructive: this.pendingMutation.destructive,
        ...this.scopeInput(),
      });
      this.pendingMutation = null;
      await this.loadEditor(this.draft.profileId);
      globalThis.justToast?.("Your agent customizations were removed.", "success", 2200);
    } catch (error) {
      this.error = error.message || String(error);
    }
  },

  async deleteProfile(profileId) {
    try {
      const confirmed = await showConfirmDialog({
        title: `Delete ${escapeHtml(profileId)}?`,
        message: `<p>This agent profile will be permanently deleted from ${escapeHtml(this.scopeLabel)} and cannot be recovered.</p>`,
        confirmText: "Delete agent",
        type: "danger",
      });
      if (!confirmed) return;
      await callJsonApi(API, {
        action: "delete",
        profile_id: profileId,
        confirm: true,
        ...this.scopeInput(),
      });
      await this.loadProfiles();
      await modelConfigStore.loadAgentProfiles(true);
      this.view = "manage";
      this.setModalTitle("Manage agents");
      globalThis.justToast?.(`Agent deleted from ${this.scopeLabel}.`, "success", 1800);
    } catch (error) {
      this.error = error.message || String(error);
    }
  },

  showManager() {
    if (this.dirty && !window.confirm("You have unsaved changes that will be lost. Continue?")) return;
    this.view = "manage";
    this.mode = "easy";
    this.syncSurface();
    this.setModalTitle("Manage agents");
    this.loadProfiles();
  },
};

export const store = createStore("agentEditor", model);
