from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import quote

import httpx2
from pydantic import BaseModel

from devnet_core.exceptions import SystemConnectionError
from devnet_core.serialization import cached_type_adapter
from system_ise.models import NetworkDeviceGroup, NetworkDeviceGroupRequest, ResourceSummary

if TYPE_CHECKING:
    from system_ise.client import IseClient

# ISE
_MAX_PAGE_SIZE = 100


class _Link(BaseModel):
    href: str


class _SearchResult(BaseModel):
    resources: list[ResourceSummary]
    nextPage: _Link | None = None


class _Search(BaseModel):
    SearchResult: _SearchResult


class _HasId(Protocol):
    id: str


class Endpoint[T: _HasId, R]:
    """
    One ISE ERS endpoint

    Args:
        model: What ISE returns, e.g. NetworkDeviceGroup
        request: What create sends, e.g. NetworkDeviceGroupRequest
        wrapper: Key around the object in a body, e.g. {"NetworkDeviceGroup": {...}}
    """

    def __init__(self, client: IseClient, path: str, model: type[T], request: type[R], *, wrapper: str):
        self._client = client
        self.path = path
        self.model = model
        self.request = request
        self.wrapper = wrapper

    def _unwrap(self, response: httpx2.Response) -> T:
        return self._client._parse(response, dict[str, self.model])[self.wrapper]

    async def get(self, id: str) -> T:
        response = await self._client._request("GET", f"{self.path}/{id}")
        return self._unwrap(response)

    async def find_one(self, *, name: str) -> T | None:
        """
        ISE ignores case in the name, e.g. find_one(name="Location#All Locations")
        """
        try:
            response = await self._client._request("GET", f"{self.path}/name/{quote(name, safe='')}")
        except SystemConnectionError as e:
            if e.status_code == httpx2.codes.NOT_FOUND:
                return None
            raise
        return self._unwrap(response)

    async def find(self, **filters: str) -> list[ResourceSummary]:
        """
        Every object matching the filters, e.g. find(type="Location")
        """
        objects: list[ResourceSummary] = []
        params: dict[str, Any] = {
            "filter": [f"{field}.EQ.{value}" for field, value in filters.items()],
            "page": 1,
            "size": _MAX_PAGE_SIZE,
        }
        while True:
            response = await self._client._request("GET", self.path, params=params)
            result = self._client._parse(response, _Search).SearchResult
            objects.extend(result.resources)
            if result.nextPage is None:
                return objects
            params["page"] += 1

    async def create(self, data: R) -> T:
        body = cached_type_adapter(self.request).dump_python(data, mode="json", exclude_none=True)
        response = await self._client._request("POST", self.path, json={self.wrapper: body})
        # 201 with an empty body: the new object's URL is in Location
        return await self.get(response.headers["Location"].rsplit("/", 1)[-1])

    async def update(self, id: str, data: dict[str, Any]) -> T:
        """
        Change only the fields in `data`
        """
        response = await self._client._request("PATCH", f"{self.path}/{id}", json={self.wrapper: data})
        return self._unwrap(response)

    async def delete(self, id: str) -> None:
        await self._client._request("DELETE", f"{self.path}/{id}")

    async def ensure(self, desired: R) -> str:
        """
        Create or update fields that differ

        Args:
            desired: Fields left as None aren't compared or written

        Returns:
            The object's ID
        """
        data = cached_type_adapter(self.request).dump_python(desired, mode="json", exclude_none=True)
        found = await self.find_one(name=data["name"])
        if found is None:
            return (await self.create(desired)).id
        changed = {k: v for k, v in data.items() if getattr(found, k) != v}
        if changed:
            await self.update(found.id, changed)
        return found.id


class NetworkEndpoints:
    def __init__(self, client: IseClient):
        self.device_groups = Endpoint(
            client,
            "/ers/config/networkdevicegroup",
            NetworkDeviceGroup,
            NetworkDeviceGroupRequest,
            wrapper="NetworkDeviceGroup",
        )
