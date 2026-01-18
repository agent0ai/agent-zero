import copy
import json
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Literal, Optional, TYPE_CHECKING, TypeVar, cast

from python.helpers.secrets import get_secrets_manager
from python.helpers.strings import truncate_text_by_ratio


if TYPE_CHECKING:
    from agent import AgentContext


_MARK_DIRTY_ALL = None
_MARK_DIRTY_FOR_CONTEXT = None


def _lazy_mark_dirty_all(*, reason: str | None = None) -> None:
    # Lazy import to avoid circular import at module load time (AgentContext -> Log).
    global _MARK_DIRTY_ALL
    if _MARK_DIRTY_ALL is None:
        from python.helpers.state_monitor_integration import mark_dirty_all

        _MARK_DIRTY_ALL = mark_dirty_all
    _MARK_DIRTY_ALL(reason=reason)


def _lazy_mark_dirty_for_context(context_id: str, *, reason: str | None = None) -> None:
    # Lazy import to avoid circular import at module load time (AgentContext -> Log).
    global _MARK_DIRTY_FOR_CONTEXT
    if _MARK_DIRTY_FOR_CONTEXT is None:
        from python.helpers.state_monitor_integration import mark_dirty_for_context

        _MARK_DIRTY_FOR_CONTEXT = mark_dirty_for_context
    _MARK_DIRTY_FOR_CONTEXT(context_id, reason=reason)


T = TypeVar("T")

Type = Literal[
    "agent",
    "browser",
    "code_exe",
    "error",
    "hint",
    "info",
    "progress",
    "response",
    "tool",
    "input",
    "user",
    "util",
    "warning",
]

ProgressUpdate = Literal["persistent", "temporary", "none"]


HEADING_MAX_LEN: int = 120
CONTENT_MAX_LEN: int = 15_000
RESPONSE_CONTENT_MAX_LEN: int = 250_000
KEY_MAX_LEN: int = 60
VALUE_MAX_LEN: int = 5000
PROGRESS_MAX_LEN: int = 120


def _truncate_heading(text: str | None) -> str:
    if text is None:
        return ""
    return truncate_text_by_ratio(str(text), HEADING_MAX_LEN, "...", ratio=1.0)


def _truncate_progress(text: str | None) -> str:
    if text is None:
        return ""
    return truncate_text_by_ratio(str(text), PROGRESS_MAX_LEN, "...", ratio=1.0)


def _truncate_key(text: str) -> str:
    return truncate_text_by_ratio(str(text), KEY_MAX_LEN, "...", ratio=1.0)


def _truncate_value(val: T) -> T:
    # If dict, recursively truncate each value
    if isinstance(val, dict):
        for k in list(val.keys()):
            v = val[k]
            del val[k]
            val[_truncate_key(k)] = _truncate_value(v)
        return cast(T, val)
    # If list or tuple, recursively truncate each item
    if isinstance(val, list):
        for i in range(len(val)):
            val[i] = _truncate_value(val[i])
        return cast(T, val)
    if isinstance(val, tuple):
        return cast(T, tuple(_truncate_value(x) for x in val))

    # Convert non-str values to json for consistent length measurement
    if isinstance(val, str):
        raw = val
    else:
        try:
            raw = json.dumps(val, ensure_ascii=False)
        except Exception:
            raw = str(val)

    if len(raw) <= VALUE_MAX_LEN:
        return val  # No truncation needed, preserve original type

    # Do a single truncation calculation
    removed = len(raw) - VALUE_MAX_LEN
    replacement = f"\n\n<< {removed} Characters hidden >>\n\n"
    truncated = truncate_text_by_ratio(raw, VALUE_MAX_LEN, replacement, ratio=0.3)
    return cast(T, truncated)


def _truncate_content(text: str | None, type: Type) -> str:

    max_len = CONTENT_MAX_LEN if type != "response" else RESPONSE_CONTENT_MAX_LEN

    if text is None:
        return ""
    raw = str(text)
    if len(raw) <= max_len:
        return raw

    # Same dynamic replacement logic as value truncation
    removed = len(raw) - max_len
    while True:
        replacement = f"\n\n<< {removed} Characters hidden >>\n\n"
        truncated = truncate_text_by_ratio(raw, max_len, replacement, ratio=0.3)
        new_removed = len(raw) - (len(truncated) - len(replacement))
        if new_removed == removed:
            break
        removed = new_removed
    return truncated


@dataclass
class LogItem:
    log: "Log"
    no: int
    type: Type
    heading: str = ""
    content: str = ""
    temp: bool = False
    update_progress: Optional[ProgressUpdate] = "persistent"
    kvps: Optional[OrderedDict] = None  # Use OrderedDict for kvps
    id: Optional[str] = None  # Add id field
    guid: str = ""
    timestamp: float = 0.0
    duration_ms: Optional[int] = None
    agent_number: int = 0

    def __post_init__(self):
        self.guid = self.log.guid
        self.timestamp = self.timestamp or time.time()

    def update(
        self,
        type: Type | None = None,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
        temp: bool | None = None,
        update_progress: ProgressUpdate | None = None,
        **kwargs,
    ):
        if self.guid == self.log.guid:
            self.log._update_item(
                self.no,
                type=type,
                heading=heading,
                content=content,
                kvps=kvps,
                temp=temp,
                update_progress=update_progress,
                **kwargs,
            )

    def stream(
        self,
        heading: str | None = None,
        content: str | None = None,
        **kwargs,
    ):
        if heading is not None:
            self.update(heading=self.heading + heading)
        if content is not None:
            self.update(content=self.content + content)

        for k, v in kwargs.items():
            prev = self.kvps.get(k, "") if self.kvps else ""
            self.update(**{k: prev + v})

    def output(self):
        return {
            "no": self.no,
            "id": self.id,  # Include id in output
            "type": self.type,
            "heading": self.heading,
            "content": self.content,
            "temp": self.temp,
            "kvps": self.kvps,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "agent_number": self.agent_number,
        }


class Log:

    def __init__(self):
        self._lock = threading.RLock()
        self.context: "AgentContext|None" = None  # set from outside
        self.guid: str = str(uuid.uuid4())
        self.updates: list[int] = []
        self.logs: list[LogItem] = []
        self.progress: str = ""
        self.progress_no: int = 0
        self.progress_active: bool = False
        self.set_initial_progress()

    def log(
        self,
        type: Type,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
        temp: bool | None = None,
        update_progress: ProgressUpdate | None = None,
        id: Optional[str] = None,
        **kwargs,
    ) -> LogItem:
        with self._lock:
            # add a minimal item to the log
            # Determine agent number from streaming agent
            agent_number = 0
            if self.context and self.context.streaming_agent:
                agent_number = self.context.streaming_agent.number

            item = LogItem(
                log=self,
                no=len(self.logs),
                type=type,
                agent_number=agent_number,
            )
            # Set duration on previous item and mark it as updated
            if self.logs:
                prev = self.logs[-1]
                prev.duration_ms = int((item.timestamp - prev.timestamp) * 1000)
                self.updates += [prev.no]
            self.logs.append(item)

        # Update outside the lock - the heavy masking/truncation work should not hold
        # the lock; we only need locking while mutating shared arrays/fields.
        self._update_item(
            no=item.no,
            type=type,
            heading=heading,
            content=content,
            kvps=kvps,
            temp=temp,
            update_progress=update_progress,
            id=id,
            notify_state_monitor=False,
            **kwargs,
        )

        self._notify_state_monitor()
        return item

    def _update_item(
        self,
        no: int,
        type: Type | None = None,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
        temp: bool | None = None,
        update_progress: ProgressUpdate | None = None,
        id: Optional[str] = None,
        notify_state_monitor: bool = True,
        **kwargs,
    ):
        # Capture the effective type for truncation without holding the lock during
        # masking/truncation work.
        with self._lock:
            current_type = self.logs[no].type
        type_for_truncation = type if type is not None else current_type

        heading_out: str | None = None
        if heading is not None:
            heading_out = _truncate_heading(self._mask_recursive(heading))

        content_out: str | None = None
        if content is not None:
            content_out = _truncate_content(self._mask_recursive(content), type_for_truncation)

        kvps_out: OrderedDict | None = None
        if kvps is not None:
            kvps_out_tmp = OrderedDict(copy.deepcopy(kvps))
            kvps_out_tmp = self._mask_recursive(kvps_out_tmp)
            kvps_out_tmp = _truncate_value(kvps_out_tmp)
            kvps_out = OrderedDict(kvps_out_tmp)

        kwargs_out: dict | None = None
        if kwargs:
            kwargs_out = copy.deepcopy(kwargs)
            kwargs_out = self._mask_recursive(kwargs_out)

        with self._lock:
            item = self.logs[no]

            if id is not None:
                item.id = id

            if type is not None:
                item.type = type

            if temp is not None:
                item.temp = temp

            if update_progress is not None:
                item.update_progress = update_progress

            if heading_out is not None:
                item.heading = heading_out

            if content_out is not None:
                item.content = content_out

            if kvps_out is not None:
                item.kvps = kvps_out
            elif item.kvps is None:
                item.kvps = OrderedDict()

            if kwargs_out:
                if item.kvps is None:
                    item.kvps = OrderedDict()
                item.kvps.update(kwargs_out)

            self.updates.append(item.no)

            if item.heading and item.update_progress != "none":
                if item.no >= self.progress_no:
                    self.progress = item.heading
                    self.progress_no = (
                        item.no if item.update_progress == "persistent" else -1
                    )
                    self.progress_active = True
        if notify_state_monitor:
            self._notify_state_monitor_for_context_update()

    def _notify_state_monitor(self) -> None:
        ctx = self.context
        if not ctx:
            return
        # Logs update both the active chat stream (sid-bound) and the global chats list
        # (context metadata like last_message/log_version). Broadcast so all tabs refresh
        # their chat/task lists without leaking logs (logs are still scoped per-sid).
        _lazy_mark_dirty_all(reason="log.Log._notify_state_monitor")

    def _notify_state_monitor_for_context_update(self) -> None:
        ctx = self.context
        if not ctx:
            return
        # Log item updates only need to refresh the active chat stream for any sid
        # currently projecting this context. Avoid global fanout at high frequency.
        _lazy_mark_dirty_for_context(ctx.id, reason="log.Log._update_item")

    def set_progress(self, progress: str, no: int = 0, active: bool = True):
        progress = self._mask_recursive(progress)
        progress = _truncate_progress(progress)
        changed = False
        ctx = self.context
        with self._lock:
            prev_progress = self.progress
            prev_active = self.progress_active

            self.progress = progress
            if not no:
                no = len(self.logs)
            self.progress_no = no
            self.progress_active = active

            changed = self.progress != prev_progress or self.progress_active != prev_active

        if changed and ctx:
            # Progress changes are included in every snapshot, but push sync requires a
            # dirty mark even when no log items changed.
            _lazy_mark_dirty_for_context(ctx.id, reason="log.Log.set_progress")

    def set_initial_progress(self):
        self.set_progress("Waiting for input", 0, False)

    def output(self, start=None, end=None):
        with self._lock:
            if start is None:
                start = 0
            if end is None:
                end = len(self.updates)
            updates = self.updates[start:end]
            logs = list(self.logs)

        out = []
        seen = set()
        for update in updates:
            if update not in seen and update < len(logs):
                out.append(logs[update].output())
                seen.add(update)
        return out

    def reset(self):
        with self._lock:
            self.guid = str(uuid.uuid4())
            self.updates = []
            self.logs = []
        self.set_initial_progress()

    def _mask_recursive(self, obj: T) -> T:
        """Recursively mask secrets in nested objects."""
        try:
            from agent import AgentContext
            secrets_mgr = get_secrets_manager(self.context or AgentContext.current())

            # debug helper to identify context mismatch
            # self_id = self.context.id if self.context else None
            # current_ctx = AgentContext.current()
            # current_id = current_ctx.id if current_ctx else None
            # if self_id != current_id:
            #     print(f"Context ID mismatch: {self_id} != {current_id}")

            if isinstance(obj, str):
                return cast(Any, secrets_mgr.mask_values(obj))
            elif isinstance(obj, dict):
                return {k: self._mask_recursive(v) for k, v in obj.items()}  # type: ignore
            elif isinstance(obj, list):
                return [self._mask_recursive(item) for item in obj]  # type: ignore
            else:
                return obj
        except Exception:
            # If masking fails, return original object
            return obj
