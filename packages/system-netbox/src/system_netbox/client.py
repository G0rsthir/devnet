from typing import Self

import httpx2

from devnet_core.connections.http import build_client
from system_netbox.config import NetboxConfig


class NetboxClient:
    """
    Netbox REST API client

    Usage:
        async with NetboxClient(config) as client:
            await client.get_version()
    """

    def __init__(self, config: NetboxConfig, *, transport: httpx2.AsyncBaseTransport | None = None):
        self.config = config
        self._transport = transport
        self._client: httpx2.AsyncClient | None = None

    @property
    def client(self) -> httpx2.AsyncClient:
        if self._client is None:
            raise RuntimeError("NetboxClient must be used as an async context manager")
        return self._client

    async def __aenter__(self) -> Self:
        self._client = build_client(
            base_url=self.config.base_url, verify_tls=self.config.verify_tls, transport=self._transport
        )
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._client is not None:
            await self._client.__aexit__(exc_type, exc_value, traceback)
            self._client = None

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx2.Response:
        with connection_errors(self.config.name, message_key=ERROR_MESSAGE_KEY):
            response = await self.client.request(method, path, **kwargs)
            response.raise_for_status()
            return response

    def _parse[M: BaseModel](self, response: httpx2.Response, model: type[M]) -> M:
        try:
            return model.model_validate_json(response.content)
        except ValidationError as e:
            raise DataSourceConnectionError(
                source_name=self.config.name, msg=f"Unexpected response from {response.request.url.path}"
            ) from e

    async def _login(self) -> None:
        response = await self._request(
            "POST",
            "/api/v2/sessions",
            json={
                "username": self.config.username,
                "password": self.config.password,
                "provider": self.config.provider.value,
            },
        )
        session = self._parse(response, _SessionResponse)
        self.client.headers["Authorization"] = f"Bearer {session.sessionId}"

    async def get_version(self) -> str | None:
        response = await self._request("GET", "/api/v2/version")
        return self._parse(response, _VersionResponse).version
