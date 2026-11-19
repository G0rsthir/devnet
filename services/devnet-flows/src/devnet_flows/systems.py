"""
The systems that the tasks talk to: their clients, built from devnet.yaml, and the errors that can pass
"""

from http import HTTPStatus
from typing import Any

from prefect import Task
from prefect.client.schemas.objects import State, TaskRun

from devnet_config import get_config
from devnet_core.exceptions import ConfigurationError, SystemConnectionError
from system_ise.client import IseClient
from system_netbox.client import NetboxClient


def netbox() -> NetboxClient:
    return NetboxClient(get_config().systems.netbox)


def ise() -> IseClient:
    """
    Raises:
        ConfigurationError: If devnet.yaml has no system
    """
    config = get_config().systems.ise
    if config is None:
        raise ConfigurationError("systems.ise is not configured")
    return IseClient(config)


def transient(task: Task[..., Any], task_run: TaskRun, state: State) -> bool:
    """
    `retry_condition_fn` of the tasks: retry only an error that can pass

    A timeout, a refused connection, 429 and 5xx can pass. A 4xx, a config error or a bug fails the same way again
    """
    error = state.data
    if not isinstance(error, SystemConnectionError):
        return False
    status = error.status_code
    return status is None or status == HTTPStatus.TOO_MANY_REQUESTS or status >= HTTPStatus.INTERNAL_SERVER_ERROR
