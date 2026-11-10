import logging
from collections.abc import MutableMapping
from typing import Any

import structlog

from devnet_core.logging import get_logger


def _logger_factory(*args: Any) -> logging.Logger:
    return get_logger("diffsync")


def _drop_run_context(_logger: Any, _method: str, event: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    # The same on every line of a run
    for key in ("src", "dst", "flags"):
        event.pop(key, None)
    return event


def configure_logging() -> None:
    """
    Send DiffSync's log events to the `devnet.diffsync` logger

    DiffSync logs with structlog. If nothing configures structlog, it prints every event to stdout.
    A service that configures structlog itself keeps its own setup.
    """
    if structlog.is_configured():
        return
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.format_exc_info,
            _drop_run_context,
            # event='Created' action='create' model='interface' unique_id='sw1__Gi0/1' diffs={...}
            structlog.processors.KeyValueRenderer(
                key_order=["event", "action", "model", "unique_id"], drop_missing=True
            ),
        ],
        logger_factory=_logger_factory,
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
