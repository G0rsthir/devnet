from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

import httpx2
from pydantic import BaseModel

from devnet_core.serialization import cached_type_adapter
from system_netbox.models.generated import (
    VRF,
    CustomField,
    CustomFieldChoiceSet,
    Device,
    EventRule,
    Interface,
    IPAddress,
    MACAddress,
    MACAddressRequest,
    Tag,
    TagRequest,
    VRFRequest,
    Webhook,
    WebhookRequest,
    WritableCustomFieldChoiceSetRequest,
    WritableCustomFieldRequest,
    WritableDeviceRequest,
    WritableEventRuleRequest,
    WritableInterfaceRequest,
    WritableIPAddressRequest,
)

if TYPE_CHECKING:
    from system_netbox.client import NetboxClient

# NetBox
_MAX_PAGE_SIZE = 1000


class _Page[T](BaseModel):
    results: list[T]
    next: str | None = None


class _HasId(Protocol):
    id: int


# TODO remove unnececery comments
def _matches(desired: Any, actual: Any) -> bool:
    # Choice: {"value": "select", "label": "Selection"}
    if isinstance(actual, dict) and "value" in actual and not isinstance(desired, dict):
        return desired == actual["value"]
    # Related objects set by ID
    if isinstance(desired, int) and isinstance(actual, dict):
        return desired == actual.get("id")
    # object_types, event_types, tags: order doesn't matter
    if isinstance(desired, list) and isinstance(actual, list) and all(isinstance(v, str | dict) for v in desired):
        return len(desired) == len(actual) and all(any(_matches(d, a) for a in actual) for d in desired)
    # Related objects read back in full: compare only the keys we set, e.g. {"name": ...}
    if isinstance(desired, dict) and isinstance(actual, dict):
        return all(_matches(v, actual.get(k)) for k, v in desired.items())
    return desired == actual


# TODO remove ai logic
class Endpoint[T: _HasId, R]:
    """
    One NetBox endpoint

    Args:
        model: What NetBox returns, e.g. Webhook
        request: What create sends, e.g. WebhookRequest
        key: Field that identifies an object of this kind
        fields: Read only these fields. Set by select()
    """

    def __init__(
        self,
        client: NetboxClient,
        path: str,
        model: type[T],
        request: type[R],
        *,
        key: str = "name",
        fields: list[str] | None = None,
    ):
        self._client = client
        self.path = path
        self.model = model
        self.request = request
        self.key = key
        self.fields = fields

    def select[M: _HasId](self, model: type[M]) -> Endpoint[M, R]:
        """
        This endpoint, read into a model of the fields that a caller uses

        Reads ask NetBox for these fields only (`?fields=`): the full serializer of some objects is slow,
        and a NetBox upgrade can't break a field that isn't read

        Args:
            model: A pydantic model with an `id` field
        """
        fields = cast(type[BaseModel], model).model_fields
        names = [field.alias or name for name, field in fields.items()]
        return Endpoint(self._client, self.path, model, self.request, key=self.key, fields=names)

    def _read_params(self) -> dict[str, str]:
        return {"fields": ",".join(self.fields)} if self.fields else {}

    async def get(self, id: int) -> T:
        response = await self._client._request("GET", f"{self.path}{id}/", params=self._read_params())
        return self._client._parse(response, self.model)

    async def find_one(self, **filters: str) -> T | None:
        """
        Filters, e.g. find_one(name="devnet")
        """
        params = {**filters, **self._read_params(), "limit": 1}
        response = await self._client._request("GET", self.path, params=params)
        results = self._client._parse(response, _Page[self.model]).results
        return results[0] if results else None

    async def find(self, **filters: str) -> list[T]:
        """
        Every object matching the filters, ordered by ID, e.g. find(tag="devnet")
        """
        objects: list[T] = []
        # Paged by ID, not offset: an object deleted while paging can't make the next page skip one
        params: dict[str, str | int] = {**filters, **self._read_params(), "start": 0, "limit": _MAX_PAGE_SIZE}
        while True:
            response = await self._client._request("GET", self.path, params=params)
            page = self._client._parse(response, _Page[self.model])
            objects.extend(page.results)
            if page.next is None:
                return objects
            params["start"] = httpx2.URL(page.next).params["start"]

    async def create(self, data: R) -> T:
        body = cached_type_adapter(self.request).dump_python(data, mode="json", exclude_none=True)
        response = await self._client._request("POST", self.path, json=body)
        return self._client._parse(response, self.model)

    async def update(self, id: int, data: dict[str, Any]) -> T:
        """
        Change only the fields in `data`
        """
        response = await self._client._request("PATCH", f"{self.path}{id}/", json=data)
        return self._client._parse(response, self.model)

    async def delete(self, id: int) -> None:
        await self._client._request("DELETE", f"{self.path}{id}/")

    async def ensure(self, desired: R) -> int:
        """
        Create or update fields that differ

        Args:
            desired: Fields left as None aren't compared or written

        Returns:
            The object's ID
        """
        data = cached_type_adapter(self.request).dump_python(desired, mode="json", exclude_none=True)
        # Raw, not find_one: _matches compares against what NetBox sends back
        response = await self._client._request("GET", self.path, params={self.key: data[self.key], "limit": 1})
        results = self._client._parse(response, _Page[dict[str, Any]]).results
        if not results:
            return (await self.create(desired)).id
        found = results[0]
        changed = {k: v for k, v in data.items() if not _matches(v, found.get(k))}
        if changed:
            await self.update(found["id"], changed)
        return found["id"]


class DcimEndpoints:
    def __init__(self, client: NetboxClient):
        self.devices = Endpoint(client, "/api/dcim/devices/", Device, WritableDeviceRequest)
        self.interfaces = Endpoint(client, "/api/dcim/interfaces/", Interface, WritableInterfaceRequest)
        self.mac_addresses = Endpoint(client, "/api/dcim/mac-addresses/", MACAddress, MACAddressRequest)


class IpamEndpoints:
    def __init__(self, client: NetboxClient):
        self.ip_addresses = Endpoint(client, "/api/ipam/ip-addresses/", IPAddress, WritableIPAddressRequest)
        self.vrfs = Endpoint(client, "/api/ipam/vrfs/", VRF, VRFRequest)


class ExtrasEndpoints:
    def __init__(self, client: NetboxClient):
        self.custom_field_choice_sets = Endpoint(
            client, "/api/extras/custom-field-choice-sets/", CustomFieldChoiceSet, WritableCustomFieldChoiceSetRequest
        )
        self.custom_fields = Endpoint(client, "/api/extras/custom-fields/", CustomField, WritableCustomFieldRequest)
        self.event_rules = Endpoint(client, "/api/extras/event-rules/", EventRule, WritableEventRuleRequest)
        self.tags = Endpoint(client, "/api/extras/tags/", Tag, TagRequest, key="slug")
        self.webhooks = Endpoint(client, "/api/extras/webhooks/", Webhook, WebhookRequest)
