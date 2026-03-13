import fnmatch
import glob
import json
import os
import tempfile
import threading
from typing import Any

from helpers.files import get_abs_path

_runtime_lock = threading.RLock()
_runtime_store: dict[str, Any] = {}

_persistent_lock = threading.RLock()


def _persistent_dir() -> str:
    return get_abs_path("usr", "kvp")


def _validate_key(key: str) -> None:
    if not key:
        raise ValueError("key must not be empty")
    if "\x00" in key:
        raise ValueError("key contains NUL")
    if "/" in key or os.path.sep in key or (os.path.altsep and os.path.altsep in key):
        raise ValueError("key must not contain path separators")


def _key_to_path(key: str) -> str:
    _validate_key(key)
    return os.path.join(_persistent_dir(), f"{key}.json")


def get_runtime(key: str, default: Any = None) -> Any:
    with _runtime_lock:
        return _runtime_store.get(key, default)


def set_runtime(key: str, value: Any) -> None:
    _validate_key(key)
    with _runtime_lock:
        _runtime_store[key] = value


def remove_runtime(key: str) -> None:
    with _runtime_lock:
        _runtime_store.pop(key, None)


def find_runtime(pattern: str) -> list[str]:
    if not pattern:
        return []
    with _runtime_lock:
        return sorted([k for k in _runtime_store.keys() if fnmatch.fnmatch(k, pattern)])


def get_persistent(key: str, default: Any = None) -> Any:
    path = _key_to_path(key)
    with _persistent_lock:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return default


def set_persistent(key: str, value: Any) -> None:
    path = _key_to_path(key)
    dir_path = os.path.dirname(path)

    with _persistent_lock:
        os.makedirs(dir_path, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(prefix=f"{key}.", suffix=".tmp", dir=dir_path)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except OSError:
                pass


def remove_persistent(key: str) -> None:
    path = _key_to_path(key)
    with _persistent_lock:
        try:
            os.unlink(path)
        except FileNotFoundError:
            return


def find_persistent(pattern: str) -> list[str]:
    if not pattern:
        return []

    dir_path = _persistent_dir()
    with _persistent_lock:
        if not os.path.isdir(dir_path):
            return []

        search = os.path.join(dir_path, f"{pattern}.json")
        paths = glob.glob(search)
        keys = [os.path.basename(p)[: -len(".json")] for p in paths]
        keys.sort()
        return keys
