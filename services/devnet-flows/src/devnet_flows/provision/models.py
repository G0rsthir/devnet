from pydantic import Field, ValidationError

from devnet_config import get_config
from devnet_core.exceptions import ConfigurationError
from devnet_core.settings import ConfigModel


class PrefectProvision(ConfigModel):
    # tag -> max concurrent task runs
    concurrency_limits: dict[str, int] = Field(default_factory=dict)


class ProvisionConfig(ConfigModel):
    prefect: PrefectProvision = PrefectProvision()


def provision_config() -> ProvisionConfig:
    """
    Raises:
        ConfigurationError: If the provision section is invalid or its secrets aren't set
    """
    try:
        return ProvisionConfig.model_validate(get_config().provision)
    except ValidationError as e:
        raise ConfigurationError(f"provision: {e}") from e
