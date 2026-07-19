# Commands Plugin DOX

## Purpose

- Own the built-in slash command manager and chat composer slash picker.
- Keep file-backed `/command` discovery consistent across project, global, and plugin-provided scopes.

## Ownership

- `plugin.yaml` owns the built-in `_commands` plugin metadata.
- `helpers/commands.py` owns command name sanitization, argument parsing, scope resolution, file persistence, plugin command discovery, and command invocation resolution.
- `api/commands.py` owns the Commands API actions used by the WebUI.
- `webui/` owns the manager/editor modal stores, HTML surfaces, and thumbnail asset.
- `commands/` owns bundled read-only slash command definitions shipped by `_commands`.
- `extensions/` owns the chat composer slash picker and incoming-message command resolution.
- `extensions/python/startup_migration/` owns one-time migration from the legacy community `commands` plugin namespace.
- `skills/commands-create-slash-command/` owns the agent-facing authoring workflow for reusable slash commands.
- `tests/` owns regression coverage for parsing, CRUD, scope precedence, plugin-distributed commands, legacy migration, and skill discovery.

## Local Contracts

- The plugin identity is `_commands`; user-created command files live under `usr/plugins/_commands/commands/` or `usr/projects/<project>/.a0proj/plugins/_commands/commands/`.
- Each command is one `.command.yaml` config plus one same-directory `.txt` text template or `.py` script hook.
- Project commands override global commands, global commands override bundled `_commands/commands/` defaults, and bundled defaults override other plugin-distributed commands with the same name.
- Bundled `_commands/commands/` definitions and commands contributed by other plugins are read-only from this manager.
- The manager lists bundled commands separately; editing one copies it unchanged into the selected project or global scope under the same name, then edits that higher-precedence override.
- Bundled command files use canonical command names only; do not ship alias-only built-ins such as `/img` for `/attach`.
- Command configs may set `webui_hidden: true` to stay resolvable but be omitted from the chat composer picker.
- Commands contributed by enabled plugins live in their `commands/` directory and must not be rediscovered through the generic plugin-distributed path from `_commands` itself.
- On startup, `_commands` copies legacy `usr/plugins/commands` command and skill files into `usr/plugins/_commands` without overwriting existing files, copies scoped legacy command folders to `_commands`, and disables the legacy `commands` plugin roots to prevent duplicate WebUI popovers.
- Script commands must expose `run(payload)` and return a string or a dict with `text` and optional `effects`; `show_markdown` effects render as auto-dismissing toast notifications.
- Script commands may emit `send_message` with `text` to submit the rendered composer text immediately after command resolution.
- Commands accept prefix syntax (`/goal objective`) and exact postfix syntax (`objective /goal`); ordinary mid-sentence mentions are not invocations.
- WebUI sends resolve through the picker effect path, while backend-originated messages resolve before reaching the agent.
- Built-in `/computer-use on|off` emits a bounded `computer_use` effect. WebUI
  only directs the user to Host access in A0 Launcher or the same command in A0
  CLI; it never changes a Launcher gateway lease from Agent Zero page content.

## Work Guidance

- Keep the command storage and route namespace aligned with `_commands`.
- Preserve unknown command config keys when editing commands.
- Keep built-in source files immutable; user edits must be same-name scope overrides.
- Keep WebUI paths pointed at `/plugins/_commands/...`.

## Verification

- Run `conda run -n a0 pytest plugins/_commands/tests` after backend or command contract changes.

## Child DOX Index

No child DOX files.
