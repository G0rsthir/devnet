"""
Device import: a network device's serial, interfaces, IP addresses and MAC addresses -> NetBox
"""

from .collected import CollectedDevice, CollectedInterface
from .job import import_device

__all__ = ["CollectedDevice", "CollectedInterface", "import_device"]
