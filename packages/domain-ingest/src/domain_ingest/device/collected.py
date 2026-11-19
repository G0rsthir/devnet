"""
What a collector returns for one device. No vendor terms and no NetBox terms.

A collector returns complete data or raises: the sync treats a missing interface as removed.
"""

import ipaddress
import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field


def _mac_address(value: str) -> str:
    """
    Any common notation -> AA:BB:CC:DD:EE:FF
    """
    digits = re.sub(r"[.:\-]", "", value.strip()).upper()
    if not re.fullmatch(r"[0-9A-F]{12}", digits):
        raise ValueError(f"invalid MAC address: {value}")
    return ":".join(digits[i : i + 2] for i in range(0, 12, 2))


def _ip_interface(value: str) -> str:
    if "/" not in value:
        raise ValueError(f"address needs a prefix length, e.g. 10.0.0.1/24: {value}")
    return str(ipaddress.ip_interface(value.strip()))


type MacAddressStr = Annotated[str, AfterValidator(_mac_address)]
type IPInterfaceStr = Annotated[str, AfterValidator(_ip_interface)]


class CollectedInterface(BaseModel):
    name: str
    # Config intent: no "shutdown"
    admin_up: bool
    oper_up: bool
    description: str = ""
    # e.g. EtherSVI, Gigabit Ethernet
    hardware_type: str | None = None
    # e.g. 10/100/1000BaseTX, SFP-10GBase-SR
    media_type: str | None = None
    mac_address: MacAddressStr | None = None
    mtu: int | None = None
    ipv4: list[IPInterfaceStr] = Field(default_factory=list)
    # NetBox VRF name. None is the global table
    vrf: str | None = None


class CollectedDevice(BaseModel):
    hostname: str
    serial: str
    interfaces: list[CollectedInterface] = Field(default_factory=list)
