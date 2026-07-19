---
name: a0-debug-plugin
description: Diagnose and fix Agent Zero plugin problems. Covers plugin not appearing, won't enable, API endpoints not responding, frontend store errors, extension point injection, settings resolution, hooks.py issues, and log inspection. Use when a plugin is not working, not loading, crashing, missing from the list, or behaving unexpectedly.
version: 1.0.0
tags: ["plugins", "debug", "troubleshoot", "fix", "diagnose", "error", "broken"]
trigger_patterns:
  - "plugin not working"
  - "plugin not loading"
  - "plugin not showing"
  - "plugin broken"
  - "plugin error"
  - "plugin missing"
  - "plugin crash"
  - "debug plugin"
  - "troubleshoot plugin"
  - "fix plugin"
---

# Agent Zero Plugin Debugger

Work through these checks in order. Stop at the first failure and fix it before continuing.

---

## 1. Plugin not appearing in the Plugins list

```bash
# Check plugin.yaml exists
ls /a0/usr/plugins/<name>/plugin.yaml

# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('/a0/usr/plugins/<name>/plugin.yaml'))"

# Check directory name doesn't start with '.'
ls /a0/usr/plugins/
```

Common causes:
- Missing `plugin.yaml` - plugin not discovered
- Invalid YAML syntax - plugin skipped silently
- Directory name starts with `.` - skipped by discovery

---

## 2. Plugin appears but won't enable

```bash
# Check toggle state
ls -la /a0/usr/plugins/<name>/.toggle-*

# Check for conflicting scoped toggles
ls -la project/.a0proj/plugins/<name>/.toggle-* 2>/dev/null
ls -la /a0/usr/agents/default/plugins/<name>/.toggle-* 2>/dev/null
```

---

## 3. API endpoint not responding

- Verify the handler file is in `api/` and subclasses `ApiHandler`
- Route format: `POST /api/plugins/<plugin_name>/<handler_filename_without_.py>`
- Check for Python import errors on startup (check Agent Zero logs)
- Verify correct import paths: `from agent import AgentContext` not `from helpers.context import AgentContext`

```bash
# Check for syntax errors in handler
python3 -m py_compile /a0/usr/plugins/<name>/api/my_handler.py
```

---

## 4. Frontend component not rendering / store errors

- Check browser console for Alpine.js errors
- Verify the store file is imported in HTML `<head>` via `<script type="module">`
- Confirm Store Gate pattern is used (missing gate = undefined error if store not yet loaded)
- Verify store name in `createStore(...)` matches `$store.<name>` in templates

---

## 5. Extension point not injecting

- Check the HTML file is in `extensions/webui/<correct_breakpoint_name>/`
- Verify the breakpoint name exists in core UI (check `webui/index.html` or component files for `<x-extension id="...">`)
- Common breakpoints: `sidebar-quick-actions-main-start`, `plugins-list-header-buttons`, `chat-input-bottom-actions-end`
- Confirm the HTML file has a root element with `x-data` and an `x-move-*` directive

For backend extension hooks:
- Named lifecycle hooks must live under `extensions/python/<point>/`
- Implicit `@extensible` hooks must live under `extensions/python/_functions/<module>/<qualname>/<start|end>/`
- The retired flattened form `extensions/python/<module>_<qualname>_<start|end>/` no longer loads

---

## 6. Settings not saving / loading wrong values

Config resolution order (highest priority first):
1. `project/.a0proj/agents/<profile>/plugins/<name>/config.json`
2. `project/.a0proj/plugins/<name>/config.json`
3. `usr/agents/<profile>/plugins/<name>/config.json`
4. `usr/plugins/<name>/config.json`
5. `plugins/<name>/default_config.yaml`

```bash
# Find which config file is actually being loaded
find /a0 -path "*/plugins/<name>/config.json" 2>/dev/null
```

---

## 7. hooks.py install hook not running

The `install()` hook is called automatically by the plugin installer after placement. If it didn't run:
- Check the function is named exactly `install` (not `on_install` or similar)
- Check for exceptions in the function (add try/except with print for debugging)
- Manually trigger in the **framework runtime** (not via `code_execution_tool` python - that uses `/opt/venv`, not `/opt/venv-a0`):

```bash
cd /a0 && /opt/venv-a0/bin/python -c "
import asyncio
from helpers.plugins import call_plugin_hook
asyncio.run(call_plugin_hook('<plugin_name>', 'install'))
print('Done')
"
```

If the `pre_update()` hook is not running before plugin updates:
- Check the function is named exactly `pre_update`
- Check for exceptions in the function
- Manually trigger it in the **framework runtime** the same way:

```bash
cd /a0 && /opt/venv-a0/bin/python -c "
import asyncio
from helpers.plugins import call_plugin_hook
asyncio.run(call_plugin_hook('<plugin_name>', 'pre_update'))
print('Done')
"
```

If the `uninstall()` hook is not running when the plugin is removed:
- Check the function is named exactly `uninstall` (not `on_uninstall` or similar)
- Check for exceptions in the function
- The `uninstall()` hook is called by `uninstall_plugin()` in `helpers/plugins.py` before the plugin directory is deleted. If the user removed the plugin manually (`rm -rf`), the hook was bypassed — always use the API or UI to uninstall.
- Manually trigger it in the **framework runtime** the same way:

```bash
cd /a0 && /opt/venv-a0/bin/python -c "
import asyncio
from helpers.plugins import call_plugin_hook
asyncio.run(call_plugin_hook('<plugin_name>', 'uninstall'))
print('Done')
"
```

---

## 8. Check Agent Zero logs

```bash
# Find recent log files
ls -lt /a0/logs/*.html | head -5
```

Plugin-related errors appear as Python tracebacks mentioning the plugin path.

---

## How Plugin Discovery Works

1. Agent Zero walks `usr/plugins/` then `plugins/` at startup
2. Any directory containing `plugin.yaml` is treated as a plugin
3. `usr/plugins/<name>` takes priority over `plugins/<name>` when both exist (user overrides core)
4. Toggle state is evaluated: `.toggle-0` disables, `.toggle-1` enables, no file = enabled by default
5. Enabled plugins have their `extensions/`, `api/`, `tools/`, etc. registered into the runtime, including both named extension points and implicit `_functions/...` extensible hooks

Plugins are re-scanned when:
- Agent Zero restarts
- A plugin is installed/removed via the installer
- The "Refresh" action is triggered in the Plugins UI

---

## References

- Plugin architecture: `/a0/docs/agents/AGENTS.plugins.md`
- Manage (install/update/uninstall): read `/a0/skills/a0-manage-plugin/SKILL.md`
