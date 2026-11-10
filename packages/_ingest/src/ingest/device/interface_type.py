"""
NetBox interface type from what the device reports. Best effort: the answer is `other` if nothing matches.
"""

_MEDIA_TYPES = {
    "zx": "1000base-zx",
    "sx": "1000base-sx",
    "lx": "1000base-lx",
}
_VIRTUAL_HARDWARE = ("ethersvi", "loopback", "tunnel", "vlan", "virtual")
_VIRTUAL_NAMES = ("loopback", "tunnel", "vlan", "nve", "bdi")
_LAG_NAMES = ("port-channel", "bundle-ether")


def parent_name(name: str) -> str | None:
    """
    Cisco subinterfaces are <parent>.<unit>, e.g. GigabitEthernet0/0.100
    """
    return name.rsplit(".", 1)[0] if "." in name else None


def interface_type(name: str, *, hardware_type: str | None = None, media_type: str | None = None) -> str:
    # NetBox lets only a virtual interface have a parent
    if parent_name(name):
        return "virtual"

    media = (media_type or "").lower()
    if media in _MEDIA_TYPES:
        return _MEDIA_TYPES[media]

    hardware = (hardware_type or "").lower()
    if any(word in hardware for word in _VIRTUAL_HARDWARE):
        return "virtual"
    # GEChannel, EtherChannel, Port-channel
    if "channel" in hardware:
        return "lag"

    lowered = name.lower()
    if lowered.startswith(_VIRTUAL_NAMES):
        return "virtual"
    if lowered.startswith(_LAG_NAMES):
        return "lag"
    return "other"
