from dataclasses import dataclass
from typing import Self

from compliance.cisco.config_tree import ConfigTree


@dataclass(frozen=True, kw_only=True)
class RunningConfig:
    """
    The running config of one device

    Args:
        network_os: Network OS in the names of netutils, e.g. cisco_xe
    """

    text: str
    network_os: str
    tree: ConfigTree

    @classmethod
    def parse(cls, text: str, *, network_os: str) -> Self:
        """
        Raises:
            LookupError: If there is no parser for the network OS
            ValueError: If the text is empty or cannot be parsed, e.g. the output was cut off
        """
        tree = ConfigTree(text, network_os=network_os)
        if not tree.lines:
            raise ValueError("the config is empty")
        return cls(text=text, network_os=network_os, tree=tree)
