from __future__ import annotations

import re
from typing import Iterable


_DURABLE_SUBJECT_RE = re.compile(
    r"\b(user|project|repo|repository|workspace|runtime|service|server|"
    r"plugin|agent zero|a0|profile|team|organization|company)\b",
    re.IGNORECASE,
)
_DURABLE_RELATION_RE = re.compile(
    r"\b(prefers?|requires?|uses?|runs?|lives?|located|configured|default|"
    r"current(?:ly)?|must|should|always|never|constraint|path|endpoint|port)\b",
    re.IGNORECASE,
)
_TRANSIENT_RE = re.compile(
    r"(/tmp\b|\btmp/|\btemporary\b|\btemp\b|\bworkdir\b|"
    r"\bcontainer-local\b|\bmachine-local\b|\bpersonal absolute path\b|"
    r"\blocal endpoint\b|\blocal port\b|"
    r"\btest marker\b|\bmemory test\b|\bcleanup token\b|\bthrowaway\b|"
    r"\bsample file\b|\bdemo file\b|\bvalidation directory\b|\blive-test\b|"
    r"\bone-off\b|\bsession-only\b)",
    re.IGNORECASE,
)
_LOCAL_COORDINATE_RE = re.compile(
    r"\b(localhost|127\.0\.0\.1|0\.0\.0\.0|::1)\b|"
    r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(?::\d+)?|"
    r"/(?:home|Users)/[^/\s]+/|"
    r"\b[A-Za-z]:\\Users\\",
    re.IGNORECASE,
)
_AGENT_ACTION_RE = re.compile(
    r"\b(agent|assistant|codex|a0)\b.{0,80}\b("
    r"created|implemented|built|ran|tested|verified|fixed|wrote|generated|"
    r"saved|cleaned|inspected|synced|restarted|committed|staged|opened|"
    r"reported|showed)\b",
    re.IGNORECASE,
)
_USER_REQUEST_RE = re.compile(
    r"\b(user|the user)\s+(asked|requested|wanted|told|prompted|instructed)\b",
    re.IGNORECASE,
)
_COMMAND_HISTORY_RE = re.compile(
    r"\b(ran|executed)\s+[`'\"]?[\w./-]+|\bterminal command\b|"
    r"\bcommand output\b|\bexit code\b|\bstdout\b|\bstderr\b",
    re.IGNORECASE,
)
_LOW_VALUE_RE = re.compile(
    r"^(hello|hi|greeting|conversation start|task completed|file created|"
    r"implementation completed|test passed|memory search)$",
    re.IGNORECASE,
)


def normalize_memory_candidate(value: object) -> str:
    return str(value).strip()


def is_auto_fragment_worth_saving(text: str) -> bool:
    """Return True only for durable facts suitable for automatic fragments."""

    text = normalize_memory_candidate(text)
    has_durable_relation = bool(_DURABLE_RELATION_RE.search(text))
    if len(text) < 24:
        return False
    if _LOW_VALUE_RE.match(text):
        return False
    if _TRANSIENT_RE.search(text):
        return False
    if _LOCAL_COORDINATE_RE.search(text):
        return False
    if _COMMAND_HISTORY_RE.search(text):
        return False
    if _AGENT_ACTION_RE.search(text) and not has_durable_relation:
        return False
    if _USER_REQUEST_RE.search(text) and not has_durable_relation:
        return False

    return bool(_DURABLE_SUBJECT_RE.search(text) and has_durable_relation)


def filter_auto_memory_fragments(memories: Iterable[object]) -> list[str]:
    return [
        text
        for text in (normalize_memory_candidate(memory) for memory in memories)
        if is_auto_fragment_worth_saving(text)
    ]
