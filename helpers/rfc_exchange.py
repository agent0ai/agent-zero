from helpers import crypto, dotenv

async def get_root_password():
    return _get_root_password()

def _provide_root_password(public_key_pem: str):
    pswd = _get_root_password()
    enc = crypto.encrypt_data(pswd, public_key_pem)
    return enc

def _get_root_password():
    return dotenv.get_dotenv_value(dotenv.KEY_ROOT_PASSWORD) or ""
