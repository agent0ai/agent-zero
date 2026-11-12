# Telegram Integration Plugin DOX

## Purpose

- Own Telegram bot integration for Agent Zero with polling, webhook, per-user sessions, and file exchange.

## Ownership

- `helpers/bot_manager.py` owns bot lifecycle.
- `helpers/scopes.py` owns configured-scope discovery, unique bot identities, activation, current authorization, session access, and secret-free context snapshots.
- `helpers/migration.py` snapshots existing configuration, activation, and session mappings privately before the first lifecycle pass, then upgrades missing/invalid legacy webhook secrets. Original settings and valid secrets remain unchanged; partial upgrades retry without replacing the original backup.
- `helpers/handler.py` and `helpers/telegram_client.py` own message routing, replies, and Telegram API interaction.
- `helpers/slash_commands.py` adapts the shared Commands resolver and effects to Telegram replies, menus, session bindings, exports, and compaction confirmation.
- `helpers/settings_ui.py` owns Telegram plugin toggles and tool-permission menus, delegating writes to the existing plugin and Agent Editor owners.
- `hooks.py` normalizes configurations, supplies stable names, and rejects unsafe/duplicate names, reused Telegram bot identities, and routing outside the owning project on save.
- `helpers/dependencies.py` and `requirements.txt` own framework-runtime dependency bootstrap.
- `api/`, `prompts/`, `extensions/`, `default_config.yaml`, `plugin.yaml`, `README.md`, and `webui/` own tests/webhook endpoints, prompt fragments, hooks, settings, metadata, docs, and UI.
- `webui/config.html` is the sole plugin WebUI, including bot setup and connection checks.
- `docs/guides/telegram.md` in the repository root owns the user setup walkthrough; keep its UI labels, scope examples, access guidance, and migration claims aligned with this plugin.

## Local Contracts

- Treat bot tokens, chat IDs, attachments, and user data as sensitive.
- Incoming attachment filenames are untrusted; strip both slash styles and NULs to a basename before constructing the upload path.
- Keep allowed-user, group-mode, project, model, and `/send` controls enforced.
- Resolve raw commands before adding the Telegram message envelope; its closing marker prevents queued/rendered text from being interpreted as a second postfix command. Custom/project definitions override bundled commands; keep Telegram's existing integration aliases and pickers for unoverridden commands.
- `/commands` discovers the current chat's effective commands on each use. The native Telegram menu registers global commands at startup, maps hyphens to underscores, and obeys Telegram's name/description/count limits.
- Render text/script results and supported effects in Telegram. Browser-only settings return guidance instead of pretending to open a modal; host computer permissions remain controlled by Launcher/CLI.
- Settings menus and every settings callback require the current sender to pass both `allowed_users` and the separate `admin_users` list; an omitted or empty administrator list grants nobody settings access. Derive administration from the current bot configuration for each event, never from context or callback data.
- Permission callbacks bind canonical tool IDs to the current context/project/profile, revalidate the live catalog, and refuse changes during an active run. Required tools stay outside the menu. Plugin toggles are instance-wide, protect always-enabled plugins, and keep Telegram/Commands enabled so the connection remains controllable.
- `/new` creates and binds a fresh context without resetting the previous chat. `/clear` retains Telegram's existing reset behavior. Compaction confirms the current idle context and uses the existing backup-producing compactor.
- Restart bots when their token, delivery mode, group mode, webhook URL, or webhook secret changes. Polling may start on the next job-loop tick after saving settings.
- Webhook dispatch requires an active webhook and a matching nonempty secret header. Setup requires a random 32–256 character secret using letters, digits, `_` or `-`; polling and webhook removal revoke HTTP delivery.
- Install Telegram dependencies into the framework runtime only when required.
- Support global, project, profile, and combined configurations and activation using framework precedence. Each explicitly saved configuration owns separate Telegram bots; inherited configuration does not create another connection. Reusing a Telegram bot ID (including a rotated token) across configurations is rejected on save and pauses all conflicting connections on read, preserving files for review.
- Global runtime keys remain bot names. Scoped keys include a stable scope digest; state mappings, webhooks, attachments, and replies use those keys. Project/profile-owned bots stay inside their owning scope; new contexts start in that project/profile. Global bots retain default-project and per-user routing.
- Preserve existing names, including spaces and Unicode, so global session keys do not change on upgrade. Reject path separators/control characters and pause runtime-key collisions. Never infer administrators, merge allowlists, drop scoped overrides, or silently choose between duplicate bot tokens during migration.
- Every event resolves the current owning and destination configuration, activation, allowlist, and group policy before dispatch. Never fall back to captured settings after removal, disablement, or connection rotation. Scope selection commands and callbacks validate the destination before changing it. Outbound replies, streams, and heartbeats recheck authorization too.
- Session lists and selection enforce bot/user/chat ownership and destination access. Only explicitly configured administrators may attach an unbound WebUI session; another Telegram user's session is never selectable. Context config snapshots exclude tokens and webhook secrets.
- The core `_11_scoped_telegram` job-loop bridge runs the manager when the global plugin is disabled, so explicitly enabled scoped bots can start and revoked connections can stop.
- Agent profile picker actions change the top-level chat profile and must
  preserve existing subordinate agent profiles. Picker rows and direct matches
  use the shared presentation catalog while current status may still report an
  existing chat that uses the utility profile.
- Model picker status shows the effective preset; clearing a chat override returns to its scoped preset rather than assuming `Default`.

## Work Guidance

- Coordinate bot lifecycle changes with job-loop hooks and settings reload behavior.
- WebUI store initialization must ignore Alpine registration calls without a configuration object.

## Verification

- Smoke-test connection checks, polling or webhook delivery, per-user context reuse, attachments, and replies when practical.
- Run `tests/test_telegram_config_scope.py` for all scopes, duplicate-token shutdown, inherited activation, current authorization, revocation, and session isolation.
- Run `tests/test_telegram_migration.py` for exact configuration/state preservation, private backups, webhook-secret upgrades, symlink preservation, and retry after interrupted or failed writes.
- Run `PYTHONPATH=. conda run -n a0 python -m pytest -q tests/test_telegram_commands.py tests/test_telegram_webhook_security.py` for command routing, menu bounds, configuration normalization, bot lifecycle, and administrator-only policy persistence and revocation regressions.

## Child DOX Index

No child DOX files.
