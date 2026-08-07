import secrets
import string


def remove_digits(s: str) -> str:
    return ''.join([c for c in s if not c.isdigit()])


def rand_str(length=21) -> str:
    """Generates a random string of letters and digits."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


PREFIX_SEPARATOR = '____'

def add_random_prefix(string_: str) -> str:
    return rand_str() + PREFIX_SEPARATOR + string_

def remove_random_prefix(string_: str) -> str:
    if PREFIX_SEPARATOR in string_:
        return string_.split(PREFIX_SEPARATOR)[-1]
    else:
        return string_