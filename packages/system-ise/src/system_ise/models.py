from dataclasses import dataclass

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
