from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, kw_only=True)
class NetboxDeviceRecord:
    """
    The device as the NetBox REST API returns it, with its config context

    Args:
        data: The JSON object of `/api/dcim/devices/{id}/`
    """

    data: Mapping[str, Any]

    def value(self, path: str) -> Any:
        """
        A field by its path, e.g. `serial`, `tenant.slug`, `custom_fields.owner`, `config_context.ntp_servers`

        Returns:
            None if a part of the path is missing
        """
        current: Any = self.data
        for part in path.split("."):
            if not isinstance(current, Mapping):
                return None
            current = current.get(part)
        return current


def is_empty(value: Any) -> bool:
    """
    True for the values that NetBox returns for a field that is not set
    """
    return value is None or value == "" or value == [] or value == {}
