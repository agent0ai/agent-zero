from helpers import dotenv
import hashlib


def _present(value) -> bool:
    return bool(value) and bool(str(value).strip())


def _auth_values():
    user = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
    password = dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD)
    return user, password


def get_credentials_hash():
    user, password = _auth_values()
    if not _present(user) and not _present(password):
        return None
    # Either remnant means auth was configured. Hash both halves so a
    # missing login or password cannot match a complete sign-in attempt.
    return hashlib.sha256(f"{user or ''}:{password or ''}".encode()).hexdigest()


def is_login_required():
    user, password = _auth_values()
    return _present(user) or _present(password)
