"""
The contract between a NetBox device and its ISE network device

The identifier is the NetBox ID. devnet writes it into the description of the ISE device, so the sync finds
the ISE device after the device is renamed or deleted in NetBox. An ISE device without it is not devnet's.
"""

from typing import ClassVar

from diffsync import DiffSyncModel


class NetworkDevice(DiffSyncModel):
    _modelname: ClassVar[str] = "network_device"
    _identifiers: ClassVar[tuple[str, ...]] = ("netbox_id",)
    _attributes: ClassVar[tuple[str, ...]] = ("name", "ip_addresses")

    netbox_id: int
    name: str
    # Sorted, with prefix length, e.g. 10.0.0.1/32
    ip_addresses: tuple[str, ...] = ()
