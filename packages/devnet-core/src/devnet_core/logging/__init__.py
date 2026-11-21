import logging
from typing import Final

ROOT_LOGGER: Final = "devnet"


def get_logger(name: str) -> logging.Logger:
    """
    Return the logger for a module, under the `devnet` namespace

    Each service configures `devnet` logger in its own logging config

    """
    if name == ROOT_LOGGER or name.startswith(f"{ROOT_LOGGER}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{ROOT_LOGGER}.{name}")
