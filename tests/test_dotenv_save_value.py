"""Regression tests for `helpers.dotenv.save_dotenv_value`.

This helper persists `usr/.env` — auth passwords, root password, provider API keys
and the CSRF allowed-origins list all go through it. The cases here cover the three
ways it used to damage or reject that file: locale-dependent encoding, an unescaped
key interpolated into a regex, and CRLF translation.
"""

from __future__ import annotations

import builtins
from contextlib import contextmanager
from unittest.mock import patch

import pytest

from helpers import dotenv

# A codec that is the platform default on a stock Windows install but cannot
# represent most of Unicode — cp1252 rejects CJK, cp936 rejects "ä".
LEGACY_CODEC = "cp1252"


@contextmanager
def legacy_default_encoding(codec: str = LEGACY_CODEC):
    """Make encoding-less `open()` calls behave as they do under a legacy locale.

    Monkeypatching `locale.getpreferredencoding` does not work: CPython reads the
    locale encoding at the C level, so `open()` ignores the patched function. This
    shim instead supplies a codec in exactly the position CPython would supply the
    locale's — only when the caller passed no `encoding` — so the tests fail on a
    machine of any locale when `encoding=` is missing, and pass on a machine of any
    locale when it is present.
    """
    real_open = builtins.open

    def shim(file, mode="r", *args, **kwargs):
        if "b" not in mode and kwargs.get("encoding") is None and len(args) < 2:
            kwargs["encoding"] = codec
        return real_open(file, mode, *args, **kwargs)

    with patch.object(builtins, "open", shim):
        yield


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    """Point the helper at a temp `.env` and stop it touching the real process env."""
    path = tmp_path / ".env"
    monkeypatch.setattr(dotenv, "get_dotenv_file_path", lambda: str(path))
    monkeypatch.setattr(dotenv, "load_dotenv", lambda: None)
    return path


def test_non_ascii_value_is_saved_under_a_legacy_locale(env_file):
    """A password or API key outside the codepage must still be persisted.

    Settings accepts any string as `auth_password` / `root_password`, so a user
    with an accented or CJK password used to get a UnicodeEncodeError from the
    save instead of a stored credential.
    """
    with legacy_default_encoding():
        dotenv.save_dotenv_value("AUTH_PASSWORD", "pässwörd-密码")

    assert env_file.read_text(encoding="utf-8").strip() == "AUTH_PASSWORD=pässwörd-密码"


def test_existing_non_ascii_content_does_not_break_an_ascii_save(env_file):
    """The file's *existing* bytes alone used to be enough to fail every save.

    A UTF-8 comment left by the user — or a value written earlier by
    `helpers/secrets.py`, which reads and writes this same file as UTF-8 — made
    `readlines()` raise, so a later save of a purely ASCII value failed too and
    the setting was silently never persisted.
    """
    env_file.write_bytes("# café ☕ setup\nAUTH_LOGIN=admin\n".encode("utf-8"))

    # cp1252 happens to map every byte, so use a codec that rejects them on read —
    # as cp936 (a Chinese Windows default) does for these exact bytes.
    with legacy_default_encoding("ascii"):
        dotenv.save_dotenv_value("AUTH_PASSWORD", "plain-ascii")

    text = env_file.read_text(encoding="utf-8")
    assert "AUTH_PASSWORD=plain-ascii" in text
    assert "# café ☕ setup" in text  # the comment survived unchanged
    assert "AUTH_LOGIN=admin" in text


def test_ascii_only_save_still_works_under_a_legacy_locale(env_file):
    """Control: the case the old code got right must not regress."""
    with legacy_default_encoding():
        dotenv.save_dotenv_value("AUTH_LOGIN", "admin")

    assert env_file.read_text(encoding="utf-8").strip() == "AUTH_LOGIN=admin"


def test_key_with_regex_metacharacters_does_not_rewrite_another_entry(env_file):
    """The key is interpolated into a pattern, so it must be escaped.

    Keys are built from request data (`API_KEY_{provider.upper()}` in
    `plugins/_model_config/api/api_keys.py` and `helpers/settings.py`, with no
    whitelist), so a key holding "." or "|" used to match a *different* line and
    overwrite its name — discarding the real key stored there.
    """
    env_file.write_text(
        "API_KEY_OPENAI=sk-real-openai\nAPI_KEY_OPENROUTER=sk-real-openrouter\n",
        encoding="utf-8",
    )

    dotenv.save_dotenv_value("API_KEY_OPEN.I", "injected")

    text = env_file.read_text(encoding="utf-8")
    assert "API_KEY_OPENAI=sk-real-openai" in text  # not clobbered
    assert "API_KEY_OPENROUTER=sk-real-openrouter" in text
    assert "API_KEY_OPEN.I=injected" in text  # appended as its own entry


def test_existing_key_is_updated_in_place(env_file):
    """Control for the escaping change: a normal key must still be replaced."""
    env_file.write_text("AUTH_LOGIN=old\nAUTH_PASSWORD=keep\n", encoding="utf-8")

    dotenv.save_dotenv_value("AUTH_LOGIN", "new")

    text = env_file.read_text(encoding="utf-8")
    assert "AUTH_LOGIN=new" in text
    assert "AUTH_LOGIN=old" not in text
    assert "AUTH_PASSWORD=keep" in text  # untouched


def test_saved_file_uses_lf_endings(env_file):
    """`.env` is also sourced by shells and read by Docker, which keep the CR.

    Text mode translated the LF endings written by the helper into CRLF on
    Windows, so a shell doing `. .env` bound `AUTH_PASSWORD` to "secret\\r".
    """
    env_file.write_text("AUTH_LOGIN=admin\n", encoding="utf-8")

    dotenv.save_dotenv_value("AUTH_PASSWORD", "secret")

    assert b"\r\n" not in env_file.read_bytes()
