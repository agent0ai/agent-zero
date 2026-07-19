# notification.py DOX

## Purpose

- Own the `notification.py` helper module.
- This module owns notification data models and notification manager state.
- Keep this file-level DOX profile synchronized with `notification.py` because this directory is intentionally flat.

## Ownership

- `notification.py` owns the runtime implementation.
- `notification.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `NotificationType` (`Enum`)
- `NotificationPriority` (`Enum`)
- `NotificationItem` (no explicit base class)
  - `mark_read(self)`
  - `output(self)`
- `NotificationManager` (no explicit base class)
  - `send_notification(type: NotificationType, priority: NotificationPriority, message: str, title: str=..., detail: str=..., display_time: int=..., group: str=..., id: str=...) -> NotificationItem`
  - `add_notification(self, type: NotificationType, priority: NotificationPriority, message: str, title: str=..., detail: str=..., display_time: int=..., group: str=..., id: str=...) -> NotificationItem`
  - `get_recent_notifications(self, seconds: int=...) -> list[NotificationItem]`
  - `output(self, start: int | None=..., end: int | None=...) -> list[dict]`
  - `output_with_state(self, start: int | None=..., end: int | None=...) -> tuple[list[dict], str, int]`
  - `output_all(self) -> list[dict]`
  - `mark_read_by_ids(self, notification_ids: list[str]) -> int`
  - `update_item(self, no: int, **kwargs) -> None`
  - `mark_all_read(self)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Notification payloads, GUIDs, and update cursors are captured under one lock so WebUI snapshots cannot skip notifications created during snapshot assembly.
- Observed side-effect areas: filesystem deletion, settings/state persistence.
- Imported dependency areas include: `dataclasses`, `datetime`, `enum`, `helpers.localization`, `threading`, `uuid`.

## Key Concepts

- Important called helpers/classes observed in the source: `self.manager.update_item`, `threading.RLock`, `AgentContext.get_notification_manager.add_notification`, `mark_dirty_all`, `self._update_item`, `NotificationType`, `Localization.get.serialize_datetime`, `uuid.uuid4`, `Localization.get.now`, `timedelta`, `n.output`, `AgentContext.get_notification_manager`, `next`, `NotificationPriority`, `NotificationItem`, `self._enforce_limit`, `seen.add`, `notifications.output`, `nid.strip`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_download_toast_regressions.py`
  - `tests/test_multi_tab_isolation.py`
  - `tests/test_self_update_tag_filter.py`
  - `tests/test_snapshot_parity.py`
  - `tests/test_snapshot_schema_v1.py`
  - `tests/test_state_monitor.py`
  - `tests/test_state_sync_handler.py`
  - `tests/test_state_sync_welcome_screen.py`

## Child DOX Index

No child DOX files.
