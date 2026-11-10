from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, kw_only=True)
class CliTarget:
    """
    What a driver needs to open a session

    Args:
        network_os: Network OS in the names of netutils, e.g. cisco_xe. See compliance.device.platform
    """

    name: str
    host: str
    network_os: str
    port: int = 22


class DeviceCli(Protocol):
    """
    Port: run show commands on a network device

    Each driver (pyATS, scrapli, netmiko) is one adapter: a class with this method.
    Code that needs a device takes a DeviceCli and does not import a driver.
    """

    async def run(self, target: CliTarget, commands: Sequence[str]) -> list[str]:
        """
        Open one session, run the commands in order, close the session

        Returns:
            The output of each command, in the same order

        Raises:
            SystemConnectionError: If the device is unreachable, rejects the login or rejects a command
        """
        ...
