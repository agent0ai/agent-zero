from __future__ import annotations

import os
import platform
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable


APT_LOCK_TIMEOUT_SECONDS = 240
APT_LOCK_RETRY_SECONDS = 5
KALI_SUITE = "kali-last-snapshot"
KALI_SOURCE_FILES = (
    Path("/etc/apt/sources.list"),
    Path("/etc/apt/sources.list.d/kali.sources"),
)

_apt_lock = threading.RLock()


def run_runtime_apt(command: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    """Run runtime repairs with the Docker build's Kali package sources."""
    with _apt_lock:
        if platform.freedesktop_os_release().get("ID") == "kali":
            for source in KALI_SOURCE_FILES:
                if source.is_file():
                    original = source.read_text(encoding="utf-8")
                    updated = original.replace("kali-rolling", KALI_SUITE)
                    if updated != original:
                        source.write_text(updated, encoding="utf-8")

        return run_apt_with_retries(
            lambda: subprocess.run(
                command,
                check=False,
                text=True,
                capture_output=True,
                timeout=timeout,
                env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"},
            )
        )


def run_apt_with_retries(
    runner: Callable[[], subprocess.CompletedProcess[str]],
    *,
    lock_timeout_seconds: int = APT_LOCK_TIMEOUT_SECONDS,
    retry_seconds: int = APT_LOCK_RETRY_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Run an apt/dpkg command, serializing in-process callers and waiting out apt locks."""

    with _apt_lock:
        deadline = time.monotonic() + max(0, lock_timeout_seconds)
        while True:
            result = runner()
            if result.returncode == 0 or not is_apt_lock_error(result):
                return result
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return result
            time.sleep(min(max(1, retry_seconds), remaining))


def is_apt_lock_error(result: subprocess.CompletedProcess[str]) -> bool:
    output = f"{result.stderr or ''}\n{result.stdout or ''}".lower()
    return (
        "could not get lock" in output
        or "unable to lock directory" in output
        or "unable to acquire the dpkg frontend lock" in output
        or "is another process using it" in output
    )
