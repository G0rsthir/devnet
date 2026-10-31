import httpx2
from pydantic import BaseModel

from devnet_core.connections.base import ConnectivityInfo
from devnet_core.connections.client import ApiClient
from system_ise.config import IseConfig


class _OperationValue(BaseModel):
    name: str
    value: str


class _OperationResult(BaseModel):
    resultValue: list[_OperationValue]


class _Operation(BaseModel):
    OperationResult: _OperationResult


class IseClient(ApiClient[IseConfig]):
    """
    Cisco ISE ERS API client

    Usage:
        async with IseClient(config) as client:
            await client.check_connectivity()
    """

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}

    def _auth(self) -> httpx2.Auth:
        return httpx2.BasicAuth(self.config.username.get_secret_value(), self.config.password.get_secret_value())

    async def check_connectivity(self) -> ConnectivityInfo:
        # In the legacy API docs, not in the ERS OpenAPI schema
        response = await self._request("GET", "/ers/config/op/systemconfig/iseversion")
        values = self._parse(response, _Operation).OperationResult.resultValue
        return ConnectivityInfo(version=next((v.value for v in values if v.name == "version"), None))

    def _error_message(self, response: httpx2.Response) -> str | None:
        # Error: {"ERSResponse": {"messages": [{"title": "message", ...}, ...]}}
        message = super()._error_message(response)
        if message:
            return message
        try:
            body = response.json()
        except ValueError:
            return None
        if not isinstance(body, dict):
            return None
        messages = body.get("ERSResponse", {}).get("messages", [])
        return "; ".join(message["title"] for message in messages) or None
