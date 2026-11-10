"""
System module: the data of a device in NetBox

Data: NetboxDeviceRecord. Source: NetboxDeviceSource.
"""

from .evidence import NetboxDeviceRecord
from .rules import NetboxMustHave
from .sources import NetboxDeviceSource

__all__ = ["NetboxDeviceRecord", "NetboxDeviceSource", "NetboxMustHave"]
