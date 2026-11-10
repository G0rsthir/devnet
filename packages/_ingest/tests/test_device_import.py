from typing import Any

import pytest
from fake_netbox import FakeNetbox

from ingest.device import CollectedDevice, CollectedInterface, import_device
from ingest.sync import SyncReport

pytestmark = pytest.mark.anyio

UPLINK = CollectedInterface(
    name="GigabitEthernet0/1",
    admin_up=True,
    oper_up=True,
    description="uplink",
    hardware_type="Gigabit Ethernet",
    mac_address="aabb.cc00.0100",
    mtu=1500,
    ipv4=["10.0.0.1/24"],
)
SUBINTERFACE = CollectedInterface(
    name="GigabitEthernet0/1.100",
    admin_up=True,
    oper_up=True,
    mac_address="aabb.cc00.0100",
    ipv4=["10.1.0.1/24"],
    vrf="servers",
)
LOOPBACK = CollectedInterface(name="Loopback0", admin_up=True, oper_up=True, ipv4=["192.0.2.1/32"])
DOWN = CollectedInterface(name="GigabitEthernet0/2", admin_up=False, oper_up=False)


def collected(*interfaces: CollectedInterface) -> CollectedDevice:
    return CollectedDevice(hostname="sw1.lab", serial="FOC123", interfaces=list(interfaces))


SW1 = collected(SUBINTERFACE, UPLINK, LOOPBACK, DOWN)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def netbox(monkeypatch: pytest.MonkeyPatch) -> FakeNetbox:
    monkeypatch.setenv("NETBOX_TOKEN", "test")
    fake = FakeNetbox()
    fake.add("devices", name="sw1", serial="")
    fake.add("vrfs", name="servers")
    return fake


async def run(netbox: FakeNetbox, device: CollectedDevice = SW1, **options: Any) -> SyncReport:
    async with netbox.client() as client:
        device_id = netbox.find("devices", name="sw1")["id"]
        return await import_device(client, device_id=device_id, device_name="sw1", collected=device, **options)


async def test_dry_run_shows_every_change_and_writes_nothing(netbox: FakeNetbox) -> None:
    report = await run(netbox)

    # 3 interfaces, 3 IP addresses, 1 MAC address. The down interface isn't created
    assert report.planned == {"create": 7, "update": 1, "delete": 0, "no-change": 0}
    assert report.applied == {}
    assert netbox.writes == []


async def test_first_import_creates_the_tree(netbox: FakeNetbox) -> None:
    report = await run(netbox, dry_run=False)

    assert report.ok, report.failures
    assert report.applied == {"create": 7, "update": 1}
    assert netbox.find("devices", name="sw1")["serial"] == "FOC123"

    uplink = netbox.find("interfaces", name="GigabitEthernet0/1")
    assert uplink["description"] == "uplink"
    assert uplink["mtu"] == 1500
    # The MAC address is created after its interface, then set as primary
    assert uplink["primary_mac_address"]["id"] == netbox.find("mac-addresses", mac_address="AA:BB:CC:00:01:00")["id"]

    # The parent is created first, although the device lists the subinterface first
    subinterface = netbox.find("interfaces", name="GigabitEthernet0/1.100")
    assert subinterface["type"] == {"value": "virtual"}
    assert subinterface["parent"]["id"] == uplink["id"]

    # Names become NetBox IDs at write time
    address = netbox.find("ip-addresses", address="10.1.0.1/24")
    assert address["vrf"]["id"] == netbox.find("vrfs", name="servers")["id"]
    assert address["assigned_object_id"] == subinterface["id"]
    assert netbox.find("ip-addresses", address="192.0.2.1/32")["role"] == {"value": "loopback"}

    assert not [row for row in netbox.rows["interfaces"].values() if row["name"] == "GigabitEthernet0/2"]


async def test_second_run_changes_nothing(netbox: FakeNetbox) -> None:
    await run(netbox, dry_run=False)
    netbox.writes.clear()

    report = await run(netbox, dry_run=False)

    assert report.planned == {"create": 0, "update": 0, "delete": 0, "no-change": 8}
    assert netbox.writes == []


async def test_changes_on_the_device_reach_netbox(netbox: FakeNetbox) -> None:
    await run(netbox, dry_run=False)
    netbox.writes.clear()

    renamed = UPLINK.model_copy(update={"description": "core uplink", "admin_up": False})
    report = await run(netbox, collected(renamed, SUBINTERFACE), dry_run=False)

    # Loopback0 is gone from the device: its address is deleted, then the interface
    assert report.applied == {"update": 2, "delete": 2}
    assert netbox.writes == ["PATCH interfaces", "PATCH ip-addresses", "DELETE ip-addresses", "DELETE interfaces"]
    uplink = netbox.find("interfaces", name="GigabitEthernet0/1")
    assert (uplink["description"], uplink["enabled"]) == ("core uplink", False)
    assert "Loopback0" not in [row["name"] for row in netbox.rows["interfaces"].values()]


async def test_empty_collection_deletes_nothing(netbox: FakeNetbox) -> None:
    # One interface is under the delete limit. Only the empty collection blocks its delete
    netbox.add("interfaces", device=netbox.find("devices", name="sw1")["id"], name="Loopback0", type="virtual")

    report = await run(netbox, collected(), dry_run=False)

    assert report.planned["delete"] == 0
    assert report.warnings == ["1 of 2 objects would be deleted: deletes blocked"]
    assert netbox.writes == ["PATCH devices"]
    assert netbox.find("interfaces", name="Loopback0")


async def test_mass_delete_is_blocked(netbox: FakeNetbox) -> None:
    await run(netbox, dry_run=False)
    netbox.writes.clear()

    # The device reports one interface of three: more likely a bad collection than a real change
    report = await run(netbox, collected(LOOPBACK), dry_run=False)

    assert report.warnings == ["5 of 8 objects would be deleted: deletes blocked"]
    assert netbox.writes == []


async def test_interface_that_opted_out_is_not_touched(netbox: FakeNetbox) -> None:
    device_id = netbox.find("devices", name="sw1")["id"]
    kept = {"type": "1000base-t", "description": "set by hand", "custom_fields": {"sync_enabled": False}}
    netbox.add("interfaces", device=device_id, name="GigabitEthernet0/1", **kept)
    netbox.add("interfaces", device=device_id, name="GigabitEthernet0/9", **kept)

    report = await run(netbox, collected(UPLINK, LOOPBACK), dry_run=False)

    # Not updated, no addresses added below it, and not deleted although the device doesn't report it
    assert report.applied == {"create": 2, "update": 1}
    assert netbox.find("interfaces", name="GigabitEthernet0/1")["description"] == "set by hand"
    assert netbox.find("interfaces", name="GigabitEthernet0/9")
    assert [row["address"] for row in netbox.rows["ip-addresses"].values()] == ["192.0.2.1/32"]


async def test_ip_only_ignores_interfaces_without_an_address(netbox: FakeNetbox) -> None:
    no_address = CollectedInterface(name="GigabitEthernet0/3", admin_up=True, oper_up=True)

    await run(netbox, collected(LOOPBACK, no_address), ip_only=True, dry_run=False)

    assert [row["name"] for row in netbox.rows["interfaces"].values()] == ["Loopback0"]


async def test_one_failure_does_not_stop_the_other_objects(netbox: FakeNetbox) -> None:
    netbox.reject_names.add("GigabitEthernet0/1")

    report = await run(netbox, dry_run=False)

    assert not report.ok
    # The subinterface fails too: its parent doesn't exist. The children of both are not tried
    assert report.failures == [
        "create interface sw1__GigabitEthernet0/1: netbox: 400 Bad Request. name: Rejected by the test.",
        "create interface sw1__GigabitEthernet0/1.100: interface GigabitEthernet0/1 is not in NetBox",
    ]
    assert report.applied == {"update": 1, "create": 2}
    assert netbox.find("interfaces", name="Loopback0")
