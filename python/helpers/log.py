from dataclasses import dataclass, field
import json
import time
from typing import Any, Literal, Optional, Dict, TypeVar, TYPE_CHECKING

T = TypeVar("T")
import uuid
from collections import OrderedDict  # Import OrderedDict
from python.helpers.strings import truncate_text_by_ratio
import copy
from typing import TypeVar
from python.helpers.secrets import get_secrets_manager


if TYPE_CHECKING:
    from agent import AgentContext

T = TypeVar("T")

Type = Literal[
    "agent",
    "browser",
    "code_exe",
    "subagent",
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
        return val
    # If list or tuple, recursively truncate each item
    if isinstance(val, list):
        for i in range(len(val)):
            val[i] = _truncate_value(val[i])
        return val
    if isinstance(val, tuple):
        return tuple(_truncate_value(x) for x in val) # type: ignore

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
    return truncated


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
    update_progress: Optional[ProgressUpdate] = "persistent"
    kvps: Optional[OrderedDict] = None  # Use OrderedDict for kvps
    id: Optional[str] = None  # Add id field
    guid: str = ""
    timestamp: float = 0.0
    agentno: int = 0

    def __post_init__(self):
        self.guid = self.log.guid
        self.timestamp = self.timestamp or time.time()

    def update(
        self,
        type: Type | None = None,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
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
            "kvps": self.kvps,
            "timestamp": self.timestamp,
            "agentno": self.agentno,
        }


class Log:

    def __init__(self):
        self.context: "AgentContext|None" = None # set from outside
        self.guid: str = str(uuid.uuid4())
        self.updates: list[int] = []
        self.logs: list[LogItem] = []
        self.set_initial_progress()

    def log(
        self,
        type: Type,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
        update_progress: ProgressUpdate | None = None,
        id: Optional[str] = None,
        **kwargs,
    ) -> LogItem:

        # add a minimal item to the log
        # Determine agent number from streaming agent
        agentno = 0
        if self.context and self.context.streaming_agent:
            agentno = self.context.streaming_agent.number
        
        item = LogItem(
            log=self,
            no=len(self.logs),
            type=type,
            agentno=agentno,
        )
        # Set duration on previous item and mark it as updated
        if self.logs:
            prev = self.logs[-1]
            self.updates += [prev.no]
        self.logs.append(item)

        # and update it (to have just one implementation)
        self._update_item(
            no=item.no,
            type=type,
            heading=heading,
            content=content,
            kvps=kvps,
            update_progress=update_progress,
            id=id,
            **kwargs,
        )
        return item

    def _update_item(
        self,
        no: int,
        type: Type | None = None,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
        update_progress: ProgressUpdate | None = None,
        id: Optional[str] = None,
        **kwargs,
    ):
        item = self.logs[no]

        if id is not None:
            item.id = id

        if type is not None:
            item.type = type

        if update_progress is not None:
            item.update_progress = update_progress


        # adjust all content before processing
        if heading is not None:
            heading = self._mask_recursive(heading)
            heading = _truncate_heading(heading)
            item.heading = heading
        if content is not None:
            content = self._mask_recursive(content)
            content = _truncate_content(content, item.type)
            item.content = content
        if kvps is not None:
            kvps = OrderedDict(copy.deepcopy(kvps))
            kvps = self._mask_recursive(kvps)
            kvps = _truncate_value(kvps)
            item.kvps = kvps
        elif item.kvps is None:
            item.kvps = OrderedDict()
        if kwargs:
            kwargs = copy.deepcopy(kwargs)
            kwargs = self._mask_recursive(kwargs)
            item.kvps.update(kwargs)

        self.updates += [item.no]
        self._update_progress_from_item(item)

    def set_progress(self, progress: str, no: int = 0, active: bool = True):
        progress = self._mask_recursive(progress)
        progress = _truncate_progress(progress)
        self.progress = progress
        if not no:
            no = len(self.logs)
        self.progress_no = no
        self.progress_active = active

    def set_initial_progress(self):
        self.set_progress("Waiting for input", 0, False)

    def output(self, start=None, end=None):
        if start is None:
            start = 0
        if end is None:
            end = len(self.updates)

        out = []
        seen = set()
        for update in self.updates[start:end]:
            if update not in seen:
                out.append(self.logs[update].output())
                seen.add(update)

        return out

    def reset(self):
        self.guid = str(uuid.uuid4())
        self.updates = []
        self.logs = []
        self.set_initial_progress()

    def _update_progress_from_item(self, item: LogItem):
        if item.heading and item.update_progress != "none":
            if item.no >= self.progress_no:
                self.set_progress(
                    item.heading,
                    (item.no if item.update_progress == "persistent" else -1),
                )

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
                return secrets_mgr.mask_values(obj)
            elif isinstance(obj, dict):
                return {k: self._mask_recursive(v) for k, v in obj.items()}  # type: ignore
            elif isinstance(obj, list):
                return [self._mask_recursive(item) for item in obj]  # type: ignore
            else:
                return obj
        except Exception as _e:
            # If masking fails, return original object
            return obj