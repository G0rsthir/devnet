from typing import Final

# NetBox platform slug -> network OS. The names are those of netutils and netmiko, so
# netutils.lib_mapper gives the name that each driver uses (pyATS: iosxe, scrapli: cisco_iosxe)
PLATFORMS: Final = {
    "ios": "cisco_ios",
    "cisco-ios": "cisco_ios",
    "iosxe": "cisco_xe",
    "ios-xe": "cisco_xe",
    "cisco-iosxe": "cisco_xe",
    "iosxr": "cisco_xr",
    "ios-xr": "cisco_xr",
    "nxos": "cisco_nxos",
    "nx-os": "cisco_nxos",
    "asa": "cisco_asa",
}


def network_os(platform: str | None) -> str:
    """
    Raises:
        LookupError: If the NetBox platform has no network OS
    """
    try:
        return PLATFORMS[platform or ""]
    except KeyError:
        raise LookupError(f"NetBox platform {platform!r} has no network OS in PLATFORMS") from None
