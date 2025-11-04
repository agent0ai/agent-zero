import random, string

def generate_id(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))
