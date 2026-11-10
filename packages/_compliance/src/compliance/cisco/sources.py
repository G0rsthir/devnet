from pathlib import Path

import anyio

from compliance.cisco.evidence import RunningConfig
from compliance.core import Device
from compliance.device import CliTarget, DeviceCli, network_os
from devnet_core.const import ENCODING

SHOW_RUNNING_CONFIG = "show running-config"


class CliConfigSource:
    """
    Source adapter: the running config from the device itself

    Args:
        cli: The driver. This class does not know which one
    """

    provides = RunningConfig

    def __init__(self, cli: DeviceCli) -> None:
        self._cli = cli

    async def collect(self, device: Device) -> RunningConfig:
        if not device.primary_ip:
            raise LookupError(f"{device.name} has no primary IP in NetBox")
        target = CliTarget(name=device.name, host=device.primary_ip, network_os=network_os(device.platform))
        (text,) = await self._cli.run(target, [SHOW_RUNNING_CONFIG])
        return RunningConfig.parse(text, network_os=target.network_os)


class FileConfigSource:
    """
    Source adapter: the running config from a file, e.g. a config backup

    No session to the device opens. The file is not checked for its age.

    Args:
        directory: Folder with one file for each device
        pattern: File name of a device. `{name}` is the device name
    """

    provides = RunningConfig

    def __init__(self, directory: Path, *, pattern: str = "{name}.cfg") -> None:
        self._directory = directory.resolve()
        self._pattern = pattern

    async def collect(self, device: Device) -> RunningConfig:
        path = (self._directory / self._pattern.replace("{name}", device.name)).resolve()
        # A device name is data from NetBox. It must not select a file outside the folder
        if not path.is_relative_to(self._directory):
            raise ValueError(f"{device.name} is not a valid file name")
        try:
            text = await anyio.Path(path).read_text(encoding=ENCODING)
        except FileNotFoundError:
            raise LookupError(f"no config file {path.name}") from None
        return RunningConfig.parse(text, network_os=network_os(device.platform))
