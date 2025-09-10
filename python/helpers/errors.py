import re
import traceback
import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Any, Optional


def handle_error(e: Exception):
    # if asyncio.CancelledError, re-raise
    if isinstance(e, asyncio.CancelledError):
        raise e


def error_text(e: Exception):
    return str(e)


def format_error(e: Exception, start_entries=6, end_entries=4):
    # format traceback from the provided exception instead of the most recent one
    traceback_text = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
    # Split the traceback into lines
    lines = traceback_text.split("\n")

    if not start_entries and not end_entries:
        trimmed_lines = []
    else:

        # Find all "File" lines
        file_indices = [
            i for i, line in enumerate(lines) if line.strip().startswith("File ")
        ]

        # If we found at least one "File" line, trim the middle if there are more than start_entries+end_entries lines
        if len(file_indices) > start_entries + end_entries:
            start_index = max(0, len(file_indices) - start_entries - end_entries)
            trimmed_lines = (
                lines[: file_indices[start_index]]
                + [
                    f"\n>>>  {len(file_indices) - start_entries - end_entries} stack lines skipped <<<\n"
                ]
                + lines[file_indices[start_index + end_entries] :]
            )
        else:
            # If no "File" lines found, or not enough to trim, just return the original traceback
            trimmed_lines = lines

    # Find the error message at the end
    error_message = ""
    for line in reversed(lines):
        # match both simple errors and module.path.Error patterns
        if re.match(r"[\w\.]+Error:\s*", line):
            error_message = line
            break

    # Combine the trimmed traceback with the error message
    if not trimmed_lines:
        result = error_message
    else:
        result = "Traceback (most recent call last):\n" + "\n".join(trimmed_lines)
        if error_message:
            result += f"\n\n{error_message}"

    # at least something
    if not result:
        result = str(e)

    return result


class RepairableException(Exception):
    """An exception type indicating errors that can be surfaced to the LLM for potential self-repair."""
    pass


# Phase 1: unified retry & error classification

class ErrorClass(Enum):
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    AUTH = "auth"
    TIMEOUT = "timeout"
    PARSE = "parse"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    cls: ErrorClass
    retryable: bool = True
    rotate_key: bool = False
    message: str = ""


def map_exception(e: Exception) -> ErrorInfo:
    name = e.__class__.__name__.lower()
    msg = str(e).lower()
    # LiteLLM & HTTP style patterns
    if "ratelimit" in name or "rate limit" in msg or "429" in msg:
        return ErrorInfo(ErrorClass.RATE_LIMIT, True, True, message=str(e))
    if "timeout" in name or "timed out" in msg:
        return ErrorInfo(ErrorClass.TIMEOUT, True, False, message=str(e))
    if "503" in msg or "unavailable" in msg:
        return ErrorInfo(ErrorClass.SERVER, True, True, message=str(e))
    if "401" in msg or "403" in msg or "unauthorized" in msg:
        return ErrorInfo(ErrorClass.AUTH, False, True, message=str(e))
    if "connection" in msg or "dns" in msg or "temporary failure" in msg:
        return ErrorInfo(ErrorClass.NETWORK, True, False, message=str(e))
    return ErrorInfo(ErrorClass.UNKNOWN, True, False, message=str(e))


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    jitter: float = 0.3  # +/- 30%
    backoff_factor: float = 2.0
    max_delay: float = 15.0
    # classes that should NOT retry
    no_retry: tuple[ErrorClass, ...] = (ErrorClass.AUTH,)


@dataclass
class AttemptRecord:
    attempt: int
    start: float
    end: float
    error: Optional[str]
    error_class: Optional[str]
    action: str  # success|retry|fail
    key_used: Optional[str] = None


@dataclass
class RetryOutcome:
    ok: bool
    result: Any = None
    attempts: list[AttemptRecord] = None  # type: ignore
    final_error: Optional[Exception] = None
    total_time: float = 0.0


async def execute_with_retry(
    op: Callable[[str | None], Awaitable[Any]],
    select_key: Callable[[], str | None] | None = None,
    mark_key_good: Callable[[str | None], None] | None = None,
    mark_key_bad: Callable[[str | None, ErrorInfo], None] | None = None,
    retry_cfg: RetryConfig | None = None,
    log_cb: Callable[[dict], Awaitable[None]] | None = None,
) -> RetryOutcome:
    retry_cfg = retry_cfg or RetryConfig()
    attempts: list[AttemptRecord] = []
    t0 = time.time()
    for i in range(1, retry_cfg.max_attempts + 1):
        key = select_key() if select_key else None
        start = time.time()
        try:
            result = await op(key)
            end = time.time()
            rec = AttemptRecord(i, start, end, None, None, "success", key)
            attempts.append(rec)
            if mark_key_good and key:
                mark_key_good(key)
            if log_cb:
                await log_cb(
                    {
                        "phase": "model_call",
                        "attempt": i,
                        "action": "success",
                        "latency": round(end - start, 3),
                        "key": _mask_key(key),
                    }
                )
            return RetryOutcome(
                ok=True, result=result, attempts=attempts, total_time=time.time() - t0
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            end = time.time()
            info = map_exception(e)
            action = "fail"
            if info.cls not in retry_cfg.no_retry and i < retry_cfg.max_attempts:
                action = "retry"
            rec = AttemptRecord(
                i, start, end, str(e), info.cls.value, action, key
            )
            attempts.append(rec)
            if mark_key_bad and key and info.rotate_key:
                mark_key_bad(key, info)
            if log_cb:
                await log_cb(
                    {
                        "phase": "model_call",
                        "attempt": i,
                        "action": action,
                        "error_class": info.cls.value,
                        "error": str(e)[:400],
                        "latency": round(end - start, 3),
                        "key": _mask_key(key),
                    }
                )
            if action == "retry":
                delay = min(
                    retry_cfg.base_delay * (retry_cfg.backoff_factor ** (i - 1)),
                    retry_cfg.max_delay,
                )
                # jitter
                import random

                jitter_span = delay * retry_cfg.jitter
                delay = delay + random.uniform(-jitter_span, jitter_span)
                await asyncio.sleep(max(0.05, delay))
                continue
            return RetryOutcome(
                ok=False,
                result=None,
                attempts=attempts,
                total_time=time.time() - t0,
                final_error=e,
            )
    # should not reach here
    return RetryOutcome(ok=False, attempts=attempts, total_time=time.time() - t0)


def _mask_key(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) <= 6:
        return "***"
    return key[:3] + "***" + key[-2:]
