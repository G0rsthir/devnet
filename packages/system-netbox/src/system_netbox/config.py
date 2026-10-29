from devnet_core.connections.client import HttpConfig
from devnet_core.settings import EnvSecret


class NetboxConfig(HttpConfig):
    name: str = "netbox"
    token: EnvSecret
