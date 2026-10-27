from collections.abc import Callable, Generator
from contextlib import contextmanager

import httpx2

from devnet_core.exceptions import SystemConnectionError
from devnet_core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = httpx2.Timeout(30.0, connect=10.0)


MESSAGE_KEYS = ("detail", "message", "error")

type MessageParser = Callable[[httpx2.Response], str | None]


def build_client(
    *,
    base_url: str,
    verify_tls: bool,
    timeout: httpx2.Timeout = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    transport: httpx2.AsyncBaseTransport | None = None,
) -> httpx2.AsyncClient:
    """
    HTTP client for system APIs

    Certificates are verified against the system trust store (httpx2 uses truststore)

    Args:
        transport: Where requests go instead of the network, e.g. an `httpx2.MockTransport`
    """
    return httpx2.AsyncClient(
        base_url=base_url,
        verify=verify_tls,
        timeout=timeout,
        headers=headers,
        trust_env=False,
        transport=transport,
    )


def _error_reason(exc: BaseException) -> str:
    """
    First non-empty message in the exception chain. httpx2 connection errors often have an empty message,
    while the cause underneath has the real reason, e.g. an ssl or socket error.
    """
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if msg := str(current).strip():
            return msg
        current = current.__cause__ or current.__context__
    return type(exc).__name__


def system_message(response: httpx2.Response) -> str | None:
    """
    Default MessageParser
    """
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None
    for key in MESSAGE_KEYS:
        if isinstance(value := body.get(key), str) and value.strip():
            return value.strip()
    return None


def _parse_message(response: httpx2.Response, message_parser: MessageParser) -> str | None:
    try:
        return message_parser(response)
    except Exception:
        logger.warning("Error message parser %r failed", message_parser, exc_info=True)
        return None


@contextmanager
def connection_errors(name: str, *, message_parser: MessageParser = system_message) -> Generator[None]:
    """
    Translate httpx2 errors into SystemConnectionError with a readable message

    Args:
        name: System name, included in the message
        message_parser: Reads the system's error message from an error response
    """
    try:
        yield
    except httpx2.HTTPStatusError as e:
        response = e.response
        msg = f"{response.status_code} {response.reason_phrase}"
        system_msg = _parse_message(response, message_parser)
        if system_msg:
            msg = f"{msg}. {system_msg}"
        raise SystemConnectionError(name=name, msg=msg) from e
    except httpx2.TimeoutException as e:
        raise SystemConnectionError(name=name, msg="Connection timed out") from e
    except httpx2.HTTPError as e:
        raise SystemConnectionError(name=name, msg=f"Unable to connect: {_error_reason(e)}") from e
