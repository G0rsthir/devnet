from __future__ import annotations

import asyncio
from typing import Any, cast

from diffsync.enum import DiffSyncModelFlags
from pydantic import BaseModel

from ingest.device.models import Device, Interface, IPAddress, MACAddress
from ingest.sync import RemoteModel, SyncAdapter
from system_netbox.client import NetboxClient
from system_netbox.endpoints import Endpoint
from system_netbox.models.generated import (
    MACAddressRequest,
    VRFRequest,
    WritableDeviceRequest,
    WritableInterfaceRequest,
    WritableIPAddressRequest,
)

DEVICE_INTERFACE = "dcim.interface"

# Interface custom field. False opts the interface out of the import
SYNC_ENABLED = "sync_enabled"


# What this feature reads from NetBox. A list request asks for these fields only: the full
# interface serializer is slow, and a NetBox upgrade can't break fields that aren't read


class _Ref(BaseModel):
    id: int
    name: str = ""


class _Choice(BaseModel):
    value: str


class _Device(BaseModel):
    id: int
    name: str
    serial: str = ""


class _Interface(BaseModel):
    id: int
    name: str
    type: _Choice
    enabled: bool = True
    description: str = ""
    mtu: int | None = None
    parent: _Ref | None = None
    primary_mac_address: _Ref | None = None
    custom_fields: dict[str, Any] = {}


class _IPAddress(BaseModel):
    id: int
    address: str
    vrf: _Ref | None = None
    status: _Choice
    description: str = ""
    assigned_object_type: str | None = None
    assigned_object_id: int | None = None


class _MACAddress(BaseModel):
    id: int
    mac_address: str
    assigned_object_type: str | None = None
    assigned_object_id: int | None = None


class _Vrf(BaseModel):
    id: int
    name: str


def _fields(model: type[BaseModel]) -> str:
    return ",".join(model.model_fields)


class _Api:
    """
    The NetBox endpoints of this feature. Their place is system_netbox, as client.dcim and client.ipam
    """

    def __init__(self, client: NetboxClient) -> None:
        self.devices = Endpoint(client, "/api/dcim/devices/", _Device, WritableDeviceRequest)
        self.interfaces = Endpoint(client, "/api/dcim/interfaces/", _Interface, WritableInterfaceRequest)
        self.ip_addresses = Endpoint(client, "/api/ipam/ip-addresses/", _IPAddress, WritableIPAddressRequest)
        self.mac_addresses = Endpoint(client, "/api/dcim/mac-addresses/", _MACAddress, MACAddressRequest)
        self.vrfs = Endpoint(client, "/api/ipam/vrfs/", _Vrf, VRFRequest)


class _NetboxModel(RemoteModel):
    # NetBox ID. Not in _attributes, so DiffSync doesn't compare it
    pk: int | None = None

    @property
    def nb(self) -> NetboxDeviceAdapter:
        return cast(NetboxDeviceAdapter, self.adapter)

    @property
    def id(self) -> int:
        if self.pk is None:
            raise LookupError(f"{self.get_type()} {self.get_unique_id()} has no NetBox ID")
        return self.pk


class NetboxDevice(_NetboxModel, Device):
    # devnet doesn't create or delete devices: acreate and adelete stay unsupported

    async def aupdate(self, attrs: dict[str, Any]) -> None:
        await self.nb.api.devices.update(self.id, attrs)


class NetboxInterface(_NetboxModel, Interface):
    def _parent_id(self, parent: str | None) -> int | None:
        return self.nb.interface_id(parent) if parent else None

    async def acreate(self) -> None:
        request = WritableInterfaceRequest(
            device=self.nb.device_id,
            name=self.name,
            type=self.type,  # type: ignore[arg-type]
            enabled=self.enabled,
            description=self.description,
            mtu=self.mtu,
            parent=self._parent_id(self.parent),
        )
        self.pk = (await self.nb.api.interfaces.create(request)).id

    async def aupdate(self, attrs: dict[str, Any]) -> None:
        payload = dict(attrs)
        if "parent" in payload:
            payload["parent"] = self._parent_id(payload["parent"])
        await self.nb.api.interfaces.update(self.id, payload)

    async def adelete(self) -> None:
        await self.nb.api.interfaces.delete(self.id)


class NetboxIPAddress(_NetboxModel, IPAddress):
    async def acreate(self) -> None:
        request = WritableIPAddressRequest(
            address=self.address,
            vrf=self.nb.vrf_id(self.vrf),
            status=self.status,  # type: ignore[arg-type]
            description=self.description,
            # Set at creation only. It isn't an attribute, so a role that a person sets in NetBox stays
            role="loopback" if self.interface.lower().startswith("loopback") else None,
            assigned_object_type=DEVICE_INTERFACE,
            assigned_object_id=self.nb.interface_id(self.interface),
        )
        self.pk = (await self.nb.api.ip_addresses.create(request)).id

    async def aupdate(self, attrs: dict[str, Any]) -> None:
        await self.nb.api.ip_addresses.update(self.id, attrs)

    async def adelete(self) -> None:
        await self.nb.api.ip_addresses.delete(self.id)


class NetboxMACAddress(_NetboxModel, MACAddress):
    async def _set_primary(self, primary: bool) -> None:
        interface_id = self.nb.interface_id(self.interface)
        await self.nb.api.interfaces.update(interface_id, {"primary_mac_address": self.id if primary else None})

    async def acreate(self) -> None:
        request = MACAddressRequest(
            mac_address=self.mac,
            assigned_object_type=DEVICE_INTERFACE,
            assigned_object_id=self.nb.interface_id(self.interface),
        )
        self.pk = (await self.nb.api.mac_addresses.create(request)).id
        if self.primary:
            await self._set_primary(True)

    async def aupdate(self, attrs: dict[str, Any]) -> None:
        await self._set_primary(attrs["primary"])

    async def adelete(self) -> None:
        await self.nb.api.mac_addresses.delete(self.id)


class NetboxDeviceAdapter(SyncAdapter):
    """
    Target: one NetBox device with its interfaces, IP addresses and MAC addresses

    Models use names, NetBox uses IDs. The adapter keeps the IDs and resolves a name when a model writes.
    """

    device = NetboxDevice
    interface = NetboxInterface
    ip_address = NetboxIPAddress
    mac_address = NetboxMACAddress

    top_level = ["device"]

    def __init__(self, client: NetboxClient, *, device_id: int) -> None:
        super().__init__(name="netbox")
        self.api = _Api(client)
        self.device_id = device_id
        self.device_name = ""
        self._vrf_ids: dict[str, int] = {}

    def interface_id(self, name: str) -> int:
        interface = self.get_or_none(NetboxInterface, {"device": self.device_name, "name": name})
        if interface is None:
            raise LookupError(f"interface {name} is not in NetBox")
        return cast(NetboxInterface, interface).id

    def vrf_id(self, name: str | None) -> int | None:
        if name is None:
            return None
        if name not in self._vrf_ids:
            raise LookupError(f"VRF {name} is not in NetBox")
        return self._vrf_ids[name]

    async def aload(self) -> None:
        device_id = str(self.device_id)
        nb_device, nb_interfaces, nb_ip_addresses, nb_mac_addresses, nb_vrfs = await asyncio.gather(
            self.api.devices.get(self.device_id),
            self.api.interfaces.find(device_id=device_id, fields=_fields(_Interface)),
            self.api.ip_addresses.find(device_id=device_id, fields=_fields(_IPAddress)),
            self.api.mac_addresses.find(device_id=device_id, fields=_fields(_MACAddress)),
            self.api.vrfs.find(fields=_fields(_Vrf)),
        )
        self._vrf_ids = {vrf.name: vrf.id for vrf in nb_vrfs}
        self.device_name = nb_device.name

        device = NetboxDevice(name=nb_device.name, serial=nb_device.serial, pk=nb_device.id)
        self.add(device)

        interfaces: dict[int, NetboxInterface] = {}
        primary_mac_ids: set[int] = set()
        for nb_interface in nb_interfaces:
            # Delete the IP and MAC addresses of an interface before the interface
            flags = DiffSyncModelFlags.NATURAL_DELETION_ORDER
            if nb_interface.custom_fields.get(SYNC_ENABLED) is False:
                flags |= DiffSyncModelFlags.IGNORE
            interface = NetboxInterface(
                device=device.name,
                name=nb_interface.name,
                type=nb_interface.type.value,
                enabled=nb_interface.enabled,
                description=nb_interface.description,
                mtu=nb_interface.mtu,
                parent=nb_interface.parent.name if nb_interface.parent else None,
                pk=nb_interface.id,
                model_flags=flags,
            )
            self.add(interface)
            device.add_child(interface)
            interfaces[nb_interface.id] = interface
            if nb_interface.primary_mac_address:
                primary_mac_ids.add(nb_interface.primary_mac_address.id)

        for nb_ip_address in nb_ip_addresses:
            owner = interfaces.get(nb_ip_address.assigned_object_id or 0)
            if owner is None or nb_ip_address.assigned_object_type != DEVICE_INTERFACE:
                continue
            ip_address = NetboxIPAddress(
                device=device.name,
                interface=owner.name,
                address=nb_ip_address.address,
                vrf=nb_ip_address.vrf.name if nb_ip_address.vrf else None,
                status=nb_ip_address.status.value,
                description=nb_ip_address.description,
                pk=nb_ip_address.id,
            )
            self.add(ip_address)
            owner.add_child(ip_address)

        for nb_mac_address in nb_mac_addresses:
            owner = interfaces.get(nb_mac_address.assigned_object_id or 0)
            if owner is None or nb_mac_address.assigned_object_type != DEVICE_INTERFACE:
                continue
            mac_address = NetboxMACAddress(
                device=device.name,
                interface=owner.name,
                mac=nb_mac_address.mac_address.upper(),
                primary=nb_mac_address.id in primary_mac_ids,
                pk=nb_mac_address.id,
            )
            self.add(mac_address)
            owner.add_child(mac_address)
