"""
Loggers for all devnet code, under one `devnet` namespace.

Every module gets its logger with `get_logger(__name__)`, so `compliance/collect.py` logs as
`devnet.compliance.collect`. Each service then configures all of them through the one `devnet`
logger in its own logging config; this package only names them.
"""

import logging
from typing import Final

ROOT_LOGGER: Final = "devnet"


def get_logger(name: str) -> logging.Logger:
    """
    Return the logger for a module, under the `devnet` namespace.

    `get_logger(__name__)` in `compliance/collect.py` returns the `devnet.compliance.collect` logger.
    """
    if name == ROOT_LOGGER or name.startswith(f"{ROOT_LOGGER}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{ROOT_LOGGER}.{name}")
