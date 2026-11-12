# Telegram Integration

Communicate with Agent Zero via Telegram. Supports polling and webhook modes with per-user chat sessions, group mentions, inline keyboards, and file exchange.

**Setting up your first bot?** Follow the [Telegram setup guide](../../docs/guides/telegram.md)
for a screenshot-led walkthrough, private access, project/profile scopes, and
upgrade troubleshooting. This reference describes the plugin's capabilities and implementation.

## What It Does

This plugin connects one or more Telegram bots to Agent Zero. Each bot runs independently with its own token, mode (polling or webhook), access control list, and project binding. Users message the bot on Telegram, and Agent Zero processes the conversation just like a WebUI chat — including tool use, sub-agents, and file attachments.

## Main Behavior

- **Dependency management**
  - Keeps `aiogram` in the plugin-local `requirements.txt` instead of the global root requirements.
  - Active code paths call `helpers/dependencies.py::ensure_dependencies()` to install `aiogram` into the framework runtime on first use via `uv pip install --python <current interpreter> -r plugins/_telegram_integration/requirements.txt`.
- **Bot lifecycle**
  - Managed by a `job_loop` extension that starts, restarts, or stops bots whenever plugin settings change.
  - Supports both long-polling and webhook delivery modes. Webhook mode requires a random secret of 32–256 letters, digits, underscores or hyphens; generate one with `python -c 'import secrets; print(secrets.token_urlsafe(32))'`. The upgrade migration supplies a secure secret for legacy webhook configurations that lack one.
  - The webhook endpoint rejects polling bots and requires a matching `X-Telegram-Bot-Api-Secret-Token` header before dispatch.
  - Bot names are generated automatically if left empty. Existing names, including spaces and Unicode, are retained. Names must be unique within their configuration, fit within 128 characters, and exclude path separators and control characters. Saving a new token or webhook connection restarts that bot on the next maintenance tick (up to about a minute); events from the old connection are rejected immediately.
- **Per-user chat sessions**
  - Each Telegram user gets a dedicated `AgentContext`, persisted across restarts via a JSON state file.
  - `/start` creates a context; `/new` starts fresh; `/clear` resets the current context.
  - `/commands` shows the shared integration command menu (`/help` is an alias).
  - `/commands` also provides a paginated menu of Agent Zero's built-in, enabled-plugin, global, and active-project commands. Custom commands use the same templates, scripts, and scope precedence as the WebUI, including prefix and postfix syntax.
  - `/stop`, `/goal`, and `/rename` execute their existing Agent Zero commands. `/compact` offers confirmation before summarizing, preserving the existing conversation backup. `/copy` sends the transcript as a text file; `/attach` explains Telegram's native attachment control.
  - Session selection is limited to that Telegram bot, user, and chat, within an allowed project/profile. Explicit bot administrators can also attach an unbound WebUI chat in an allowed scope. Another Telegram user's chats remain inaccessible.
  - `/models` and `/presets` open the model preset picker; `/chats` opens the session picker, and `/chat <id>` switches sessions. `/browser` offers runtime buttons.
  - For users listed separately as bot administrators, `/plugins` provides paginated instance-wide plugin toggles and `/permissions` edits the current profile's tool permissions, including Allow/Block/Default per tool, separate Tools/MCP defaults, and inherited policy. An empty administrator list disables these settings changes from Telegram. Always-required tools and the Telegram connection remain protected. Computer Use permissions stay with A0 Launcher/CLI.
  - Telegram's native command menu includes global commands at bot startup. Hyphenated commands also accept an underscore spelling, such as `/computer_use`; use `/commands` for freshly added or project-specific commands.
  - `/status` shows project, model, agent profile, and queue state.
  - `/project <name>` switches the active project for the current chat.
  - `/model <preset>` switches the active model preset for the current chat (`/config` remains an alias).
  - `/agent <profile>` switches the active agent profile when the current run is idle.
  - `/model`, `/project`, and `/agent` show Telegram inline keyboard pickers when used without arguments.
  - `/stream` toggles live response streaming; `/tools` toggles tool progress messages.
  - `/send` or `/queue send` flushes queued messages for the current chat.
  - `/steer <message>` sends an intervention to the active run.
- **Group support**
  - Three modes: `mention` (respond only when @mentioned or replied to), `all` (respond to every message), `off` (private only).
  - Optional welcome message for new members.
- **Message handling**
  - Extracts text, captions, locations, contacts, stickers, and attachment indicators.
  - Downloads photos, documents, audio, voice, and video into `usr/uploads/` with configurable auto-cleanup.
- **Reply delivery**
  - Streams tool progress and response text through real Telegram messages updated with `editMessageText`.
  - Tool progress and the AI response are separate messages; only the AI response replies to the user message.
  - `tool_execute_after` intercepts the `response` tool — sends `break_loop=false` updates as separate intermediate Telegram messages.
  - `process_chain_end` auto-sends the final response, with retry logic on failure.
- **Formatting**
  - Converts Markdown output to Telegram-compatible HTML (bold, italic, strikethrough, code, links, blockquotes, lists).
  - Auto-splits messages exceeding the 4096-character limit; falls back to plain text on parse errors.
- **Inline keyboards**
  - Agent can attach a `keyboard` array to the `response` tool; button presses feed back as user messages.
- **Typing indicator**
  - Persistent "typing…" action while the agent is processing, cancelled on reply.
- **Busy-run queue**
  - Normal user messages received while a run is active are queued automatically.
  - `/steer <message>` is still delivered immediately as an intervention.
- **Notifications**
  - Optional WebUI notifications for incoming Telegram messages.
- **Access control**
  - Per-bot allow-list by Telegram user ID or @username. Empty list = open to all.
  - A separate `admin_users` list grants access to plugin and tool-permission settings. Administrators must also pass `allowed_users`; an omitted or empty administrator list grants nobody settings access. Each message and callback uses the current bot configuration, so removing an administrator also revokes existing menu buttons.
  - Replies, streamed progress, and heartbeats also check current access. New context snapshots omit bot tokens and webhook secrets.
- **Project binding**
  - Map individual Telegram users to specific Agent Zero projects; supports a default-project fallback.
  - Inherits model overrides from sibling contexts in the same project.

## Key Files

- **Helpers**
  - `helpers/handler.py` — Central message routing, context lifecycle, user auth, attachment download, reply sending, typing indicator.
  - `helpers/bot_manager.py` — Bot creation, polling/webhook lifecycle, bot registry.
  - `helpers/telegram_client.py` — Low-level Telegram API wrapper: send text/file/photo, Markdown→HTML converter, keyboard builder, message splitting.
  - `helpers/command_ui.py` — Telegram inline keyboard command pickers and callback handling.
  - `helpers/draft_stream.py` — Editable Telegram message streaming for tool progress and response previews.
- **Extensions**
  - `extensions/python/job_loop/_10_telegram_bot.py` — Bot lifecycle manager, starts/stops bots on each tick.
  - `extensions/python/message_loop_start/_45_telegram_draft_start.py` — Initializes Telegram response streaming.
  - `extensions/python/tool_execute_before/_45_telegram_draft_tool.py` — Streams tool-start progress.
  - `extensions/python/response_stream/_45_telegram_draft_response.py` — Streams final response previews.
  - `extensions/python/system_prompt/_20_telegram_context.py` — Injects Telegram-specific system prompt.
  - `extensions/python/tool_execute_after/_50_telegram_response.py` — Intercepts `response` tool for inline delivery.
  - `extensions/python/process_chain_end/_55_telegram_reply.py` — Auto-sends final reply with retry.
- **API**
  - `api/webhook.py` — POST endpoint authenticated by the webhook secret header (no session auth/CSRF).
  - `api/test_connection.py` — Token validation endpoint for the settings UI.
- **Prompts**
  - `prompts/fw.telegram.system_context_reply.md` — Telegram session behavior & formatting rules.
  - `prompts/fw.telegram.user_message.md` — Incoming message template.
  - `prompts/fw.telegram.user_message_instructions.md` — Per-bot custom agent instructions.
  - `prompts/fw.telegram.update_ok.md` / `update_error.md` / `send_failed.md` — Delivery feedback prompts.
- **Frontend**
  - `webui/config.html` — Alpine.js settings panel (bot list, token input, mode selector, etc.).
  - `webui/telegram-config-store.js` — Alpine store for the settings modal.

## Configuration Scope

All four scopes are supported: global, project, agent profile, and project plus profile. A bot configured in a project starts conversations there and cannot switch out of that project. A profile-scoped bot starts with that profile and cannot switch to another profile. A combined scope enforces both. Global bots retain default-project and per-user project routing.

Each explicitly saved configuration needs its own Telegram bot token. Create another bot with **@BotFather**, copy the desired settings, and replace the token before saving in another scope. Telegram bot accounts are not cloned by copying their tokens. To move an existing bot instead, remove its token from the old configuration before saving it in the new scope; previous chats are retained, while the new scope starts its own session bindings.

Where no scoped configuration exists, normal configuration inheritance applies without starting another bot. Scoped activation overrides still apply to inherited bots: disabling Telegram in a destination project/profile blocks events there. An explicitly enabled scoped bot can run while global activation is disabled. Configurations replace the inherited bot list rather than merging lists.

Existing scoped settings no longer pause every bot just because they exist. If multiple saved configurations contain the same Telegram bot identity, all conflicting connections remain paused until those tokens are separated or moved. This also detects old and rotated tokens for the same bot. Unreadable settings pause delivery rather than falling back to permissive rules. Use **Show existing configurations** to review saved copies; files are never deleted automatically.

## Upgrading Existing Installations

Before starting bots for the first time after this upgrade, Agent Zero saves an exact snapshot of existing Telegram configuration files, activation overrides, and session mappings in `usr/plugins/_telegram_integration/backups/config-scopes-v1/`. The manifest records each original path and checksum. The directory is private (`0700`) and backup files are private (`0600`), since configurations contain credentials.

Existing tokens, bot names, allowlists, administrator lists, project mappings, instructions, and other settings are retained. Existing global bots keep their chat bindings. The only automatic configuration edit supplies a random secret for an old webhook configuration with a missing or invalid secret; valid secrets remain unchanged. The migration preserves symlinks and can resume after an interrupted write without rotating an already upgraded secret or replacing the original backup. It never grants administrator access or merges conflicting access rules.

No manual migration command is required. Token conflicts stay preserved for review through the settings UI, as described above.

## Plugin Metadata

- **Name**: `_telegram_integration`
- **Title**: `Telegram Integration`
- **Description**: Communicate with Agent Zero via Telegram. Supports polling and webhook modes with per-user chat sessions.
