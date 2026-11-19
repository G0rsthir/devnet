from __future__ import annotations

from dataclasses import asdict
from ipaddress import ip_interface
from typing import Any, cast

from devnet_core.exceptions import DataIntegrityError
from devnet_core.sync import RemoteModel, SyncAdapter
from domain_ingest.ise.models import NetworkDevice
from system_ise.client import IseClient
from system_ise.models import NetworkDeviceIP, NetworkDeviceRequest


def description(netbox_id: int) -> str:
    """
    The description of an ISE device that devnet manages. The sync searches ISE for it
    """
    return f"NetBox device {netbox_id}"


def _ip_list(ip_addresses: tuple[str, ...]) -> list[NetworkDeviceIP]:
    interfaces = [ip_interface(address) for address in ip_addresses]
    return [NetworkDeviceIP(ipaddress=str(i.ip), mask=i.network.prefixlen) for i in interfaces]


class IseNetworkDevice(RemoteModel, NetworkDevice):
    # ISE ID. Not in _attributes, so DiffSync doesn't compare it
    pk: str | None = None

    @property
    def ise(self) -> IseDeviceTarget:
        return cast(IseDeviceTarget, self.adapter)

    @property
    def id(self) -> str:
        if self.pk is None:
            raise LookupError(f"{self.get_type()} {self.get_unique_id()} has no ISE ID")
        return self.pk

    async def acreate(self) -> None:
        request = NetworkDeviceRequest(
            name=self.name,
            description=description(self.netbox_id),
            NetworkDeviceIPList=_ip_list(self.ip_addresses),
        )
        self.pk = (await self.ise.devices.create(request)).id

    async def aupdate(self, attrs: dict[str, Any]) -> None:
        payload: dict[str, Any] = {}
        if "name" in attrs:
            payload["name"] = attrs["name"]
        if "ip_addresses" in attrs:
            payload["NetworkDeviceIPList"] = [asdict(ip) for ip in _ip_list(attrs["ip_addresses"])]
        await self.ise.devices.update(self.id, payload)

    async def adelete(self) -> None:
        await self.ise.devices.delete(self.id)


class IseDeviceTarget(SyncAdapter):
    """
    Target: the ISE network device of one NetBox device, found by the NetBox ID in its description
    """

    network_device = IseNetworkDevice

    top_level = ["network_device"]

    def __init__(self, client: IseClient, *, netbox_id: int) -> None:
        super().__init__(name="ise")
        self.devices = client.network.devices
        self.netbox_id = netbox_id

    async def aload(self) -> None:
        found = await self.devices.find(description=description(self.netbox_id))
        if len(found) > 1:
            names = ", ".join(sorted(device.name for device in found))
            raise DataIntegrityError(f"ISE has {len(found)} devices for NetBox device {self.netbox_id}: {names}")

        for summary in found:
            device = await self.devices.get(summary.id)
            ip_addresses = tuple(sorted(f"{ip.ipaddress}/{ip.mask}" for ip in device.NetworkDeviceIPList))
            self.add(
                IseNetworkDevice(netbox_id=self.netbox_id, name=device.name, ip_addresses=ip_addresses, pk=device.id)
            )
