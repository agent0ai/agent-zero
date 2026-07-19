# Commands

YAML-configured slash commands for Agent Zero.

This plugin lets you define reusable `/commands` as `.command.yaml` files with either:

- a `.txt` template body
- a `.py` script hook

Commands are managed from the plugin modal and can be inserted directly from the chat composer with prefix syntax (`/goal objective`) or an exact trailing command (`objective /goal`).

## Features

- `.command.yaml` config files with command metadata
- Text template commands with `{}` placeholders and parsed args
- Python hook commands with parsed args and optional chat history payload
- Unified parser for positional args, free-form tail, and flags
- Prefix and postfix command resolution for WebUI and remote/AI-sent messages
- Scope-aware command resolution across project and global scopes
- Built-in A0 CLI connector command pack for common session, queue, model, project, browser, and connector status commands
- Slash picker in the chat composer with keyboard navigation and create-on-empty flow

## Command File Model

Each command is defined by one config file plus one content file in the same scope directory.
Set `webui_hidden: true` to keep a command resolvable while omitting it from the chat composer picker.

Example text command:

`scan.command.yaml`

```yaml
name: scan
description: Scan a Git repository.
argument_hint: /scan --git-url https://github.com/org/repo
type: text
template_path: scan.txt
```

`scan.txt`

```txt
Please scan repository: {args.flags.git_url}

Raw input:
{raw}
```

Example python hook command:

`optimize.command.yaml`

```yaml
name: optimize
description: Optimize the current request.
argument_hint: /optimize 30%
type: script
script_path: optimize.py
include_history: true
```

`optimize.py`

```python
def run(payload):
    args = payload["arguments"]
    pct = args["positional"][0] if args["positional"] else "10%"
    return {
        "text": f"Optimize this response by {pct}.",
        "effects": [],
    }
```

## Argument Parsing

The parser supports:

- Positional input: `/scan https://github.com/org/repo`
- Postfix input: `https://github.com/org/repo /scan`
- Long flags: `/scan --git-url https://github.com/org/repo`
- Long flags with equals: `/scan --git-url=https://github.com/org/repo`
- Short flags and bundles: `/scan -v -q` or `/scan -vq`

Parsed data is available to:

- Text templates via `{}` placeholders:
  - `{raw}`
  - `{args.positional.0}`
  - `{args.flags.git_url}`
- Python scripts via `payload["arguments"]`

## Script Hook Contract

Python hook file must expose:

```python
def run(payload): ...
```

It can return:

- `str` (used as replacement text)
- `dict` with:
  - `text: str` (replacement text)
  - `effects: list[dict]`

Supported frontend effects:

- `{"type": "replace_input", "text": "..."}`
- `{"type": "append_input", "text": "..."}`
- `{"type": "toast", "level": "info|error|success", "message": "..."}`
- Built-in UI effects for existing WebUI actions such as chat switching, modals, attachments, compaction, queue actions, transcript copy, and toast output

## Scope Resolution

Commands are discovered from these scope folders:

- Project: `usr/projects/<project>/.a0proj/plugins/_commands/commands/`
- Global fallback: `usr/plugins/_commands/commands/`
- Built-in defaults: `plugins/_commands/commands/`
- Other enabled plugins: `plugins/<plugin>/commands/` or `usr/plugins/<plugin>/commands/`

Precedence in the chat picker:

1. Project
2. Global
3. Built-in `_commands`
4. Other plugin-distributed commands

## Legacy Community Plugin Migration

When the built-in `_commands` plugin starts, it migrates files from the older community `commands` plugin namespace:

- Copies `usr/plugins/commands/commands/` into `usr/plugins/_commands/commands/`
- Copies `usr/plugins/commands/skills/` into `usr/plugins/_commands/skills/`
- Copies project and agent scoped `plugins/commands/commands/` folders to matching `plugins/_commands/commands/` folders
- Skips existing destination files
- Disables the legacy `commands` plugin roots so the WebUI does not load two slash-command popovers

## UI Surfaces

- Plugin modal: manage project/global commands and create editable same-name overrides of bundled commands
- Chat composer: type `/` at the start or as the final token to browse commands

## Agent Skill

The plugin ships with `commands-create-slash-command`, a plugin-scoped skill that helps Agent Zero create or update command files.
