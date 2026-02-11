import hashlib

from python.helpers import dotenv


def get_credentials_hash():
    user = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
    password = dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD)
    if not user:
        return None
    return hashlib.sha256(f"{user}:{password}".encode()).hexdigest()


def is_login_required():
    user = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
    return bool(user)
