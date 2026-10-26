def empty_to_none(value: object) -> object:
    """
    A blank string means "no value".
    """
    if isinstance(value, str) and not value.strip():
        return None
    return value
