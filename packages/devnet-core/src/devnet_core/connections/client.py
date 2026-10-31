from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Self

import httpx2
from pydantic import ValidationError

from devnet_core.connections.base import ConnectivityInfo
from devnet_core.connections.http import build_client, connection_errors, system_message
from devnet_core.exceptions import SystemConnectionError
from devnet_core.logging import get_logger
from devnet_core.serialization import cached_type_adapter
from devnet_core.settings.file import ConfigModel

logger = get_logger(__name__)


class HttpConfig(ConfigModel):
    """
    What every HTTP system needs. A system's config adds its credentials
    """

    name: str
    base_url: str
    verify_tls: bool = True


class ApiClient[C: HttpConfig](ABC):
    """
    Base for system clients

    Usage:
        async with ApiClient(config) as client:
            await client.check_connectivity()
    """

    def __init__(self, config: C, *, transport: httpx2.AsyncBaseTransport | None = None):
        self.config = config
        self._transport = transport
        self._http: httpx2.AsyncClient | None = None

    @property
    def http(self) -> httpx2.AsyncClient:
        if self._http is None:
            raise RuntimeError(f"{type(self).__name__} must be used as an async context manager")
        return self._http

    def _headers(self) -> dict[str, str]:
        """
        Headers sent with every request
        """
        return {}

    def _auth(self) -> httpx2.Auth | None:
        return None

    async def _authenticate(self) -> None:
        """
        Runs once after connecting
        """
        return None

    def _error_message(self, response: httpx2.Response) -> str | None:
        """
        The system's own error message from an error response
        """
        return system_message(response)

    @abstractmethod
    async def check_connectivity(self) -> ConnectivityInfo:
        """
        Authenticate and perform a lightweight request

        Raises:
            SystemConnectionError: If the system is unreachable or rejects the request
        """

    async def __aenter__(self) -> Self:
        self._http = build_client(
            base_url=self.config.base_url,
            verify_tls=self.config.verify_tls,
            headers=self._headers(),
            auth=self._auth(),
            transport=self._transport,
        )
        await self._http.__aenter__()
        try:
            await self._authenticate()
        except BaseException as e:
            await self.__aexit__(type(e), e, e.__traceback__)
            raise
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._http is not None:
            await self._http.__aexit__(exc_type, exc_value, traceback)
            self._http = None

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx2.Response:
        with connection_errors(self.config.name, message_parser=self._error_message):
            response = await self.http.request(method, path, **kwargs)
            # Not params or body: they can hold secrets
            logger.debug(
                "%s(%s): %s %s -> %d",
                self.__class__.__name__,
                self.config.name,
                method,
                path,
                response.status_code,
            )
            response.raise_for_status()
            return response

    def _parse[T](self, response: httpx2.Response, model: type[T]) -> T:
        """
        Also works with dataclasses
        """
        try:
            return cached_type_adapter(model).validate_json(response.content)
        except ValidationError as e:
            error = e.errors()[0]
            field = ".".join(str(part) for part in error["loc"]) or "body"
            raise SystemConnectionError(
                name=self.config.name,
                msg=f"Unexpected response from {response.request.url.path}: {field}: {error['msg']}",
            ) from e
