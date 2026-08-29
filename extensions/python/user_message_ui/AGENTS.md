# User Message UI Extensions DOX

## Purpose

- Own backend behavior triggered around user-visible UI messages.

## Ownership

- Ordered Python files own Agent Zero and daily custom-plugin update messaging, plus future user-message UI hooks.

## Local Contracts

- Keep proactive UI messages relevant, non-spammy, and safe for display.
- Keep update-available notifications visible until the user dismisses them or opens the updater.
- Do not expose local diagnostics or update data that should stay internal.

## Work Guidance

- Gate recurring messages so they do not repeat unnecessarily across chats or tabs.
- Run remote plugin checks outside the user-message request path, preserve the
  last good status on remote errors, and retry only failed plugins.

## Verification

- Smoke-test UI message rendering after changes.

## Child DOX Index

No child DOX files.
