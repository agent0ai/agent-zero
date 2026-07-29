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

def save_dotenv_value(key: str, value: str):
    if value is None:
        value = ""
    dotenv_path = get_dotenv_file_path()
    if not os.path.isfile(dotenv_path):
        with open(dotenv_path, "w", encoding="utf-8") as f:
            f.write("")
    # UTF-8 explicitly: without it `open()` uses the platform's preferred encoding,
    # a legacy codepage on a stock Windows install. `helpers/secrets.py` reads and
    # writes this same file through `files.read_file`/`files.write_file`, which
    # default to UTF-8, so the two paths must agree.
    with open(dotenv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # The key is interpolated into a pattern, so escape it: an unescaped "." or "|"
    # would match a *different* line and rewrite its name, discarding that entry's
    # value. Keys reach here from request payloads (`API_KEY_{provider.upper()}`).
    key_pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    found = False
    for i, line in enumerate(lines):
        if key_pattern.match(line):
            lines[i] = f"{key}={value}\n"
            found = True
    if not found:
        lines.append(f"\n{key}={value}\n")
    # newline="" keeps the LF endings written above from being translated to CRLF
    # on Windows; this file is also sourced by shells and read by Docker.
    with open(dotenv_path, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    load_dotenv()
