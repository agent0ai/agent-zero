# Team Compose DOX

## Purpose

- Own local team deployment against the pinned framework and agent runtime image.

## Ownership

- `compose.yaml` owns the loopback listener, team opt-in, read-only source, and per-project user/cache volumes.
- `compose.host-browser-proxy.yaml` adds an optional relay for machines that route public requests through a local HTTP proxy. The relay opens only a root-owned Unix socket in a separate Compose volume and forwards to the administrator-selected loopback port.

## Local Contracts

- Use a separate Compose project name for each team QA or upgrade installation.
- Team SQLite and native projects, chats and scheduler storage are backed up together from a stopped framework. Code versions and backups move together during rollback.
- Only one framework process opens a team user volume. Persisted credentials remain in the selected user volume.

## Work Guidance

- Keep the image pin, Compose health check and documentation synchronized with verified runtime changes.

## Verification

- Verify Compose expansion, health, native logins, persistence across restart, and upgrade and restore against independent named volumes.

## Child DOX Index

No child DOX files.
