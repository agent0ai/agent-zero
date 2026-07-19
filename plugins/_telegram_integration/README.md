# Telegram Integration

Communicate with Agent Zero via Telegram. Supports polling and webhook modes with per-user chat sessions, group mentions, inline keyboards, and file exchange.

## What It Does

This plugin connects one or more Telegram bots to Agent Zero. Each bot runs independently with its own token, mode (polling or webhook), access control list, and project binding. Users message the bot on Telegram, and Agent Zero processes the conversation just like a WebUI chat — including tool use, sub-agents, and file attachments.

## Main Behavior

- **Dependency management**
  - Keeps `aiogram` in the plugin-local `requirements.txt` instead of the global root requirements.
  - Active code paths call `helpers/dependencies.py::ensure_dependencies()` to install `aiogram` into the framework runtime on first use via `uv pip install --python <current interpreter> -r plugins/_telegram_integration/requirements.txt`.
- **Bot lifecycle**
  - Managed by a `job_loop` extension that starts, restarts, or stops bots whenever plugin settings change.
  - Supports both long-polling and webhook delivery modes.
- **Per-user chat sessions**
  - Each Telegram user gets a dedicated `AgentContext`, persisted across restarts via a JSON state file.
  - `/start` creates a context; `/clear` resets it.
  - `/project <name>` switches the active project for the current chat.
  - `/config <preset>` switches the active model preset for the current chat.
  - `/send` or `/queue send` flushes the queued messages for the current chat.
- **Group support**
  - Three modes: `mention` (respond only when @mentioned or replied to), `all` (respond to every message), `off` (private only).
  - Optional welcome message for new members.
- **Message handling**
  - Extracts text, captions, locations, contacts, stickers, and attachment indicators.
  - Downloads photos, documents, audio, voice, and video into `usr/uploads/` with configurable auto-cleanup.
- **Reply delivery**
  - `tool_execute_after` intercepts the `response` tool — sends inline progress for `break_loop=false`.
  - `process_chain_end` auto-sends the final response, with retry logic on failure.
- **Formatting**
  - Converts Markdown output to Telegram-compatible HTML (bold, italic, strikethrough, code, links, blockquotes, lists).
  - Auto-splits messages exceeding the 4096-character limit; falls back to plain text on parse errors.
- **Inline keyboards**
  - Agent can attach a `keyboard` array to the `response` tool; button presses feed back as user messages.
- **Typing indicator**
  - Persistent "typing…" action while the agent is processing, cancelled on reply.
- **Notifications**
  - Optional WebUI notifications for incoming Telegram messages and `/clear` events.
- **Access control**
  - Per-bot allow-list by Telegram user ID or @username. Empty list = open to all.
- **Project binding**
  - Map individual Telegram users to specific Agent Zero projects; supports a default-project fallback.
  - Inherits model overrides from sibling contexts in the same project.

## Key Files

- **Helpers**
  - `helpers/handler.py` — Central message routing, context lifecycle, user auth, attachment download, reply sending, typing indicator.
  - `helpers/bot_manager.py` — Bot creation, polling/webhook lifecycle, bot registry.
  - `helpers/telegram_client.py` — Low-level Telegram API wrapper: send text/file/photo, Markdown→HTML converter, keyboard builder, message splitting.
- **Extensions**
  - `extensions/python/job_loop/_10_telegram_bot.py` — Bot lifecycle manager, starts/stops bots on each tick.
  - `extensions/python/system_prompt/_20_telegram_context.py` — Injects Telegram-specific system prompt.
  - `extensions/python/tool_execute_after/_50_telegram_response.py` — Intercepts `response` tool for inline delivery.
  - `extensions/python/process_chain_end/_55_telegram_reply.py` — Auto-sends final reply with retry.
- **API**
  - `api/webhook.py` — POST endpoint for Telegram webhook updates (no auth/CSRF).
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

- **Settings section**: `external`
- **Per-project config**: `false`
- **Per-agent config**: `false`

## Plugin Metadata

- **Name**: `_telegram_integration`
- **Title**: `Telegram Integration`
- **Description**: Communicate with Agent Zero via Telegram. Supports polling and webhook modes with per-user chat sessions.
