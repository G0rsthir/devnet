"""
Access to network devices: the DeviceCli port and its adapters

This folder imports nothing from the rest of `compliance`. The ingest collector needs the same port.
"""

from .cli import CliTarget, DeviceCli
from .platform import network_os

__all__ = ["CliTarget", "DeviceCli", "network_os"]
