import locale
import os
import re
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

def _read_env_lines(dotenv_path: str) -> list[str]:
    # Loaders (python-dotenv) always read .env as UTF-8, so writes must be UTF-8 too.
    # Older versions wrote with the platform locale encoding on Windows; tolerate those
    # bytes so a legacy file can still be updated instead of crashing the save.
    with open(dotenv_path, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return raw.decode(locale.getencoding(), errors="replace").splitlines(keepends=True)

def save_dotenv_value(key: str, value: str, reload_env: bool = True):
    if value is None:
        value = ""
    dotenv_path = get_dotenv_file_path()
    if not os.path.isfile(dotenv_path):
        with open(dotenv_path, "w", encoding="utf-8") as f:
            f.write("")
    lines = _read_env_lines(dotenv_path)
    found = False
    for i, line in enumerate(lines):
        if re.match(rf"^\s*{key}\s*=", line):
            lines[i] = f"{key}={value}\n"
            found = True
    if not found:
        lines.append(f"\n{key}={value}\n")
    with open(dotenv_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    if reload_env:
        load_dotenv()
