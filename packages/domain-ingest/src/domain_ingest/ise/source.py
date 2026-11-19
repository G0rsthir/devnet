from http import HTTPStatus
from ipaddress import ip_interface

from pydantic import BaseModel

from devnet_core.exceptions import SystemConnectionError
from devnet_core.sync import SyncAdapter
from domain_ingest.ise.models import NetworkDevice
from system_netbox.client import NetboxClient


class _Address(BaseModel):
    address: str


class _Device(BaseModel):
    id: int
    name: str
    primary_ip4: _Address | None = None


class NetboxDeviceSource(SyncAdapter):
    """
    Source: one NetBox device, as ISE must have it

    A device that NetBox does not have gives no model, so its ISE device is deleted. A device without
    a primary IPv4 address gives no model either, but counts as no data: the runner then blocks the delete.
    """

    network_device = NetworkDevice

    top_level = ["network_device"]

    def __init__(self, client: NetboxClient, *, device_id: int) -> None:
        super().__init__(name=f"netbox device {device_id}")
        self.devices = client.dcim.devices.select(_Device)
        self.device_id = device_id

    async def aload(self) -> None:
        try:
            device = await self.devices.get(self.device_id)
        except SystemConnectionError as e:
            if e.status_code == HTTPStatus.NOT_FOUND:
                return
            raise

        if device.primary_ip4 is None:
            self.empty = True
            self.problems.append(f"{device.name} has no primary IPv4 address: ISE is not changed")
            return

        # ISE matches the source address of a request: the address of the device, not the subnet of its interface
        address = ip_interface(device.primary_ip4.address).ip
        self.add(NetworkDevice(netbox_id=device.id, name=device.name, ip_addresses=(f"{address}/32",)))
