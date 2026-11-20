import hashlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

STUB_NAMES = (
    "helpers",
    "helpers.files",
    "helpers.dotenv",
    "helpers.secrets",
    "dotenv",
    "test_login_fail_closed_mod",
)


@pytest.fixture
def auth_mods(tmp_path, monkeypatch):
    missing = object()
    originals = {name: sys.modules.get(name, missing) for name in STUB_NAMES}

    helpers_pkg = types.ModuleType("helpers")
    helpers_pkg.__path__ = []

    files = types.ModuleType("helpers.files")
    files.get_abs_path = lambda *parts: str(tmp_path.joinpath(*parts))

    dotenv_pkg = types.ModuleType("dotenv")
    dotenv_pkg.load_dotenv = lambda *args, **kwargs: None

    secrets = types.ModuleType("helpers.secrets")

    class SecretsManager:
        @staticmethod
        def _invalidate_all_caches():
            return None

    secrets.SecretsManager = SecretsManager

    helpers_pkg.files = files
    helpers_pkg.secrets = secrets
    sys.modules["helpers"] = helpers_pkg
    sys.modules["helpers.files"] = files
    sys.modules["helpers.secrets"] = secrets
    sys.modules["dotenv"] = dotenv_pkg

    dotenv_spec = importlib.util.spec_from_file_location(
        "helpers.dotenv",
        PROJECT_ROOT / "helpers" / "dotenv.py",
    )
    dotenv_mod = importlib.util.module_from_spec(dotenv_spec)
    assert dotenv_spec and dotenv_spec.loader
    sys.modules["helpers.dotenv"] = dotenv_mod
    helpers_pkg.dotenv = dotenv_mod
    dotenv_spec.loader.exec_module(dotenv_mod)

    login_spec = importlib.util.spec_from_file_location(
        "test_login_fail_closed_mod",
        PROJECT_ROOT / "helpers" / "login.py",
    )
    login_mod = importlib.util.module_from_spec(login_spec)
    assert login_spec and login_spec.loader
    sys.modules["test_login_fail_closed_mod"] = login_mod
    login_spec.loader.exec_module(login_mod)

    monkeypatch.delenv("AUTH_LOGIN", raising=False)
    monkeypatch.delenv("AUTH_PASSWORD", raising=False)

    yield dotenv_mod, login_mod

    for name, original in originals.items():
        if original is missing:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original


def test_missing_auth_login_with_password_still_requires_login(auth_mods, monkeypatch):
    _dotenv_mod, login = auth_mods
    monkeypatch.setenv("AUTH_PASSWORD", "still-here")

    assert login.is_login_required() is True
    digest = login.get_credentials_hash()
    assert digest is not None
    assert digest == hashlib.sha256(b":still-here").hexdigest()
    assert digest != hashlib.sha256(b"admin:still-here").hexdigest()


def test_missing_password_with_login_still_requires_login(auth_mods, monkeypatch):
    _dotenv_mod, login = auth_mods
    monkeypatch.setenv("AUTH_LOGIN", "admin")

    assert login.is_login_required() is True
    digest = login.get_credentials_hash()
    assert digest == hashlib.sha256(b"admin:").hexdigest()
    assert digest != hashlib.sha256(b"admin:secret").hexdigest()


def test_both_credentials_missing_keeps_auth_optional(auth_mods):
    _dotenv_mod, login = auth_mods

    assert login.is_login_required() is False
    assert login.get_credentials_hash() is None


def test_complete_credentials_hash_matches_user_and_password(auth_mods, monkeypatch):
    _dotenv_mod, login = auth_mods
    monkeypatch.setenv("AUTH_LOGIN", "admin")
    monkeypatch.setenv("AUTH_PASSWORD", "secret")

    assert login.is_login_required() is True
    assert login.get_credentials_hash() == hashlib.sha256(b"admin:secret").hexdigest()


def test_save_dotenv_value_keeps_other_keys(auth_mods, tmp_path):
    dotenv_mod, _login = auth_mods
    env_path = tmp_path / "usr" / ".env"
    env_path.parent.mkdir(parents=True)
    env_path.write_text("AUTH_LOGIN=admin\nAUTH_PASSWORD=secret\nOTHER=keep\n")

    dotenv_mod.save_dotenv_value("AUTH_LOGIN", "admin", reload_env=False)

    text = env_path.read_text()
    assert "AUTH_LOGIN=admin" in text
    assert "AUTH_PASSWORD=secret" in text
    assert "OTHER=keep" in text
    assert not list(env_path.parent.glob(".env.*.tmp"))


def test_save_dotenv_value_creates_file_atomically(auth_mods, tmp_path):
    dotenv_mod, _login = auth_mods

    dotenv_mod.save_dotenv_value("AUTH_PASSWORD", "secret", reload_env=False)

    env_path = tmp_path / "usr" / ".env"
    assert env_path.read_text() == "AUTH_PASSWORD=secret\n"
    assert not list(env_path.parent.glob(".env.*.tmp"))
