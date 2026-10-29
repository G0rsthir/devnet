import httpx2
from pydantic import BaseModel, Field

from devnet_core.connections.base import ConnectivityInfo
from devnet_core.connections.client import ApiClient
from devnet_core.connections.http import system_message
from system_netbox.config import NetboxConfig


class _Status(BaseModel):
    netbox_version: str = Field(alias="netbox-version")


class NetboxClient(ApiClient[NetboxConfig]):
    """
    Netbox REST API client

    Usage:
        async with NetboxClient(config) as client:
            await client.check_connectivity()
    """

    def _headers(self) -> dict[str, str]:
        # v2 token: nbt_<key>.<token>
        return {"Authorization": f"Bearer {self.config.token.get_secret_value()}"}

    async def check_connectivity(self) -> ConnectivityInfo:
        response = await self._request("GET", "/api/status/")
        return ConnectivityInfo(version=self._parse(response, _Status).netbox_version)

    def _error_message(self, response: httpx2.Response) -> str | None:
        # Validation errors come back as {"field": ["message", ...]}
        message = system_message(response)
        if message:
            return message
        try:
            body = response.json()
        except ValueError:
            return None
        if not isinstance(body, dict):
            return None
        return "; ".join(
            f"{field}: {' '.join(map(str, errors)) if isinstance(errors, list) else errors}"
            for field, errors in body.items()
        )

    async def find(self, path: str, **filters: str) -> dict[str, Any] | None:
        """
        The object at `path` matching the filters, e.g. find("/api/extras/webhooks/", name="devnet")
        """
        response = await self._request("GET", path, params={**filters, "limit": 1})
        results = self._parse(response, _Page).results
        return results[0] if results else None

    async def create(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._parse(await self._request("POST", path, json=data), dict[str, Any])

    async def update(self, path: str, id: int, data: dict[str, Any]) -> dict[str, Any]:
        return self._parse(await self._request("PATCH", f"{path}{id}/", json=data), dict[str, Any])
