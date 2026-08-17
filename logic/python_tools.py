import secrets
import string


def remove_digits(s: str) -> str:
    return ''.join([c for c in s if not c.isdigit()])


def rand_str(length=21) -> str:
    """Generates a random string of letters and digits."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))