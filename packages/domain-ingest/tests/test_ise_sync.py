from typing import Any

import pytest
from fake_ise import FakeIse
from fake_netbox import FakeNetbox

from devnet_core.exceptions import DataIntegrityError
from devnet_core.sync import SyncReport
from domain_ingest.ise import sync_device

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def netbox(monkeypatch: pytest.MonkeyPatch) -> FakeNetbox:
    monkeypatch.setenv("NETBOX_TOKEN", "test")
    fake = FakeNetbox()
    fake.add("devices", name="sw1", primary_ip4={"address": "10.0.0.1/24"})
    return fake


@pytest.fixture
def ise(monkeypatch: pytest.MonkeyPatch) -> FakeIse:
    monkeypatch.setenv("ISE_USERNAME", "test")
    monkeypatch.setenv("ISE_PASSWORD", "test")
    return FakeIse()


def sw1(netbox: FakeNetbox) -> dict[str, Any]:
    return netbox.find("devices", name="sw1")


async def run(netbox: FakeNetbox, ise: FakeIse, *, device_id: int = 1, **options: Any) -> SyncReport:
    async with netbox.client() as netbox_client, ise.client() as ise_client:
        return await sync_device(netbox_client, ise_client, device_id=device_id, **options)


async def test_dry_run_shows_the_change_and_writes_nothing(netbox: FakeNetbox, ise: FakeIse) -> None:
    report = await run(netbox, ise)

    assert report.planned == {"create": 1, "update": 0, "delete": 0, "no-change": 0}
    assert ise.writes == []


async def test_first_run_creates_the_device_and_the_second_changes_nothing(netbox: FakeNetbox, ise: FakeIse) -> None:
    report = await run(netbox, ise, dry_run=False)

    assert report.applied == {"create": 1}
    device = ise.find(name="sw1")
    # The NetBox ID: a later run finds the device after a rename or a delete in NetBox
    assert device["description"] == "NetBox device 1"
    # The address of the device, not the subnet of its interface
    assert device["NetworkDeviceIPList"] == [{"ipaddress": "10.0.0.1", "mask": 32}]

    ise.writes.clear()
    report = await run(netbox, ise, dry_run=False)

    assert report.planned["no-change"] == 1
    assert ise.writes == []


async def test_rename_and_new_address_update_the_device(netbox: FakeNetbox, ise: FakeIse) -> None:
    await run(netbox, ise, dry_run=False)
    sw1(netbox).update(name="sw1-new", primary_ip4={"address": "10.0.0.2/24"})

    report = await run(netbox, ise, dry_run=False)

    assert report.applied == {"update": 1}
    device = ise.find(description="NetBox device 1")
    assert device["name"] == "sw1-new"
    assert device["NetworkDeviceIPList"] == [{"ipaddress": "10.0.0.2", "mask": 32}]


async def test_device_deleted_in_netbox_is_deleted_in_ise(netbox: FakeNetbox, ise: FakeIse) -> None:
    await run(netbox, ise, dry_run=False)
    del netbox.rows["devices"][sw1(netbox)["id"]]

    report = await run(netbox, ise, dry_run=False)

    assert report.applied == {"delete": 1}
    assert ise.devices == {}


async def test_device_without_address_changes_nothing(netbox: FakeNetbox, ise: FakeIse) -> None:
    await run(netbox, ise, dry_run=False)
    sw1(netbox)["primary_ip4"] = None
    ise.writes.clear()

    report = await run(netbox, ise, dry_run=False)

    # A missing address is more likely a gap in NetBox than a reason to delete the device from ISE
    assert ise.writes == []
    assert "sw1 has no primary IPv4 address: ISE is not changed" in report.warnings


async def test_device_that_a_person_created_in_ise_is_not_changed(netbox: FakeNetbox, ise: FakeIse) -> None:
    ise.add(name="sw1", description="core switch", NetworkDeviceIPList=[{"ipaddress": "10.9.9.9", "mask": 32}])

    report = await run(netbox, ise, dry_run=False)

    # devnet doesn't take over a device without its NetBox ID. ISE rejects a second device with the name
    assert report.failures == ["create network_device 1: ise: 400 Bad Request. Device name already exists"]
    assert ise.find(name="sw1")["description"] == "core switch"


async def test_two_ise_devices_with_one_netbox_id_stop_the_run(netbox: FakeNetbox, ise: FakeIse) -> None:
    for name in ("sw1", "sw1-copy"):
        ise.add(name=name, description="NetBox device 1", NetworkDeviceIPList=[])

    with pytest.raises(DataIntegrityError, match="ISE has 2 devices for NetBox device 1: sw1, sw1-copy"):
        await run(netbox, ise, dry_run=False)
