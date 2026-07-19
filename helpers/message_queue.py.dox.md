# message_queue.py DOX

## Purpose

- Own the `message_queue.py` helper module.
- This module stores and drains queued user messages for a context.
- Keep this file-level DOX profile synchronized with `message_queue.py` because this directory is intentionally flat.

## Ownership

- `message_queue.py` owns the runtime implementation.
- `message_queue.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `get_queue(context: 'AgentContext') -> list`: Get current queue from context.data.
- `_get_next_seq(context: 'AgentContext') -> int`: Get next sequence number.
- `_sync_output(context: 'AgentContext')`: Sync queue to output_data for frontend polling.
- `add(context: 'AgentContext', text: str, attachments: list[str] | None=..., item_id: str | None=...) -> dict`: Add message to queue. Attachments should be filenames, will be converted to full paths.
- `remove(context: 'AgentContext', item_id: str | None=...) -> int`: Remove item(s). If item_id is None, clears all. Returns remaining count.
- `pop_first(context: 'AgentContext') -> dict | None`: Remove and return first item.
- `pop_item(context: 'AgentContext', item_id: str) -> dict | None`: Remove and return specific item.
- `has_queue(context: 'AgentContext') -> bool`: Check if queue has items.
- `log_user_message(context: 'AgentContext', message: str, attachment_paths: list[str], message_id: str | None=..., source: str=...)`: Log user message to console and UI. Used by message API and queue processing.
- `send_message(context: 'AgentContext', item: dict, source: str=...)`: Send a single queued message (log + communicate).
- `send_next(context: 'AgentContext') -> bool`: Send next queued message. Returns True if sent, False if queue empty.
- `send_all_aggregated(context: 'AgentContext') -> int`: Aggregate and send all queued messages as one. Returns count of items sent.
- Notable constants/configuration names: `QUEUE_KEY`, `QUEUE_SEQ_KEY`, `UPLOAD_FOLDER`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem deletion, settings/state persistence.
- Imported dependency areas include: `helpers`, `helpers.print_style`, `os`, `typing`, `uuid`.

## Key Concepts

- Important called helpers/classes observed in the source: `context.set_data`, `get_queue`, `context.set_output_data`, `_sync_output`, `queue.pop`, `context.log.log`, `log_user_message`, `context.communicate`, `pop_first`, `has_queue`, `join`, `context.get_data`, `att.startswith`, `_get_next_seq`, `uuid.uuid4`, `UserMessage`, `send_message`, `guids.generate_id`, `os.path.basename`, `PrintStyle`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
