import os
import re
import tempfile
from typing import Any

from .files import get_abs_path
from dotenv import load_dotenv as _load_dotenv

KEY_AUTH_LOGIN = "AUTH_LOGIN"
KEY_AUTH_PASSWORD = "AUTH_PASSWORD"
KEY_RFC_PASSWORD = "RFC_PASSWORD"
KEY_ROOT_PASSWORD = "ROOT_PASSWORD"

def load_dotenv():
    _load_dotenv(get_dotenv_file_path(), override=True)


def get_dotenv_file_path():
    return get_abs_path("usr/.env")

def get_dotenv_value(key: str, default: Any = None):
    # load_dotenv()       
    return os.getenv(key, default)

def save_dotenv_value(key: str, value: str, reload_env: bool = True):
    if value is None:
        value = ""
    dotenv_path = get_dotenv_file_path()
    directory = os.path.dirname(dotenv_path) or "."
    os.makedirs(directory, exist_ok=True)
    if os.path.isfile(dotenv_path):
        with open(dotenv_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []
    found = False
    for i, line in enumerate(lines):
        if re.match(rf"^\s*{key}\s*=", line):
            lines[i] = f"{key}={value}\n"
            found = True
    if not found:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(f"{key}={value}\n")
    fd, tmp_path = tempfile.mkstemp(prefix=".env.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w") as f:
            f.writelines(lines)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, dotenv_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    # Import here because the secrets manager also reads dotenv configuration.
    from helpers.secrets import SecretsManager
    SecretsManager._invalidate_all_caches()
    if reload_env:
        load_dotenv()
