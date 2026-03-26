---
name: a0-plugin-router
description: Main entry point for all Agent Zero plugin tasks. Routes to specialist skills for creating, reviewing, contributing, managing, or debugging plugins. Use when the user mentions plugins, asks how the plugin system works, wants to build/install/uninstall/publish/debug a plugin, or asks about the Plugin Hub.
version: 1.0.0
tags: ["plugins", "router", "meta", "create", "review", "contribute", "manage", "plugin-hub"]
trigger_patterns:
  - "plugin"
  - "create plugin"
  - "build plugin"
  - "review plugin"
  - "contribute plugin"
  - "publish plugin"
  - "install plugin"
  - "manage plugin"
  - "plugin hub"
  - "plugin index"
  - "how does the plugin system work"
---

# Agent Zero Plugin Router

## Routing Decision

Classify the user's request and read the appropriate specialist skill immediately.

| User intent | Skill to read |
|---|---|
| Create / build / develop / write a new plugin | Read `/a0/skills/a0-create-plugin/SKILL.md` |
| Review / audit / validate / check a plugin | Read `/a0/skills/a0-review-plugin/SKILL.md` |
| Contribute / publish / submit / share to community | Read `/a0/skills/a0-contribute-plugin/SKILL.md` |
| Install / update / uninstall / remove / browse / scan | Read `/a0/skills/a0-manage-plugin/SKILL.md` |
| Plugin not working / crashing / missing / debug / troubleshoot | Read `/a0/skills/a0-debug-plugin/SKILL.md` |
| Explain / how does it work / architecture | Answer inline using the overview below |

If intent is ambiguous, ask one question before routing:
> "Are you trying to **create** a new plugin, **review** one, **contribute** it to the community, **manage** (install/update/uninstall) plugins, or **debug** a plugin that isn't working?"

If the user says "make a plugin for the community" - start with `a0-create-plugin`, then note that `a0-contribute-plugin` handles the publishing step after the plugin is built and tested.

---

## Plugin System Overview (for explain/explore queries)

### Roots and Discovery

Agent Zero discovers plugins from two roots, in priority order:
1. `usr/plugins/<name>/` - user plugins (your custom plugins go here)
2. `plugins/<name>/` - core system plugins (framework-bundled, do not modify)

A plugin is valid when its directory contains a `plugin.yaml`. Directories starting with `.` are skipped.

### Runtime Manifest (`plugin.yaml`)

Every plugin requires a `plugin.yaml` at its root:

```yaml
name: my_plugin              # required by CI for community plugins (^[a-z0-9_]+$)
title: My Plugin             # UI display name
description: What it does.
version: 1.0.0
settings_sections: [agent]   # which Settings tabs show a subsection
per_project_config: false    # enables project-scoped settings/toggle
per_agent_config: false      # enables agent-profile-scoped settings/toggle
always_enabled: false        # forces ON, disables toggle (framework use only)
```

`settings_sections` valid values: `agent`, `external`, `mcp`, `developer`, `backup`. Use `[]` for none.

### What a Plugin Can Provide

| Directory/File | Purpose |
|---|---|
| `api/` | API handlers (`ApiHandler` subclasses) |
| `tools/` | Agent tools (`Tool` subclasses) |
| `extensions/python/<point>/` and `extensions/python/_functions/<module>/<qualname>/<start_or_end>/` | Backend lifecycle hooks and implicit `@extensible` hooks |
| `extensions/webui/<point>/` | HTML/JS injected into UI breakpoints |
| `webui/config.html` | Plugin settings UI |
| `webui/*.html`, `webui/*.js` | Full plugin pages and Alpine stores |
| `hooks.py` | Framework runtime hooks (install, pre_update, cache, registration) |
| `execute.py` | User-triggered script (setup, maintenance, repair) |
| `default_config.yaml` | Settings defaults |
| `README.md` | Optional locally; strongly recommended for community plugins so Plugin Hub users can inspect the plugin |
| `agents/<profile>/agent.yaml` | Plugin-distributed agent profiles |
| `conf/model_providers.yaml` | Add/override model providers |
| `LICENSE` | Optional under `usr/plugins/`; required at the root of a plugin GitHub repo before submitting to the Plugin Index |

For `@extensible` targets, the only valid implicit hook layout is `extensions/python/_functions/<module>/<qualname>/<start|end>/`. The older flattened `extensions/python/<module>_<qualname>_<start|end>/` folders are obsolete.

### Activation

- Global toggle: `.toggle-1` (ON) / `.toggle-0` (OFF) files in the plugin dir
- Scoped toggles (project/agent) available when `per_project_config` or `per_agent_config` is true
- Default: enabled when no toggle file exists
- `always_enabled: true` forces ON and hides controls (reserved for framework)

### Settings Resolution (highest priority first)

1. `project/.a0proj/agents/<profile>/plugins/<name>/config.json`
2. `project/.a0proj/plugins/<name>/config.json`
3. `usr/agents/<profile>/plugins/<name>/config.json`
4. `usr/plugins/<name>/config.json`
5. `plugins/<name>/default_config.yaml`

### Key API Routes

| Route | Purpose |
|---|---|
| `GET /plugins/<name>/<path>` | Serve static plugin assets |
| `POST /api/plugins/<name>/<handler>` | Call plugin API endpoint |
| `POST /api/plugins` | Management (toggle, config, docs) |

### Deep-Dive References

- Architecture + extension points: `/a0/docs/agents/AGENTS.plugins.md`
- Developer guide: `/a0/docs/developer/plugins.md`
- Component system: `/a0/docs/agents/AGENTS.components.md`
- Modal system: `/a0/docs/agents/AGENTS.modals.md`
