# task_scheduler.py DOX

## Purpose

- Own the `task_scheduler.py` helper module.
- This module models, serializes, schedules, runs, and persists scheduled tasks.
- Keep this file-level DOX profile synchronized with `task_scheduler.py` because this directory is intentionally flat.

## Ownership

- `task_scheduler.py` owns the runtime implementation.
- `task_scheduler.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `TaskState` (`str`, `Enum`)
- `TaskType` (`str`, `Enum`)
- `TaskSchedule` (`BaseModel`)
  - `to_crontab(self) -> str`
- `TaskPlan` (`BaseModel`)
  - `create(cls, todo: list[datetime] | None=..., in_progress: datetime | None=..., done: list[datetime] | None=...)`
  - `add_todo(self, launch_time: datetime)`
  - `set_in_progress(self, launch_time: datetime)`
  - `set_done(self, launch_time: datetime)`
  - `get_next_launch_time(self) -> datetime | None`
  - `should_launch(self) -> datetime | None`
- `BaseTask` (`BaseModel`)
  - `pinned_preset: str | None = Field(default=None)` — optional model preset name pinned at dispatch time (wOS D4); enforced at every fire via `_resolve_pinned_preset` + `chat_model_override` context data; missing preset fails loudly (ValueError, task state=error), never falls back to ambient.
  - `consecutive_failures: int = Field(default=0)` — consecutive failed-run counter for ERROR-state auto-recovery (dev-ticket-2026-09-08-scheduler-error-state-auto-recovery); incremented in `on_error`, reset to 0 in `on_success` and on manual ERROR→IDLE reset in `run_task_by_uuid`; at `SCHEDULER_MAX_CONSECUTIVE_FAILURES` (default 3) the task transitions to DISABLED with a loud `PrintStyle.error` + `logger.error` naming task, uuid, and last error.
  - `is_retry_due(self) -> bool` — whether an ERROR-state task is eligible to retry now; default False (only `ScheduledTask` implements retry-on-next-slot using last_run + 1s as cron reference so a task never re-fires within the slot it failed in).
  - `update(self, name: str | None=..., state: TaskState | None=..., system_prompt: str | None=..., prompt: str | None=..., attachments: list[str] | None=..., last_run: datetime | None=..., last_result: str | None=..., context_id: str | None=..., **kwargs)`
  - `check_schedule(self, frequency_seconds: float=...) -> bool`
  - `get_next_run(self) -> datetime | None`
  - `is_dedicated(self) -> bool`
  - `get_next_run_minutes(self) -> int | None`
  - `async on_run(self)`
  - `async on_finish(self)`
  - `async on_error(self, error: str)`
- `AdHocTask` (`BaseTask`)
  - `create(cls, name: str, system_prompt: str, prompt: str, token: str, attachments: list[str] | None=..., context_id: str | None=..., project_name: str | None=..., project_color: str | None=...)`
  - `update(self, name: str | None=..., state: TaskState | None=..., system_prompt: str | None=..., prompt: str | None=..., attachments: list[str] | None=..., last_run: datetime | None=..., last_result: str | None=..., context_id: str | None=..., token: str | None=..., **kwargs)`
- `ScheduledTask` (`BaseTask`)
  - `create(cls, name: str, system_prompt: str, prompt: str, schedule: TaskSchedule, attachments: list[str] | None=..., context_id: str | None=..., timezone: str | None=..., project_name: str | None=..., project_color: str | None=...)`
  - `update(self, name: str | None=..., state: TaskState | None=..., system_prompt: str | None=..., prompt: str | None=..., attachments: list[str] | None=..., last_run: datetime | None=..., last_result: str | None=..., context_id: str | None=..., schedule: TaskSchedule | None=..., **kwargs)`
  - `check_schedule(self, frequency_seconds: float=...) -> bool`
  - `is_retry_due(self) -> bool` — True once the next cron slot after the last failed run has arrived (ERROR-state retry eligibility).
  - `get_next_run(self) -> datetime | None`
- `PlannedTask` (`BaseTask`)
  - `create(cls, name: str, system_prompt: str, prompt: str, plan: TaskPlan, attachments: list[str] | None=..., context_id: str | None=..., project_name: str | None=..., project_color: str | None=...)`
  - `update(self, name: str | None=..., state: TaskState | None=..., system_prompt: str | None=..., prompt: str | None=..., attachments: list[str] | None=..., last_run: datetime | None=..., last_result: str | None=..., context_id: str | None=..., plan: TaskPlan | None=..., **kwargs)`
  - `check_schedule(self, frequency_seconds: float=...) -> bool`
  - `get_next_run(self) -> datetime | None`
  - `async on_run(self)`
  - `async on_finish(self)`
  - `async on_success(self, result: str)`
  - `async on_error(self, error: str)`
- `SchedulerTaskList` (`BaseModel`)
  - `get(cls) -> 'SchedulerTaskList'`
  - `async reload(self) -> 'SchedulerTaskList'`
  - `async add_task(self, task: Union[ScheduledTask, AdHocTask, PlannedTask]) -> 'SchedulerTaskList'`
  - `async save(self) -> 'SchedulerTaskList'`
  - `async update_task_by_uuid(self, task_uuid: str, updater_func: Callable[[Union[ScheduledTask, AdHocTask, PlannedTask]], None], verify_func: Callable[[Union[ScheduledTask, AdHocTask, PlannedTask]], bool]=...) -> Union[ScheduledTask, AdHocTask, PlannedTask] | None`
  - `get_tasks(self) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]`
  - `get_tasks_by_context_id(self, context_id: str, only_running: bool=...) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]`
  - `async get_due_tasks(self) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]` — returns IDLE tasks whose `check_schedule()` matches OR ERROR tasks whose `is_retry_due()` is True (auto-recovery; DISABLED tasks never auto-fire).
- `TaskScheduler` (no explicit base class)
  - `get(cls) -> 'TaskScheduler'`
  - `cancel_running_task(self, task_uuid: str, terminate_thread: bool=...) -> bool`
  - `cancel_tasks_by_context(self, context_id: str, terminate_thread: bool=...) -> bool`
  - `async reload(self)`
  - `get_tasks(self) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]`
  - `get_tasks_by_context_id(self, context_id: str, only_running: bool=...) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]`
  - `async add_task(self, task: Union[ScheduledTask, AdHocTask, PlannedTask]) -> 'TaskScheduler'`
  - `_resolve_pinned_preset(self, task: Union[ScheduledTask, AdHocTask, PlannedTask]) -> dict | None` — resolves a pinned preset via `_model_config` `get_preset_by_name`; raises ValueError (loud, no ambient fallback) when the preset is missing or the plugin is unavailable.
  - `async _get_chat_context(self, task)` — resolves pinned preset first, then applies `chat_model_override` to both existing and newly created contexts.
  - `async remove_task_by_uuid(self, task_uuid: str) -> 'TaskScheduler'`
- Top-level functions:
- `normalize_schedule_timezone(timezone_name: str | None) -> str`
- `_now() -> datetime`
- `_localize_task_datetime(dt: datetime) -> datetime`
- `serialize_datetime(dt: Optional[datetime]) -> Optional[str]`: Serialize a datetime object to ISO format string in the user's timezone.
- `parse_datetime(dt_str: Optional[str]) -> Optional[datetime]`: Parse ISO format datetime string with timezone awareness.
- `serialize_task_schedule(schedule: TaskSchedule) -> Dict[str, str]`: Convert TaskSchedule to a standardized dictionary format.
- `parse_task_schedule(schedule_data: Dict[str, str]) -> TaskSchedule`: Parse dictionary into TaskSchedule with validation.
- `serialize_task_plan(plan: TaskPlan) -> Dict[str, Any]`: Convert TaskPlan to a standardized dictionary format.
- `parse_task_plan(plan_data: Dict[str, Any]) -> TaskPlan`: Parse dictionary into TaskPlan with validation.
- `serialize_task(task: Union[ScheduledTask, AdHocTask, PlannedTask]) -> Dict[str, Any]`: Standardized serialization for task objects with proper handling of all complex types.
- `serialize_tasks(tasks: list[Union[ScheduledTask, AdHocTask, PlannedTask]]) -> list[Dict[str, Any]]`: Serialize a list of tasks to a list of dictionaries.
- `deserialize_task(task_data: Dict[str, Any], task_class: Optional[Type[T]]=...) -> T`: Deserialize dictionary into appropriate task object with validation.
- Notable constants/configuration names: `SCHEDULER_FOLDER`, `LOCAL_TIMEZONE_ALIASES`, `SCHEDULER_MAX_CONSECUTIVE_FAILURES` (default 3), `T`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, network calls, settings/state persistence, secret handling, scheduler state.
- Imported dependency areas include: `agent`, `asyncio`, `crontab`, `datetime`, `enum`, `helpers`, `helpers.defer`, `helpers.files`, `helpers.localization`, `helpers.persist_chat`, `helpers.print_style`, `initialize`, `nest_asyncio`, `os`, `os.path`, `pydantic`.

## Key Concepts

- Important called helpers/classes observed in the source: `nest_asyncio.apply`, `TypeVar`, `str.strip`, `callable`, `datetime.now`, `tzinfo.localize`, `Field`, `PrivateAttr`, `Localization.get.serialize_datetime`, `normalize_schedule_timezone`, `Localization.get.get_timezone`, `pytz.timezone`, `now`, `localize`, `cls`, `_localize_task_datetime`, `self.todo.remove`, `self.get_next_launch_time`, `super.__init__`, `threading.RLock`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_task_scheduler_timezone.py`
  - `tests/test_task_scheduler_error_recovery.py` (ERROR retry-on-next-slot, failure cap → DISABLED, counter reset, IDLE-only semantics)
  - `tests/test_timezone_regressions.py`
  - `tests/test_tool_action_contracts.py`

## Child DOX Index

No child DOX files.
