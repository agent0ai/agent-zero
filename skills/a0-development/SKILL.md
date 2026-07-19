---
name: a0-development
description: Development guide for extending Agent Zero from current source and DOX. Use for framework architecture, tools, extensions, API/WebUI handlers, agent profiles, prompts, skills, projects, runtime boundaries, and contribution workflow. Load the focused reference files before giving implementation guidance.
version: 1.1.0
author: Agent Zero Team
tags: ["development", "framework", "agent-zero", "extending", "tools", "extensions", "skills", "api", "agents", "prompts", "dox"]
trigger_patterns:
  - "extend agent zero"
  - "agent zero development"
  - "build agent zero feature"
  - "create agent zero tool"
  - "add extension"
  - "framework development"
  - "agent zero architecture"
  - "how does agent zero work"
  - "create agent zero extension"
  - "add api endpoint"
  - "create agent profile"
  - "agent zero internals"
  - "how does the agent loop work"
  - "extension hook points"
  - "prompt system"
  - "agent profile"
  - "dox"
---

# Agent Zero Development

Use this skill as the entry point for Agent Zero framework development. It is intentionally lean: load only the reference files that match the task, then verify against the current repository before changing code.

## Reality Rules

1. Source and nearest DOX beat memory, examples, and this skill if they disagree.
2. Before editing, read the applicable `AGENTS.md` chain from the repo root to every file you expect to touch.
3. New capabilities should usually be plugins. For plugin-specific work, load `a0-plugin-router` and follow the routed specialist skill.
4. Do not assume ports. Discover WebUI host/port from startup output, launcher or Docker mapping, or explicit `--host`, `--port`, `WEB_UI_HOST`, and `WEB_UI_PORT` configuration.
5. In Docker, framework checks belong to `/opt/venv-a0` and agent/user code execution belongs to `/opt/venv`. Do not use one runtime as proof for the other.
6. Treat `/a0/` as the runtime framework root inside Docker. In local development it means the repository root. If a live container matters, prove that `/a0` matches the checkout before trusting source-only conclusions.
7. Do not document or change ignored `usr/` or `tmp/` runtime state unless the user explicitly asks.

## Reference Map

Load references with:

```json
{"tool_name": "skills_tool:read_file", "tool_args": {"skill_name": "a0-development", "file_path": "references/<file>.md"}}
```

| Need | Read |
|---|---|
| Runtime split, root layout, discovery order, path and port boundaries | `references/architecture-runtime.md` |
| DOX edit workflow, when to update docs, file-level DOX checks | `references/dox-workflow.md` |
| Tool contracts, locations, prompts, and verification | `references/tools.md` |
| Python/WebUI extension discovery, hook points, ordering, implicit hooks | `references/extensions.md` |
| HTTP API, WebSocket handlers, WebUI extension surfaces | `references/api-webui.md` |
| Agent profiles, prompts, skills, projects | `references/agents-prompts-skills-projects.md` |
| Plugin-first workflow, where to put new work, handoffs to plugin skills | `references/plugins-workflow.md` |

## Working Flow

1. Classify the request: tool, extension, API/WebUI, profile, prompt, skill, project, plugin, runtime, or docs.
2. Read the root `AGENTS.md`, then the nearest child `AGENTS.md` files for the target paths.
3. Read the focused reference file from this skill.
4. Inspect the current source files named by the reference before making a claim or patch.
5. Keep changes narrow and in the repo-owned surface. Prefer `usr/` for user-created runtime content, but do not document ignored user state unless requested.
6. Update DOX when a durable contract, path, behavior, workflow, responsibility, or verification rule changes.
7. Run targeted checks from the relevant DOX file. For skill-only changes, at minimum verify frontmatter parsing, reference paths, and markdown sanity.

## Handoffs

- Plugin creation: load `a0-create-plugin`.
- Plugin management or installation: load `a0-manage-plugin`.
- Plugin debugging: load `a0-debug-plugin`.
- Plugin review or publishing: load `a0-review-plugin` or `a0-contribute-plugin`.
- Agent profile creation: load `a0-create-agent`.
- Skill creation or skill format work: load `build-skill`.

## Closeout

Report the exact files changed, the grounding checks used, whether DOX was updated or intentionally left unchanged, and what verification ran. If a claim depends on a live Docker runtime, include the runtime proof, not only checkout evidence.
