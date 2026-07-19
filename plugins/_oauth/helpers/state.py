from __future__ import annotations

import threading
import time
from dataclasses import dataclass


LOGIN_TTL_SECONDS = 10 * 60


@dataclass(frozen=True)
class LoginAttempt:
    state: str
    verifier: str
    redirect_uri: str
    created_at: float

    @property
    def expires_at(self) -> float:
        return self.created_at + LOGIN_TTL_SECONDS

    def expired(self) -> bool:
        return time.time() > self.expires_at


@dataclass(frozen=True)
class DeviceAttempt:
    attempt_id: str
    device_auth_id: str
    user_code: str
    interval: int
    expires_at_value: float

    @property
    def expires_at(self) -> float:
        return self.expires_at_value

    def expired(self) -> bool:
        return time.time() > self.expires_at


_lock = threading.RLock()
_attempts: dict[str, LoginAttempt] = {}
_device_attempts: dict[str, DeviceAttempt] = {}


def put_attempt(state: str, verifier: str, redirect_uri: str) -> LoginAttempt:
    cleanup_expired()
    attempt = LoginAttempt(
        state=state,
        verifier=verifier,
        redirect_uri=redirect_uri,
        created_at=time.time(),
    )
    with _lock:
        _attempts[state] = attempt
    return attempt


def pop_attempt(state: str) -> LoginAttempt | None:
    cleanup_expired()
    with _lock:
        attempt = _attempts.pop(state, None)
    if attempt is None or attempt.expired():
        return None
    return attempt


def put_device_attempt(
    attempt_id: str,
    device_auth_id: str,
    user_code: str,
    interval: int,
    expires_at: float,
) -> DeviceAttempt:
    cleanup_expired()
    attempt = DeviceAttempt(
        attempt_id=attempt_id,
        device_auth_id=device_auth_id,
        user_code=user_code,
        interval=interval,
        expires_at_value=expires_at,
    )
    with _lock:
        _device_attempts[attempt_id] = attempt
    return attempt


def get_device_attempt(attempt_id: str) -> DeviceAttempt | None:
    cleanup_expired()
    with _lock:
        attempt = _device_attempts.get(attempt_id)
    if attempt is None or attempt.expired():
        return None
    return attempt


def pop_device_attempt(attempt_id: str) -> DeviceAttempt | None:
    cleanup_expired()
    with _lock:
        return _device_attempts.pop(attempt_id, None)


def cleanup_expired() -> None:
    now = time.time()
    with _lock:
        expired = [
            state for state, attempt in _attempts.items() if now > attempt.expires_at
        ]
        for state in expired:
            _attempts.pop(state, None)
        expired_devices = [
            attempt_id
            for attempt_id, attempt in _device_attempts.items()
            if now > attempt.expires_at
        ]
        for attempt_id in expired_devices:
            _device_attempts.pop(attempt_id, None)
