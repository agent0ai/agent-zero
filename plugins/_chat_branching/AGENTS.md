# Chat Branching Plugin DOX

## Purpose

- Own branching a chat from any existing message.
- Keep log and history trimming behavior consistent when creating a branched conversation.

## Ownership

- `plugin.yaml` and `README.md` own metadata and user-facing behavior notes.
- `api/branch_chat.py` owns branch creation, clone, trim, persist, and refresh behavior.
- `extensions/` owns WebUI button injection.
- `webui/` owns plugin thumbnail assets.

## Local Contracts

- Preserve UUID-based linking between log entries and history messages.
- Branched chats must include history only up to the selected message.
- Do not mutate the source chat while creating a branch.

## Work Guidance

- Coordinate UI button injection with message rendering extension points.

## Verification

- Smoke-test branching from several message positions and confirm source chat remains unchanged.

## Child DOX Index

No child DOX files.
