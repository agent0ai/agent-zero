# Telegram Integration Plugin DOX

## Purpose

- Own Telegram bot integration for Agent Zero with polling, webhook, per-user sessions, and file exchange.

## Ownership

- `helpers/bot_manager.py` owns bot lifecycle.
- `helpers/handler.py` and `helpers/telegram_client.py` own message routing, replies, and Telegram API interaction.
- `helpers/dependencies.py` and `requirements.txt` own framework-runtime dependency bootstrap.
- `api/`, `prompts/`, `extensions/`, `default_config.yaml`, `plugin.yaml`, `README.md`, and `webui/` own tests/webhook endpoints, prompt fragments, hooks, settings, metadata, docs, and UI.

## Local Contracts

- Treat bot tokens, chat IDs, attachments, and user data as sensitive.
- Keep allowed-user, group-mode, project, model, and `/send` controls enforced.
- Install Telegram dependencies into the framework runtime only when required.
- Agent profile picker actions change the top-level chat profile and must preserve existing subordinate agent profiles.
- Model picker status shows the effective preset; clearing a chat override returns to its scoped preset rather than assuming `Default`.

## Work Guidance

- Coordinate bot lifecycle changes with job-loop hooks and settings reload behavior.

## Verification

- Smoke-test connection checks, polling or webhook delivery, per-user context reuse, attachments, and replies when practical.

## Child DOX Index

No child DOX files.
