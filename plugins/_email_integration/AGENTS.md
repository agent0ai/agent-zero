# Email Integration Plugin DOX

## Purpose

- Own communicating with Agent Zero through email inboxes and SMTP replies.

## Ownership

- `helpers/handler.py` owns mailbox polling, state, dispatch, routing, and reply flow.
- `helpers/imap_client.py` and `helpers/smtp_client.py` own inbound and outbound mail transports.
- `helpers/dispatcher.py`, `prompts/`, and attachment helpers own routing decisions and message formatting.
- `api/`, `default_config.yaml`, `plugin.yaml`, `extensions/`, and `webui/` own tests, settings, metadata, hooks, and config UI.

## Local Contracts

- Treat mailbox credentials and downloaded attachments as sensitive.
- IMAP accepts exactly one valid From mailbox, rejecting duplicate fields, groups, and parser defects before body processing. Match the whitelist and address replies using that mailbox's normalized address; From filtering does not authenticate sender identity.
- Preserve UID/state tracking so restarts do not duplicate old mail.
- Keep SMTP replies threaded and safe around user-visible errors.

## Work Guidance

- Coordinate polling, dispatch prompts, and WebUI settings when adding account or routing behavior.

## Verification

- Smoke-test connection checks, polling, attachment handling, dispatch routing, and SMTP replies when practical.
- Run `PYTHONPATH=. pytest -q tests/test_email_integration_sender.py` for inbound sender validation and SMTP recipient regression coverage.

## Child DOX Index

No child DOX files.
