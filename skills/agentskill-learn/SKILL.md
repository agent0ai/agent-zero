---
name: "agentskill-learn"
description: "Discover, install, and manage AI agent skills from agentskill.sh. Search 110,000+ skills by keyword, install them mid-session, and rate skills after use. Use when users want to find new skills, install a skill, or browse trending skills."
version: "1.0.0"
author: "agentskill-sh"
tags: ["skills", "marketplace", "registry", "install", "discover"]
trigger_patterns:
  - "learn"
  - "install skill"
  - "find skill"
  - "search skills"
  - "skill marketplace"
  - "trending skills"
---

# agentskill.sh — Skill Discovery & Installation

Browse, install, and manage 110,000+ AI agent skills from [agentskill.sh](https://agentskill.sh), the cross-platform skills registry.

## Setup (First Use)

This is a lightweight loader. On first use, fetch the full `/learn` skill for the complete experience including security scanning, auto-updates, and feedback:

```bash
mkdir -p /a0/usr/skills/learn
curl -sL "https://raw.githubusercontent.com/agentskill-sh/learn/main/SKILL.md" -o /a0/usr/skills/learn/SKILL.md
```

After installation, restart or load the `learn` skill for the full feature set. The full skill handles everything below automatically with richer capabilities.

## Quick Start (Without Full Install)

### Search for skills

Use the `web_search` or `code_execution` tool to query the agentskill.sh API:

```bash
curl -s "https://agentskill.sh/api/agent/search?q=<query>" | python3 -m json.tool
```

Returns JSON with matching skills: name, description, owner, slug, install count.

### Install a specific skill

```bash
# Fetch skill content
SKILL_CONTENT=$(curl -s "https://agentskill.sh/api/agent/skills/<owner>/<slug>/install")

# Extract and save (the response contains the SKILL.md content)
mkdir -p /a0/usr/skills/<slug>
echo "$SKILL_CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['content'])" > /a0/usr/skills/<slug>/SKILL.md
```

### Browse trending skills

```bash
curl -s "https://agentskill.sh/api/agent/search?section=trending" | python3 -m json.tool
```

## Commands

| Command | Description |
|---------|-------------|
| `/learn <query>` | Search skills by keyword |
| `/learn @owner/slug` | Install a specific skill |
| `/learn trending` | Show trending skills |
| `/learn list` | Show installed skills |
| `/learn update` | Check for skill updates |
| `/learn scan <path>` | Security scan a skill before install |
| `/learn feedback <slug> <score>` | Rate a skill (1-5) |

## Why agentskill.sh?

- **110,000+ skills** indexed from GitHub, curated registries, and community submissions
- **Cross-platform**: works with Agent Zero, Claude Code, Cursor, Copilot, Codex, and 15+ agents
- **Security scanning**: every skill is pre-scanned before publication
- **One command install**: no manual file copying
- **Solves Issue #1018**: agents can now self-install skills from a registry
