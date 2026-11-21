from devnet_config import get_config
from devnet_core.exceptions import ConfigurationError
from system_ise.client import IseClient
from system_netbox.client import NetboxClient


def netbox() -> NetboxClient:
    return NetboxClient(get_config().systems.netbox)


def ise() -> IseClient:
    """
    Raises:
        ConfigurationError: If devnet.yaml has no system
    """
    config = get_config().systems.ise
    if config is None:
        raise ConfigurationError("systems.ise is not configured")
    return IseClient(config)
