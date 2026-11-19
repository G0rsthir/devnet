import httpx2
import pytest
from pydantic import BaseModel, Field

from system_netbox.client import NetboxClient
from system_netbox.config import NetboxConfig
from system_netbox.endpoints import Endpoint
from system_netbox.models.generated import WritableDeviceRequest

pytestmark = pytest.mark.anyio

DEVICE = {"id": 7, "name": "sw1", "serial": "FOC123", "primary_ip4": None}


class _Device(BaseModel):
    id: int
    name: str
    # The API name
    primary_ip: str | None = Field(default=None, alias="primary_ip4")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def requests(monkeypatch: pytest.MonkeyPatch) -> list[httpx2.Request]:
    monkeypatch.setenv("NETBOX_TOKEN", "test")
    return []


def client(requests: list[httpx2.Request]) -> NetboxClient:
    def handle(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        if request.url.path == "/api/dcim/devices/7/":
            return httpx2.Response(200, json=DEVICE)
        return httpx2.Response(200, json={"results": [DEVICE], "next": None})

    config = NetboxConfig(base_url="http://netbox.test", token="${NETBOX_TOKEN}")  # type: ignore[arg-type]
    return NetboxClient(config, transport=httpx2.MockTransport(handle))


async def test_select_reads_only_the_fields_of_the_model(requests: list[httpx2.Request]) -> None:
    async with client(requests) as netbox:
        devices = netbox.dcim.devices.select(_Device)
        found = await devices.find(site="lab")
        first = await devices.find_one(name="sw1")
        one = await devices.get(7)

    assert found == [first] == [one] == [_Device(id=7, name="sw1")]
    fields = "id,name,primary_ip4"
    assert [dict(request.url.params) for request in requests] == [
        {"site": "lab", "fields": fields, "start": "0", "limit": "1000"},
        {"name": "sw1", "fields": fields, "limit": "1"},
        {"fields": fields},
    ]


async def test_without_select_every_field_is_read(requests: list[httpx2.Request]) -> None:
    async with client(requests) as netbox:
        await Endpoint(netbox, "/api/dcim/devices/", _Device, WritableDeviceRequest).get(7)

    assert str(requests[0].url) == "http://netbox.test/api/dcim/devices/7/"
