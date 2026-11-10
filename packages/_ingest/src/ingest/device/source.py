from diffsync.enum import DiffSyncModelFlags

from ingest.device.collected import CollectedDevice, CollectedInterface
from ingest.device.interface_type import interface_type, parent_name
from ingest.device.models import Device, Interface, IPAddress, MACAddress
from ingest.sync import SyncAdapter


class CollectedDeviceAdapter(SyncAdapter):
    """
    Source: one device as it reports itself

    Rules about what to import are model flags. DiffSync applies a flag to the object and its children.

    Args:
        name: The device's name in NetBox
        ip_only: Only manage interfaces that have an IPv4 address
    """

    device = Device
    interface = Interface
    ip_address = IPAddress
    mac_address = MACAddress

    top_level = ["device"]

    def __init__(self, collected: CollectedDevice, *, name: str, ip_only: bool = False) -> None:
        super().__init__(name=f"device {name}")
        self.collected = collected
        self.device_name = name
        self.ip_only = ip_only

    def _flags(self, state: CollectedInterface) -> DiffSyncModelFlags:
        if self.ip_only and not state.ipv4:
            # Out of scope: no create, no update, no delete
            return DiffSyncModelFlags.IGNORE
        if not (state.admin_up and state.oper_up):
            # A down interface isn't created. If NetBox has it already, it's updated
            return DiffSyncModelFlags.SKIP_UNMATCHED_SRC
        return DiffSyncModelFlags.NONE

    async def aload(self) -> None:
        device = Device(name=self.device_name, serial=self.collected.serial)
        self.add(device)
        self.empty = not self.collected.interfaces

        flags = {state.name: self._flags(state) for state in self.collected.interfaces}
        for state in self.collected.interfaces:
            parent = parent_name(state.name)
            # Only link to a parent that this run manages
            if parent is not None and flags.get(parent, DiffSyncModelFlags.IGNORE) & DiffSyncModelFlags.IGNORE:
                parent = None

            interface = Interface(
                device=device.name,
                name=state.name,
                type=interface_type(state.name, hardware_type=state.hardware_type, media_type=state.media_type),
                enabled=state.admin_up,
                description=state.description,
                mtu=state.mtu,
                parent=parent,
                model_flags=flags[state.name],
            )
            self.add(interface)
            device.add_child(interface)

            for address in state.ipv4:
                ip_address = IPAddress(
                    device=device.name,
                    interface=state.name,
                    address=address,
                    vrf=state.vrf,
                    description=state.description,
                )
                self.add(ip_address)
                interface.add_child(ip_address)

            # A subinterface reports its parent's MAC address. NetBox assigns a MAC address to one interface
            if state.mac_address and parent_name(state.name) is None:
                mac_address = MACAddress(device=device.name, interface=state.name, mac=state.mac_address, primary=True)
                self.add(mac_address)
                interface.add_child(mac_address)
