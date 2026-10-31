from devnet_core.connections.client import HttpConfig
from devnet_core.settings import EnvSecret


class IseConfig(HttpConfig):
    name: str = "ise"
    username: EnvSecret
    password: EnvSecret
