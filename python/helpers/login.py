from python.helpers import dotenv
import hashlib


def get_credentials_hash():
    user = dotenv.get_dotenv_value("AUTH_LOGIN")
    password = dotenv.get_dotenv_value("AUTH_PASSWORD")
    if not user:
        return None
    return hashlib.sha256(f"{user}:{password}".encode()).hexdigest()


def is_login_required():
    user = dotenv.get_dotenv_value("AUTH_LOGIN")
    return bool(user)
