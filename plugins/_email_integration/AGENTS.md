# Email Integration Plugin DOX

## Purpose

- Own communicating with Agent Zero through email inboxes and SMTP replies.

## Ownership

- `helpers/handler.py` owns mailbox polling, state, dispatch, routing, and reply flow.
- `helpers/imap_client.py` and `helpers/smtp_client.py` are thin control clients; `sandbox/` owns optional IMAP/Exchange packages and SMTP transport. Attachments cross as selected bytes, never arbitrary guest paths.
- `helpers/dispatcher.py`, `prompts/`, and attachment helpers own routing decisions and message formatting.
- `api/`, `default_config.yaml`, `plugin.yaml`, `extensions/`, and `webui/` own tests, scoped settings, metadata, hooks, and configuration.

## Local Contracts

- Outgoing attachment reads resolve development `/a0` aliases and use local helpers. The legacy `_read_attachments_via_rfc` name remains compatible but performs no development RFC dispatch; selected attachment bytes still cross the mail guest boundary.

- Treat mailbox credentials and downloaded attachments as sensitive.
- IMAP accepts exactly one valid From mailbox, rejecting duplicate fields, groups, and parser defects before body processing. Match the whitelist and address replies using that mailbox's normalized address; From filtering does not authenticate sender identity.
- Preserve UID/state tracking so restarts do not duplicate old mail.
- First configured poll or explicit connection/send starts the persistent guest; idle cleanup/disable stops it without deleting settings or checkpoints. Disabled handlers do not provision. Validate returned attachment names/base64 before creating private files; sanitize transport errors.
- Keep SMTP replies threaded and safe around user-visible errors.
- `webui/config.html` is the sole plugin UI, including inbox setup and connection checks.
- Preserve native project and agent-profile configuration scope support.

## Work Guidance

- Coordinate polling, dispatch prompts, and WebUI settings when adding account or routing behavior.

## Verification

- Smoke-test connection checks, polling, attachment handling, dispatch routing, and SMTP replies when practical.
- Run `PYTHONPATH=. pytest -q tests/test_email_integration_sender.py` for inbound sender validation and SMTP recipient regression coverage.

## Child DOX Index

No child DOX files.
