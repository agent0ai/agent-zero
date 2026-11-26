from collections.abc import Mapping, MutableMapping
import hashlib
import os
import secrets

from helpers import dotenv
from helpers.team_store import TeamAccount, get_store


TEAM_SESSION_KEY = "team_session"


def team_mode_enabled() -> bool:
    return os.getenv("A0_TEAM_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


def _team_login_available() -> bool:
    return bool(
        team_mode_enabled()
        and dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
        and dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD)
    )


def get_credentials_hash():
    user = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
    password = dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD)
    if not user:
        return None
    return hashlib.sha256(f"{user}:{password}".encode()).hexdigest()


def is_login_required():
    user = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
    return bool(user) or team_mode_enabled()


def team_account_for_session(token: object) -> TeamAccount | None:
    if isinstance(token, str) and _team_login_available():
        return get_store().account_for_session(token)
    return None


def is_admin_session(values: Mapping) -> bool:
    if TEAM_SESSION_KEY in values or (team_mode_enabled() and not _team_login_available()):
        return False
    expected = get_credentials_hash()
    actual = values.get("authentication")
    return bool(expected and isinstance(actual, str) and secrets.compare_digest(actual.encode(), expected.encode()))


def is_authenticated(values: Mapping) -> bool:
    if TEAM_SESSION_KEY in values:
        return team_account_for_session(values[TEAM_SESSION_KEY]) is not None
    if not team_mode_enabled() and get_credentials_hash() is None:
        return True
    return is_admin_session(values)


def clear_session(values: MutableMapping) -> None:
    token = values.get(TEAM_SESSION_KEY)
    if isinstance(token, str) and team_mode_enabled():
        get_store().revoke_session(token)
    values.clear()


def authenticate(username: str, password: str, values: MutableMapping) -> bool:
    admin_name = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
    admin_password = dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD)
    if admin_name and username == admin_name and admin_password is not None and secrets.compare_digest(
        password.encode(), admin_password.encode(),
    ):
        if not team_mode_enabled() or _team_login_available():
            clear_session(values)
            values["authentication"] = get_credentials_hash()
            return True
    if not _team_login_available() or (admin_name and username.strip().lower() == admin_name.strip().lower()):
        return False
    token = get_store().sign_in(username, password)
    if token is None:
        return False
    clear_session(values)
    values[TEAM_SESSION_KEY] = token
    return True
