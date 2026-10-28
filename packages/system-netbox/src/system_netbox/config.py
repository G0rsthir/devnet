from devnet_core.settings.file import ConfigModel
from devnet_core.settings.types import EnvSecret


class NetboxConfig(ConfigModel):
    name: str = "netbox"
    base_url: str
    token: EnvSecret
    verify_tls: bool = True
