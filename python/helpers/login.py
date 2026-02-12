import hashlib
import hmac

from python.helpers import dotenv


def get_credentials_hash():
    user = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
    password = dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD)
    if not user:
        return None
    # HMAC-SHA256 for session token derivation (not password storage).
    # Using runtime persistent ID as HMAC key binds the token to this server instance.
    from python.helpers import runtime

    secret = runtime.get_persistent_id().encode()
    return hmac.new(secret, f"{user}:{password}".encode(), hashlib.sha256).hexdigest()


def is_login_required():
    user = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
    return bool(user)
