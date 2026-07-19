---
name: a0-contribute-plugin
description: Guide for publishing an Agent Zero plugin to the community Plugin Index (a0-plugins repo). Covers GitHub repo setup, index.yaml creation, CI validation rules, and PR submission. Use when the user wants to share, publish, submit, or contribute a plugin to the Plugin Hub so other Agent Zero users can find and install it.
version: 1.0.0
tags: ["plugins", "contribute", "publish", "plugin-hub", "community", "index", "PR"]
trigger_patterns:
  - "contribute plugin"
  - "publish plugin"
  - "share plugin"
  - "submit plugin"
  - "contribute to plugin hub"
  - "plugin index"
  - "community plugin"
  - "open source plugin"
---

# Agent Zero Plugin Contribution

This skill guides publishing a plugin to the [Plugin Index](https://github.com/agent0ai/a0-plugins), making it discoverable and installable by all Agent Zero users.

---

## Prerequisites

Before starting, verify:

1. Plugin exists and works locally in `/a0/usr/plugins/<name>/`
2. Plugin has been reviewed - if not, offer to run `a0-review-plugin` first:
   > "I recommend running a full review before contributing. Should I do that now?"
3. User has a GitHub account and `git` / `gh` CLI available

---

## Step 0: Ask Automation Preference

Before doing any git work, ask:

> "Do you want me to handle the git operations (fork, branch, commit, PR) automatically, or would you prefer I give you the steps to run manually?"

- **Automatic**: proceed using `gh` and `git` commands via the code execution tool
- **Manual**: provide exact commands at each step for the user to run

---

## Step 1: Prepare the Plugin GitHub Repository

The plugin must live in its **own standalone GitHub repository** with plugin contents at the **repo root** (not inside a subfolder).

### Required repo structure

```text
your-plugin-repo/           <- GitHub repository root
├── plugin.yaml             <- runtime manifest (REQUIRED)
├── README.md               <- strongly recommended (shown in Plugin Hub detail view)
├── LICENSE                 <- REQUIRED for Plugin Index submission (place at repo root)
├── default_config.yaml     <- optional
├── api/                    <- API handlers
├── tools/                  <- agent tools
├── helpers/                <- shared Python logic
├── prompts/                <- prompt templates
├── agents/                 <- agent profiles
├── conf/                   <- config files (e.g. model_providers.yaml)
├── extensions/             <- lifecycle, UI, and implicit @extensible hooks
└── webui/                  <- frontend pages, stores, components
```

Inside `extensions/`, use `python/<point>/` for named lifecycle hooks, `python/_functions/<module>/<qualname>/<start|end>/` for implicit `@extensible` hooks, and `webui/<point>/` for UI breakpoints. Do not publish the retired flattened `python/<module>_<qualname>_<start|end>/` form.

### Runtime `plugin.yaml` requirements

The remote `plugin.yaml` must include a **`name` field** - this is validated by CI and must exactly match the index folder name:

```yaml
name: my_plugin              # REQUIRED - must match index folder name (^[a-z0-9_]+$)
title: My Plugin
description: What this plugin does.
version: 1.0.0
settings_sections: []
per_project_config: false
per_agent_config: false
always_enabled: false
```

If the plugin was built locally, help the user create the GitHub repo and push it:

```bash
# Create repo (automatic mode - using gh CLI)
gh repo create <repo-name> --public --description "Agent Zero plugin: <title>"
git init
git add .
git commit -m "feat: initial plugin commit"
git remote add origin https://github.com/<user>/<repo-name>.git
git push -u origin main
```

---

## Step 2: Choose the Index Folder Name

The folder name in the index must:
- Match the `name` field in your remote `plugin.yaml` **exactly**
- Follow `^[a-z0-9_]+$` (lowercase letters, numbers, underscores - **no hyphens**)
- Be unique in the index
- Not start with `_` (reserved for internal use)

Verify uniqueness by fetching the current index:
```
https://github.com/agent0ai/a0-plugins/releases/download/generated-index/index.json
```

Check that the intended name does not appear as a key in `plugins`.

---

## Step 3: Create the Index Submission

### Fork and set up

```bash
# Automatic mode
gh repo fork https://github.com/agent0ai/a0-plugins --clone --remote
cd a0-plugins
git checkout -b add-<plugin_name>
```

### Create the plugin folder

```bash
mkdir -p plugins/<plugin_name>
```

### Create `index.yaml`

The index uses **`index.yaml`** (not `plugin.yaml`). These are different schemas:

```yaml
title: My Plugin
description: One-sentence description of what the plugin does for the user.
github: https://github.com/<user>/<repo-name>
tags:
  - tools
  - example
```

Optional additional fields:
```yaml
screenshots:
  - https://raw.githubusercontent.com/<user>/<repo>/main/docs/screenshot1.png
  - https://raw.githubusercontent.com/<user>/<repo>/main/docs/screenshot2.webp
```

### Recommended tags

Use tags from https://github.com/agent0ai/a0-plugins/blob/main/TAGS.md (up to 5).
Common tags: `tools`, `automation`, `workflow`, `api`, `web`, `database`, `memory`, `integration`, `security`, `development`, `llm`, `agents`

### Optional thumbnail

Add a square image named `thumbnail.png`, `thumbnail.jpg`, or `thumbnail.webp` (max 20 KB, must be square aspect ratio) to `plugins/<plugin_name>/`.

---

## Step 4: Pre-validate Before PR

Run these checks locally before opening the PR (mirrors what CI will verify):

| Check | Rule |
|---|---|
| `index.yaml` exists in `plugins/<name>/` | Required |
| Only `index.yaml` + optional thumbnail in the folder | No other files/subdirs |
| `title` length | Max 50 characters |
| `description` length | Max 500 characters |
| `index.yaml` total length | Max 2000 characters |
| `tags` count | Max 5 |
| `screenshots` count | Max 5, each URL must be reachable |
| `github` URL | Points to existing public repo |
| Remote `plugin.yaml` | Exists at repo root |
| Remote `plugin.yaml` `name` field | Matches index folder name exactly |
| Remote `LICENSE` | Exists at repo root (Plugin Index policy) |
| Folder name pattern | `^[a-z0-9_]+$`, no leading `_` |
| `github` URL uniqueness | Not already in the index for another plugin |

Verify the remote `plugin.yaml` name match:
```bash
curl -s https://raw.githubusercontent.com/<user>/<repo>/main/plugin.yaml | grep "^name:"
# Expected output: name: <plugin_name>
```

---

## Step 5: Commit and Open PR

```bash
# Add and commit
git add plugins/<plugin_name>/
git commit -m "feat: add <plugin_name> plugin"

# Push and open PR
git push origin add-<plugin_name>
gh pr create \
  --repo agent0ai/a0-plugins \
  --title "feat: add <plugin_name>" \
  --body "## Plugin: <title>

<description>

- GitHub: <github_url>
- Tags: <tags>"
```

### PR rules

- One plugin per PR (adding exactly one new folder under `plugins/`)
- CI validates automatically on open/sync/reopen
- A human maintainer reviews after CI passes
- If PR has no activity for 7+ days after CI failure it may be auto-closed

---

## Two Schemas at a Glance

| File | Location | Purpose | Key fields |
|---|---|---|---|
| `plugin.yaml` | Your plugin's GitHub repo root | Runtime manifest (drives Agent Zero behavior) | `name` (required!), `title`, `description`, `version`, `settings_sections`, `per_project_config`, `per_agent_config`, `always_enabled` |
| `index.yaml` | `a0-plugins/plugins/<name>/` | Index manifest (drives discoverability) | `title`, `description`, `github`, `tags`, `screenshots` |

**Never mix these up.** They have different schemas and different purposes.

---

## References

- Plugin architecture: `/a0/docs/agents/AGENTS.plugins.md`
- Developer lifecycle guide: `/a0/docs/developer/plugins.md`
- Plugin Index repo: https://github.com/agent0ai/a0-plugins
- Recommended tags: https://github.com/agent0ai/a0-plugins/blob/main/TAGS.md
- Review before contributing: read `/a0/skills/a0-review-plugin/SKILL.md`
- Build the plugin first: read `/a0/skills/a0-create-plugin/SKILL.md`
