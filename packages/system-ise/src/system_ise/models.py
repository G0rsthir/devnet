from dataclasses import dataclass, field

# Copied by hand from schema/generated


@dataclass(kw_only=True)
class ResourceSummary:
    """
    One entry of a list. `get` returns the whole object
    """

    id: str
    name: str
    description: str | None = None


@dataclass(kw_only=True)
class NetworkDeviceGroup:
    id: str
    name: str
    othername: str
    description: str | None = None


@dataclass(kw_only=True)
class NetworkDeviceGroupRequest:
    """
    Args:
        name: Whole path, e.g. Location#All Locations#Site1. ISE creates missing parents
            and answers 500 if a part is over 32 characters
        othername: Top of the path, e.g. Location
    """

    name: str
    othername: str
    description: str | None = None


@dataclass(kw_only=True)
class NetworkDeviceIP:
    """
    Args:
        mask: Prefix length, 32 for one address. A number, although the schema says object
    """

    ipaddress: str
    mask: int = 32


@dataclass(kw_only=True)
class NetworkDevice:
    id: str
    name: str
    description: str | None = None
    NetworkDeviceIPList: list[NetworkDeviceIP] = field(default_factory=list)


@dataclass(kw_only=True)
class NetworkDeviceRequest:
    """
    Args:
        NetworkDeviceIPList: The addresses that ISE accepts RADIUS and TACACS+ requests from
    """

    name: str
    NetworkDeviceIPList: list[NetworkDeviceIP]
    description: str | None = None
