# Prompt Include

Automatically inject persistent behavioral rules and preferences into the system prompt from project files.

## What It Does

This plugin scans a workspace for `*.promptinclude.md` files, applies gitignore-aware filtering and token budgets, and makes the collected content available for prompt injection.

## Main Behavior

- **Workspace scanning**
  - Recursively searches for files matching `*.promptinclude.md`.
- **Ignore support**
  - Respects ignore patterns derived from gitignore-style content.
- **Budgeted inclusion**
  - Applies per-file and total token limits.
  - Crops oversized files when they partially fit within the remaining token budget.
- **Structured scan result**
  - Returns included file content together with path, token count, status, and skipped count.

## Key Files

- **Scanner**
  - `helpers/scanner.py` implements file discovery, ignore handling, token budgeting, and trimming.
- **Configuration**
  - `default_config.yaml` contains prompt-include scanning defaults.
- **Prompts and UI**
  - `prompts/` and `webui/` provide integration with the broader app.

## Configuration Scope

- **Settings section**: `agent`
- **Per-project config**: `true`
- **Per-agent config**: `true`

## Plugin Metadata

- **Name**: `_promptinclude`
- **Title**: `Prompt Include`
- **Description**: Persistent behavioral rules and preferences auto-injected into system prompt.
