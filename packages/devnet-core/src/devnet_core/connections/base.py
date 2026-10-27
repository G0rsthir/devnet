from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, kw_only=True)
class ConnectivityInfo:
    version: str | None = None


class Connector(Protocol):
    """
    Capability shared by every client
    """

    async def check_connectivity(self) -> ConnectivityInfo:
        """
        Authenticate and perform a lightweight request

        Raises:
            SystemConnectionError: If the system is unreachable or rejects the request
        """
        ...
