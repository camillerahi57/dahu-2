def remove_digits(s: str) -> str:
    return ''.join([c for c in s if not c.isdigit()])