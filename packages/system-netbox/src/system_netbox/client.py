from __future__ import annotations

from functools import cached_property

import httpx2
from pydantic import BaseModel, Field

from devnet_core.connections.base import ConnectivityInfo
from devnet_core.connections.client import ApiClient
from system_netbox.config import NetboxConfig
from system_netbox.endpoints import ExtrasEndpoints


class _Status(BaseModel):
    netbox_version: str = Field(alias="netbox-version")


class NetboxClient(ApiClient[NetboxConfig]):
    """
    Netbox REST API client

    Usage:
        async with NetboxClient(config) as client:
            await client.check_connectivity()
            webhook = await client.extras.webhooks.find_one(name="devnet")
    """

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.config.token.get_secret_value()}"}

    async def check_connectivity(self) -> ConnectivityInfo:
        response = await self._request("GET", "/api/status/")
        return ConnectivityInfo(version=self._parse(response, _Status).netbox_version)

    @cached_property
    def extras(self) -> ExtrasEndpoints:
        return ExtrasEndpoints(self)

    def _error_message(self, response: httpx2.Response) -> str | None:
        # Error: {"field": ["message", ...]}
        message = super()._error_message(response)
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
