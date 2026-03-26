---
name: a0-review-plugin
description: Full audit of Agent Zero plugins in usr/plugins/. Reviews manifest validity, directory structure, code patterns (Store Gating, notifications, imports), security, and duplicate detection against the community index. Use when asked to review, audit, validate, or check an existing plugin before using or contributing it.
version: 1.0.0
tags: ["plugins", "review", "audit", "validate", "security", "checklist"]
trigger_patterns:
  - "review plugin"
  - "audit plugin"
  - "validate plugin"
  - "check plugin"
  - "plugin review"
  - "is my plugin correct"
  - "plugin checklist"
---

# Agent Zero Plugin Review

Full-audit workflow for plugins in `/a0/usr/plugins/<name>/`. Run all 4 phases in order and report findings grouped by phase. Mark each item PASS, FAIL, or WARN.

For detailed checklists and code pattern references, read `checklists.md` in this skill directory when needed.

---

## Phase 1: Manifest Validation

Read `usr/plugins/<name>/plugin.yaml`. Check:

- [ ] File exists at plugin root
- [ ] Valid YAML (parseable, mapping at top level)
- [ ] `name` field handling matches the intended distribution target: for community / Plugin Index plugins it must be present, non-empty, match `^[a-z0-9_]+$`, and match the directory name; for local-only plugins, a missing `name` is a WARN rather than a FAIL
- [ ] `title` present and non-empty
- [ ] `description` present and non-empty
- [ ] `version` present, follows semver or simple `x.y.z` format
- [ ] `settings_sections` is a list; each value is one of: `agent`, `external`, `mcp`, `developer`, `backup`
- [ ] `per_project_config` and `per_agent_config` are booleans (if present)
- [ ] `always_enabled` is `false` or absent (only framework core plugins should use `true`)
- [ ] No unknown fields (warn on extra keys not in the schema)

---

## Phase 2: Structure Validation

Inspect the plugin directory layout:

- [ ] Directory is under `usr/plugins/` (not `plugins/` - that is reserved for core)
- [ ] Directory name matches `^[a-z0-9_]+$`
- [ ] If `api/` exists: contains Python files only; each should subclass `ApiHandler`
- [ ] If `tools/` exists: contains Python files only; each should subclass `Tool`
- [ ] If `extensions/` exists: check subdirs follow `python/<point>/`, `python/_functions/<module>/<qualname>/<start|end>/`, or `webui/<point>/` patterns; flag the retired flattened `python/<module>_<qualname>_<start|end>/` form
- [ ] If `helpers/` exists: shared Python logic (standard directory)
- [ ] If `prompts/` exists: prompt templates (standard directory)
- [ ] If `agents/` exists: agent profiles with `<profile>/agent.yaml` (standard directory)
- [ ] If `conf/` exists: configuration files such as `model_providers.yaml` (standard directory)
- [ ] If `webui/config.html` exists: plugin must declare at least one `settings_sections` entry
- [ ] If `hooks.py` exists: review whether it defines the lifecycle hook functions the plugin appears to rely on, especially `install` and `pre_update` when the plugin needs install-time or update-time behavior
- [ ] If `execute.py` exists: check it has a `main()` function and `if __name__ == "__main__": sys.exit(main())`
- [ ] `LICENSE` at plugin root: Agent Zero does not require it for local plugins, but it is **required** at the repo root before submitting to the Plugin Index. If missing → **WARN** — `LICENSE absent — required for community contribution (Plugin Index); optional for local-only use`
- [ ] `default_config.yaml` (if present): valid YAML
- [ ] No unexpected top-level entries (WARN for anything outside the standard layout)

Standard top-level layout: `plugin.yaml`, `execute.py`, `hooks.py`, `default_config.yaml`, optional `README.md`, `LICENSE`, `__init__.py`, plus `api/`, `tools/`, `extensions/`, `webui/`, `helpers/`, `prompts/`, `agents/`, `conf/`

---

## Phase 3: Code Pattern Review

Read source files and check for violations of Agent Zero conventions.

### Frontend (HTML/JS)

- [ ] Every component that accesses a store uses the Store Gate pattern:
  ```html
  <div x-data>
    <template x-if="$store.myStore">
      <div x-init="$store.myStore.onOpen()" x-destroy="$store.myStore.cleanup()">
        ...
      </div>
    </template>
  </div>
  ```
- [ ] No `alpine:init` event listeners inside HTML files (store logic must be in `.js` files)
- [ ] Alpine stores use `createStore` imported from `/js/AlpineStore.js`
- [ ] No inline error/success `<div>` blocks bound to `store.error` or similar - must use notification system:
  - `toastFrontendError(msg, "Plugin Name")` / `toastFrontendSuccess(...)` etc.
  - Import from `/components/notifications/notification-store.js`
- [ ] Static assets served via `GET /plugins/<name>/...` (not hardcoded absolute paths)
- [ ] Store module imported in HTML `<head>` via `<script type="module" src="/plugins/<name>/webui/store.js">`

### Backend (Python)

- [ ] Correct import paths:
  - `from agent import AgentContext, AgentContextType` (not `helpers.context`)
  - `from initialize import initialize_agent` (not a local reimport)
- [ ] API handlers subclass `ApiHandler` from `python/helpers/api.py`
- [ ] Tools subclass `Tool` from `helpers.tool`
- [ ] Plugin settings read via `get_plugin_config("plugin-name", agent=agent)` from `helpers.plugins`
- [ ] User messages sent via `context.communicate(UserMessage(...))`, not direct socket writes
- [ ] `hooks.py` environment targeting: if installing packages for the agent runtime (not framework), subprocess must explicitly target the correct interpreter (e.g., `/opt/venv/bin/python`)
- [ ] No `sys.executable -m pip install` for agent-runtime deps (that installs into framework runtime instead)

---

## Phase 4: Security + Index Review

### Security checks

- [ ] No hardcoded secrets, API keys, tokens, or passwords in any file
- [ ] No `eval()` or `exec()` on user-supplied input
- [ ] File path operations use safe joins (no concatenation with user input that could escape the sandbox)
- [ ] Subprocess calls do not pass unsanitized user input as shell strings
- [ ] ZIP extraction (if any): path traversal protection in place
- [ ] No outbound network calls to third-party endpoints without user awareness (WARN if present, not automatic FAIL)

### Duplicate detection against the community index

Fetch the current index:
```
https://github.com/agent0ai/a0-plugins/releases/download/generated-index/index.json
```

Check:
- [ ] Plugin `name` does not already exist as a folder in the index
- [ ] No other index entry points to the same `github` URL
- [ ] Plugin purpose is not already covered by an existing index entry (WARN for semantic overlap, not FAIL)

### Community readiness assessment

Summarize whether the plugin is ready for contribution:
- READY: all FAIL items resolved; for Plugin Index submission, no blocking WARN items (a missing `LICENSE` is a WARN but blocks contribution readiness until fixed)
- NEEDS WORK: list specific FAIL items to fix
- OPTIONAL IMPROVEMENTS: list non-blocking WARN items (if the user is only using the plugin locally, a missing `LICENSE` can be noted as optional)

---

## Reporting Format

```
## Plugin Review: <plugin_name>

### Phase 1: Manifest
PASS name: my_plugin
PASS title: My Plugin
FAIL version: missing
...

### Phase 2: Structure
PASS plugin.yaml present
WARN Unexpected file at root: notes.txt
...

### Phase 3: Code Patterns
PASS Store Gating: found in webui/main.html
FAIL Inline error box found in webui/settings.html (use toastFrontendError instead)
...

### Phase 4: Security + Index
PASS No hardcoded secrets found
PASS No duplicate in community index
WARN Outbound HTTP call to external service in api/handler.py:42

### Summary
Status: NEEDS WORK
Fix required: version missing in plugin.yaml, inline error box in webui/settings.html
```

---

## References

- Detailed pattern checklists: read `checklists.md` in this skill directory
- Plugin architecture: `/a0/docs/agents/AGENTS.plugins.md`
- Developer lifecycle guide: `/a0/docs/developer/plugins.md`
- Component system: `/a0/docs/agents/AGENTS.components.md`
- If review passes and user wants to publish: read `/a0/skills/a0-contribute-plugin/SKILL.md`
