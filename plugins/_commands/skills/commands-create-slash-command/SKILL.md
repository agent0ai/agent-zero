---
name: commands-create-slash-command
description: Create or update Agent Zero slash commands for the built-in Commands plugin. Use when the user asks to add, edit, duplicate, or refine a reusable /command backed by YAML config plus text/python content files.
version: 1.0.0
tags: ["commands", "slash-commands", "plugin", "yaml", "python", "templates"]
triggers:
  - create slash command
  - add slash command
  - update slash command
  - edit slash command
  - commands plugin
---

# Commands Plugin Slash Command Authoring

Use this skill when the user wants a reusable `/command` for Agent Zero's built-in `_commands` plugin.

## Source Of Truth

- Slash commands are file-backed, not database rows.
- Each command uses:
  - one config file: `<slug>.command.yaml`
  - one content file:
    - text template: `<slug>.txt`, or
    - python hook: `<slug>.py`
- Required config keys:
  - `name`
  - `description`
  - `type` (`text` or `script`)
- Optional config keys:
  - `argument_hint`
  - `include_history` (script commands)
- Preserve unknown config keys when editing existing commands.

## Scope Resolution

Choose the target folder from the requested scope:

- Project: `usr/projects/<project>/.a0proj/plugins/_commands/commands/`
- Global fallback: `usr/plugins/_commands/commands/`

If the user does not specify a scope, prefer the active chat scope when it is clear. Otherwise use the global scope.

## File Rules

- Config file format: `<slug>.command.yaml`
- Slash command name should be lowercase and hyphenated, for example `explain-code`
- For text commands, keep the `.txt` template concise and directly reusable
- For script commands, implement `run(payload)` in the `.py` file
- If the command expects trailing input, use `{raw}`, `{args.positional.0}`, or `{args.flags.some_flag}`

Use the bundled templates in `template.command.yaml` and `template.command.txt` when creating a new text command from scratch.

## Editing Workflow

1. Determine scope and final slash command name.
2. Check whether a command file already exists in that scope.
3. If it exists, load the file first and preserve unknown frontmatter keys.
4. Update YAML config and template/script content.
5. Save the file in the correct scope folder.
6. Report:
   - the saved config path
   - the saved content path
   - the slash command name in `/name` form

## Output Contract

After saving, explicitly state the final file path and the exact slash command invocation, for example:

- `Saved config: /a0/usr/plugins/_commands/commands/explain-code.command.yaml`
- `Saved content: /a0/usr/plugins/_commands/commands/explain-code.txt`
- `Invoke with: /explain-code`
