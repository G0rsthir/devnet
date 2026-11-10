"""
System module: the config of a Cisco device

Data: RunningConfig. Sources: from the device (CliConfigSource), from a file (FileConfigSource).
"""

from .config_tree import ConfigLine, ConfigTree
from .evidence import RunningConfig
from .rules import ConfigMustContain, ConfigMustNotMatch, VrfHasImportMap
from .sources import CliConfigSource, FileConfigSource

__all__ = [
    "CliConfigSource",
    "ConfigLine",
    "ConfigMustContain",
    "ConfigMustNotMatch",
    "ConfigTree",
    "FileConfigSource",
    "RunningConfig",
    "VrfHasImportMap",
]
