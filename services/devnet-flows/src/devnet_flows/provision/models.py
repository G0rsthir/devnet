from pydantic import Field

from devnet_core.settings import ConfigModel
from devnet_flows.config.models import get_config


class PrefectProvision(ConfigModel):
    # tag -> max concurrent task runs
    concurrency_limits: dict[str, int] = Field(default_factory=dict)


# TODO move?
class NetboxProvision(ConfigModel):
    # devnet-api endpoint that NetBox sends device changes to
    webhook_url: str
    # webhook_token: EnvSecret
    webhook_verify_tls: bool = True


class ProvisionConfig(ConfigModel):
    prefect: PrefectProvision = PrefectProvision()
    netbox: NetboxProvision | None = None


def provision_config() -> ProvisionConfig:
    """
    Raises:
        ConfigurationError: If the provision section is invalid or its secrets aren't set
    """
    try:
        return ProvisionConfig.model_validate(get_config().provision)
    except ValidationError as e:
        raise ConfigurationError(f"provision: {e}") from e
