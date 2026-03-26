# Email Integration

Communicate with Agent Zero through email inboxes and send replies back over SMTP.

## What It Does

This plugin polls configured mailboxes, downloads incoming messages and attachments, decides whether a message should continue an existing chat or start a new one, and sends replies back by email.

It supports both:

- **IMAP inbox polling**
- **Exchange inbox polling**
- **SMTP replies**

## Main Behavior

- **Mailbox polling**
  - Tracks per-handler mailbox state in `usr/email/state.json`.
  - Uses UID tracking for IMAP accounts so only new mail is processed after initialization.
- **Attachment handling**
  - Downloads attachments into `usr/email/attachments`.
- **Dispatcher workflow**
  - Reuses or creates a background `Email Dispatcher` context.
  - Uses model prompts to decide whether an email belongs to an existing chat or should open a new one.
- **Thread routing**
  - Can continue an existing chat by thread ID found in the email subject.
  - Falls back to model-based dispatch if no direct thread match is available.
- **Notifications and persistence**
  - Saves chats after routing and emits notifications about new or continued conversations.

## Key Files

- **Core orchestration**
  - `helpers/handler.py` manages polling, state persistence, dispatching, and reply flow.
- **Mail helpers**
  - `helpers/imap_client.py` handles IMAP and Exchange fetching.
  - `helpers/smtp_client.py` handles outbound replies.
  - `helpers/dispatcher.py` formats chat summaries and parses dispatcher decisions.
- **API and extensions**
  - `api/` and `extensions/` connect the polling loop and UI-facing operations into the main app.

## Configuration Scope

- **Settings section**: `external`
- **Per-project config**: `false`
- **Per-agent config**: `false`

## Plugin Metadata

- **Name**: `_email_integration`
- **Title**: `Email Integration`
- **Description**: Communicate with Agent Zero via email. Supports IMAP/Exchange inbox polling with SMTP replies.
