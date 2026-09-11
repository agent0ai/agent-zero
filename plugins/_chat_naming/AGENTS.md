# Chat Naming Plugin DOX

## Purpose

- Own manual and Utility Model-assisted naming for chats and scheduled-task rows.

## Ownership

- `helpers/naming.py` owns user-message selection, name generation, and persistence.
- `extensions/python/monologue_end/` owns configured automatic naming.
- `api/chat_name.py` owns modal reads, generation, and manual saves.
- `webui/` and `extensions/webui/sidebar-row-actions-menu/` own the standard rename modal and row-menu action.
- `prompts/` owns the Utility Model naming instructions.
- `commands/` owns the plugin-contributed `/rename <new name|auto>` slash command.

## Local Contracts

- Automatic naming reads scoped plugin config through the active chat agent.
- Automatic naming runs after the monologue completes, so it cannot delay the Main Model.
- Utility Model input contains the current name and user messages only; assistant work and tool results are excluded.
- The complete naming prompt must remain within 70% of the effective Utility Model context window, preserving the newest user context when trimming is required.
- `once` names only unnamed user chats from their first substantive user message (bare greetings are deferred); `always` considers the latest user message plus recent user context.
- Generated names are concise and normalized before persistence.
- Renaming a parallel child updates both its context name and sidebar label.
- Manual task renames update both scheduler metadata and the task context name.
- `/rename auto` uses the same generation and persistence helpers as the rename modal; any other non-empty argument is saved as the custom chat name.

## Work Guidance

- Keep this behavior plugin-local; do not restore naming prompts or naming hooks to core extensions.
- Use the shared modal stack and sidebar row-menu extension point.

## Verification

- Run `pytest plugins/_chat_naming/tests tests/test_sidebar_row_actions.py`.

## Child DOX Index

No child DOX files.
