"""
The contract between the two sides of a device import

Both adapters build these models. DiffSync pairs objects by `_identifiers` and compares `_attributes`.
Identifiers are names that both systems know, never database IDs: the source can then build the whole
tree before anything exists in NetBox, and a dry run shows every change.

    device
    └── interface
        ├── ip_address
        └── mac_address
"""

from collections.abc import Iterator
from typing import ClassVar

from diffsync import DiffSyncModel
from diffsync.diff import Diff, DiffElement
from diffsync.enum import DiffSyncActions


class Device(DiffSyncModel):
    _modelname: ClassVar[str] = "device"
    _identifiers: ClassVar[tuple[str, ...]] = ("name",)
    _attributes: ClassVar[tuple[str, ...]] = ("serial",)
    _children: ClassVar[dict[str, str]] = {"interface": "interfaces"}

    # As in NetBox. The hostname on the device can differ
    name: str
    serial: str = ""
    interfaces: list[str] = []


class Interface(DiffSyncModel):
    _modelname: ClassVar[str] = "interface"
    _identifiers: ClassVar[tuple[str, ...]] = ("device", "name")
    _shortname: ClassVar[tuple[str, ...]] = ("name",)
    _attributes: ClassVar[tuple[str, ...]] = ("type", "enabled", "description", "mtu", "parent")
    _children: ClassVar[dict[str, str]] = {"ip_address": "ip_addresses", "mac_address": "mac_addresses"}

    device: str
    name: str
    # A NetBox interface type, e.g. virtual, lag, 1000base-sx
    type: str = "other"
    enabled: bool = True
    description: str = ""
    mtu: int | None = None
    # Name of the parent interface, for a subinterface
    parent: str | None = None
    ip_addresses: list[str] = []
    mac_addresses: list[str] = []


class IPAddress(DiffSyncModel):
    _modelname: ClassVar[str] = "ip_address"
    _identifiers: ClassVar[tuple[str, ...]] = ("device", "interface", "address", "vrf")
    _shortname: ClassVar[tuple[str, ...]] = ("address",)
    _attributes: ClassVar[tuple[str, ...]] = ("status", "description")

    device: str
    interface: str
    # With prefix length, e.g. 10.0.0.1/24
    address: str
    # NetBox VRF name. None is the global table
    vrf: str | None = None
    status: str = "active"
    description: str = ""


class MACAddress(DiffSyncModel):
    _modelname: ClassVar[str] = "mac_address"
    _identifiers: ClassVar[tuple[str, ...]] = ("device", "interface", "mac")
    _shortname: ClassVar[tuple[str, ...]] = ("mac",)
    _attributes: ClassVar[tuple[str, ...]] = ("primary",)

    device: str
    interface: str
    mac: str
    # The interface's primary MAC address
    primary: bool = False


class DeviceDiff(Diff):
    """
    Order of the interface changes

    A subinterface needs its parent: create and update parents first, delete them last
    """

    @classmethod
    def order_children_interface(cls, children: dict[str, DiffElement]) -> Iterator[DiffElement]:
        def rank(element: DiffElement) -> int:
            is_subinterface = bool((element.source_attrs or element.dest_attrs or {}).get("parent"))
            if element.action == DiffSyncActions.DELETE:
                return 2 if is_subinterface else 3
            return 1 if is_subinterface else 0

        yield from sorted(children.values(), key=rank)
