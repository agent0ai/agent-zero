"""save_dotenv_value must write the encoding python-dotenv reads back (UTF-8).

Opening the file without `encoding=` used the platform default (GBK/CP1252), so one
non-ASCII value made the whole `usr/.env` undecodable on the next load.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import dotenv  # noqa: E402

VALUE = "caf\u00e9 \u5bc6\u7801"


def test_save_dotenv_value_writes_utf8_and_keeps_other_values(
    tmp_path, monkeypatch
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("EXISTING_VALUE=caf\u00e9\n", encoding="utf-8")
    monkeypatch.setattr(dotenv, "get_dotenv_file_path", lambda: str(env_path))
    monkeypatch.setattr(dotenv, "load_dotenv", lambda: None)

    dotenv.save_dotenv_value("NON_ASCII_VALUE", VALUE, reload_env=False)

    assert VALUE.encode("utf-8") in env_path.read_bytes()
    values = dotenv_values(str(env_path))
    assert values["EXISTING_VALUE"] == "caf\u00e9"
    assert values["NON_ASCII_VALUE"] == VALUE
