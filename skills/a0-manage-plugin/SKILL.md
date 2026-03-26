---
name: a0-manage-plugin
description: Manage Agent Zero plugins lifecycle: browse the Plugin Hub, scan for security, install from Git/ZIP/Plugin Hub, update, uninstall, enable, disable, debug, and troubleshoot. Use when asked to install, update, uninstall, remove, scan, find, search, enable, disable, debug, or troubleshoot a plugin.
version: 1.2.0
tags: ["plugins", "install", "uninstall", "update", "scan", "security", "debug", "troubleshoot", "plugin-hub", "manage"]
trigger_patterns:
  - "install plugin"
  - "uninstall plugin"
  - "remove plugin"
  - "delete plugin"
  - "update plugin"
  - "scan plugin"
  - "debug plugin"
  - "troubleshoot plugin"
  - "browse plugins"
  - "search plugins"
  - "plugin not working"
  - "enable plugin"
  - "disable plugin"
  - "plugin hub"
  - "list plugins"
---

# Agent Zero Plugin Management

## Action Routing

Identify what the user needs and jump to the relevant section:

| User need | Section |
|---|---|
| Find / search / browse available plugins | [Browse Plugin Hub](#browse-plugin-hub) |
| Scan a plugin for security issues | [Security Scan](#security-scan) |
| Install a plugin | [Install a Plugin](#install-a-plugin) |
| Update an installed plugin | [Update a Plugin](#update-a-plugin) |
| Uninstall / remove a plugin | [Uninstall a Plugin](#uninstall-a-plugin) |
| Enable or disable a plugin | [Activation](#activation) |
| Plugin not loading / crashing / missing | Read `/a0/skills/a0-debug-plugin/SKILL.md` |
| Explain how plugin discovery works | Read `/a0/skills/a0-debug-plugin/SKILL.md` |

---

## Browse Plugin Hub

Fetch the current community index:

```python
import urllib.request, json

url = "https://github.com/agent0ai/a0-plugins/releases/download/generated-index/index.json"
with urllib.request.urlopen(url, timeout=30) as resp:
    index = json.loads(resp.read())

plugins = index.get("plugins", {})
```

Each entry in `plugins` is keyed by plugin name with fields: `title`, `description`, `github`, `tags`, `thumbnail` (URL if available).

**To search**: filter by keyword in `title`, `description`, or `tags`.

**To list installed plugins** locally:
```bash
ls /a0/usr/plugins/
```

**Alternatively via UI**: Open the Plugins dialog in Agent Zero and switch to the **Browse** tab (or click **Install** in the toolbar to open the Plugin Hub).

---

## Security Scan

The `_plugin_scan` plugin provides an LLM-driven security scanner that clones the repository, reads all files, and produces a structured markdown report covering 6 checks: structure match, static code review, agent manipulation detection, remote communication, secrets access, and obfuscation.

### Pre-install scan protocol (follow this for every install)

**Always offer to scan before installing.** If the user hasn't explicitly declined, say:

> "Before installing, I strongly recommend running a security scan on this plugin. Third-party plugins execute code inside your Agent Zero environment. Should I scan it first? The scan typically takes 2-4 minutes."

If the user declines, acknowledge but warn once:

> "Understood, skipping the scan. Note that installing unscanned third-party code carries security risks. Proceeding with installation."

Then proceed to install. **Do not ask again** after the user declines.

### Running a scan

```python
# (after authentication setup - see Install section)
resp = s.post(
    f"{BASE}/api/plugins/_plugin_scan/plugin_scan_run",
    json={
        "git_url": "https://github.com/<user>/<plugin-repo>",
        "checks": ["structure", "codeReview", "agentManipulation", "remoteComms", "secrets", "obfuscation"],
    },
    headers={"X-CSRF-Token": token, "Origin": ORIGIN},
    timeout=600,   # set generously - the scan clones the repo, reads all files, runs 6 LLM checks
)
data = resp.json()
```

Always pass the full `checks` list explicitly - omitting it has been observed to cause intermittent failures. To run a subset, remove unwanted keys from the list.

### Interpreting the result

```python
report = data["report"]   # full markdown security report
```

Present the full `report` to the user. Read the Summary section to determine the overall verdict (**Safe** / **Caution** / **Dangerous**) and act accordingly:

| Verdict | Action |
|---|---|
| **Safe** | Offer to proceed with installation |
| **Caution** | Show findings, warn that issues were found, ask for explicit confirmation: "Some warnings were found. Do you still want to install?" |
| **Dangerous** | Show findings, **strongly advise against installing**: "The scanner flagged serious security issues. I strongly recommend NOT installing this plugin. Do you want to proceed anyway?" Only install if user explicitly confirms. |

If the scan times out or errors (500), inform the user and ask whether to proceed without a scan.

---

## Install a Plugin

> **Always use the HTTP API or UI.** Never import Agent Zero framework modules directly from `code_execution_tool` - the agent runs in a separate Python runtime (`/opt/venv`) that does not have the framework's dependencies. All programmatic installs must go through HTTP.

### How installed state works

The Plugin Hub marks a plugin as **Installed** by cross-referencing Plugin Hub keys against `usr/plugins/` directory names at request time. To appear installed:
- The plugin directory must exist at `usr/plugins/<name>/` with a valid `plugin.yaml`
- If the plugin ships extensions, the framework will register both named extension points under `extensions/python/<point>/` and implicit `@extensible` hooks under `extensions/python/_functions/<module>/<qualname>/<start|end>/` after the plugin cache is refreshed
- The framework plugin cache must be cleared (the API handles this automatically)
- Re-fetching the Plugin Hub index will then show it as installed

### API authentication (required for all HTTP calls)

The Agent Zero API uses CSRF protection. The `Origin` header is **always required** - without it the CSRF endpoint returns `ok: false` even when login is disabled.

**Step 1: Set the base URL.** Agent Zero listens on port 80 inside Docker (the standard deployment):

```python
import requests

BASE = "http://localhost"   # port 80 inside Docker
# If running outside Docker (dev mode), check: os.environ.get("WEB_UI_PORT", "5000")
```

**Step 2: Bootstrap the session and get the CSRF token:**

```python
s = requests.Session()
ORIGIN = BASE  # Origin must match a localhost pattern

r = s.get(f"{BASE}/api/csrf_token", headers={"Origin": ORIGIN}, timeout=10)
data = r.json()

if not data.get("ok"):
    raise RuntimeError(f"CSRF bootstrap failed: {data.get('error')}")

token = data["token"]
runtime_id = data["runtime_id"]

# Set the CSRF cookie (required alongside the header)
s.cookies.set(f"csrf_token_{runtime_id}", token)
```

Reuse `s`, `BASE`, `ORIGIN`, and `token` for all subsequent API calls. Always include `headers={"X-CSRF-Token": token, "Origin": ORIGIN}` on every request.

### Method 1: From a Git URL (via HTTP API) - preferred for programmatic use

```python
# (after authentication setup above)
resp = s.post(
    f"{BASE}/api/plugins/_plugin_installer/plugin_install",
    json={
        "action": "install_git",
        "git_url": "https://github.com/<user>/<plugin-repo>",
        # "git_token": "<token>",    # optional, for private repos
        # "plugin_name": "override"  # optional, override directory name
    },
    headers={"X-CSRF-Token": token, "Origin": ORIGIN},
    timeout=120,
)
print(resp.json())
```

This runs the full pipeline in the framework runtime: clone → validate → place in `usr/plugins/` → run `install` hook → clear plugin cache → notify frontend. The Plugin Hub will show the plugin as installed on the next index fetch.

### Method 2: From the Plugin Hub (UI) - preferred for interactive use

1. Open the Plugins dialog
2. Go to the **Browse** tab (or click **Install**)
3. Find the plugin, click it, click **Install**

The UI handles everything including marking the plugin as installed in the Plugin Hub view.

### Method 3: From a ZIP file (via HTTP API)

```python
# (after authentication setup above)
with open("plugin.zip", "rb") as f:
    resp = s.post(
        f"{BASE}/api/plugins/_plugin_installer/plugin_install",
        data={"action": "install_zip"},
        files={"plugin_file": f},
        headers={"X-CSRF-Token": token, "Origin": ORIGIN},
    )
print(resp.json())
```

Or via UI: Plugins dialog -> Install -> ZIP tab -> upload file.

### Manual install (last resort only)

Only use this if the HTTP API is genuinely unavailable (not because of import errors - those mean you must use the HTTP API instead).

```bash
git clone https://github.com/<user>/<repo> /a0/usr/plugins/<plugin_name>
```

After cloning, the plugin is on disk but the framework doesn't know about it. Clear the cache and notify the frontend by calling the toggle API (off then on) which triggers `after_plugin_change()` internally:

```python
# (after authentication setup above)
for state in [False, True]:
    s.post(
        f"{BASE}/api/plugins",
        json={"action": "toggle_plugin", "plugin_name": "<plugin_name>", "enabled": state},
        headers={"X-CSRF-Token": token, "Origin": ORIGIN},
    )
```

Or simply restart Agent Zero - on startup it re-scans `usr/plugins/` fresh.

---

## Update a Plugin

> The framework update flow now calls `pre_update()` from `hooks.py` immediately before pulling new plugin code into place, then re-runs `install()` after the update if that hook exists.

### Checking for updates

**Do not compare version strings.** Contributors often forget to bump the version, so a matching version does not mean the plugin is current. Check for new commits instead:

```bash
# Is the plugin a git repo?
git -C /a0/usr/plugins/<name> rev-parse --is-inside-work-tree 2>/dev/null

# Compare local HEAD with remote HEAD (no fetch required)
LOCAL=$(git -C /a0/usr/plugins/<name> rev-parse HEAD)
REMOTE=$(git -C /a0/usr/plugins/<name> ls-remote origin HEAD | awk '{print $1}')
echo "Local:  $LOCAL"
echo "Remote: $REMOTE"
[ "$LOCAL" = "$REMOTE" ] && echo "Up to date" || echo "Update available"
```

If they differ, new commits exist on the remote - report this to the user as "update available" regardless of whether the version field changed.

### Applying the update

If installed via Git:

```bash
cd /a0/usr/plugins/<name>
git pull origin main
```

Then refresh the framework cache via the toggle API (see [API authentication](#api-authentication-required-for-all-http-calls) for session setup):

```python
# (after authentication setup)
for state in [False, True]:
    s.post(
        f"{BASE}/api/plugins",
        json={"action": "toggle_plugin", "plugin_name": "<name>", "enabled": state},
        headers={"X-CSRF-Token": token, "Origin": ORIGIN},
    )
```

If not a git repo: uninstall via the API (see [Uninstall a Plugin](#uninstall-a-plugin)), then reinstall via the Git method above.

---

## Uninstall a Plugin

> **Safety rules - read before proceeding**:
> - **Core plugins** (in `plugins/`, not `usr/plugins/`) cannot be uninstalled via the API - the framework blocks it. Disable them instead (see [Activation](#activation)).
> - **Always ask for explicit user confirmation** before uninstalling: "Are you sure you want to uninstall `<name>`? This will delete all plugin files and cannot be undone."
> - Uninstalling does NOT delete plugin config files stored in `usr/agents/` or project scopes.

### Standard uninstall (via API)

Uses the framework's `uninstall_plugin` which calls the plugin's `uninstall` hook (if defined) before deleting. Requires an authenticated session (see [API authentication](#api-authentication-required-for-all-http-calls) in the Install section):

```python
# (after authentication setup from the Install section)
resp = s.post(
    f"{BASE}/api/plugins",
    json={
        "action": "delete_plugin",
        "plugin_name": "<name>",
    },
    headers={"X-CSRF-Token": token, "Origin": ORIGIN},
)
print(resp.json())
```

This is the preferred method. The framework will:
1. Call `uninstall()` from `hooks.py` (if present) - runs cleanup
2. Delete the `usr/plugins/<name>/` directory
3. Notify the frontend to refresh the plugin list

**Via UI**: Plugins dialog -> find the plugin -> click the delete (trash) icon -> confirm.

### Fallback: direct folder removal

Use this only if the standard uninstall fails (e.g., broken `uninstall` hook that crashes or hangs):

```bash
# Confirm the plugin is a custom one (usr/plugins/) - NEVER delete from plugins/
ls /a0/usr/plugins/<name>/

# Remove it
rm -rf /a0/usr/plugins/<name>/
```

After manual removal, refresh the plugin list via the UI or restart Agent Zero.

---

## Activation

Plugins are enabled/disabled via toggle files:
- `.toggle-1` = explicitly ON
- `.toggle-0` = explicitly OFF
- No file = default (enabled for most plugins)

**Enable a plugin**:
```bash
rm -f /a0/usr/plugins/<name>/.toggle-0
touch /a0/usr/plugins/<name>/.toggle-1
```

**Disable a plugin**:
```bash
rm -f /a0/usr/plugins/<name>/.toggle-1
touch /a0/usr/plugins/<name>/.toggle-0
```

Via UI: Plugins dialog -> find the plugin -> use the toggle switch.

Plugins with `always_enabled: true` in `plugin.yaml` cannot be toggled (framework core plugins only).

**Scoped toggles** (when `per_project_config` or `per_agent_config` is true): use the "Switch" modal in the UI, or place toggle files in the appropriate scoped path:
- Project scope: `project/.a0proj/plugins/<name>/.toggle-1`
- Agent profile scope: `usr/agents/<profile>/plugins/<name>/.toggle-1`

---

## References

- Plugin architecture: `/a0/docs/agents/AGENTS.plugins.md`
- Developer lifecycle guide: `/a0/docs/developer/plugins.md`
- Debug a broken plugin: read `/a0/skills/a0-debug-plugin/SKILL.md`
- Create a new plugin: read `/a0/skills/a0-create-plugin/SKILL.md`
- Review a plugin: read `/a0/skills/a0-review-plugin/SKILL.md`
