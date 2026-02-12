import os
import re
import stat
from typing import Any

from dotenv import load_dotenv as _load_dotenv

from .files import get_abs_path

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
        with open(dotenv_path, "w") as f:
            f.write("")
    with open(dotenv_path, "r+") as f:
        lines = f.readlines()
        found = False
        for i, line in enumerate(lines):
            if re.match(rf"^\s*{key}\s*=", line):
                lines[i] = f"{key}={value}\n"
                found = True
        if not found:
            lines.append(f"\n{key}={value}\n")
        f.seek(0)
        # lgtm[py/clear-text-storage-sensitive-data]
        # Justification: .env file IS the intended credential store (gitignored, local-only).
        # File permissions restricted to 0o600 (owner read/write only) after write.
        f.writelines(lines)
        f.truncate()
    # Restrict .env file to owner read/write only (0o600)
    os.chmod(dotenv_path, stat.S_IRUSR | stat.S_IWUSR)
    load_dotenv()
