from importlib.resources.abc import Traversable

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from devnet_core.const import ENCODING
from devnet_core.exceptions import ConfigurationError


class ConfigModel(BaseModel):
    """
    Base for every section of the config file
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


def load_yaml_model[M: BaseModel](source: Traversable, model: type[M]) -> M:
    """
    Raises:
        ConfigurationError: If the file can't be read or doesn't match the model
    """
    try:
        data = yaml.safe_load(source.read_text(encoding=ENCODING)) or {}
        return model.model_validate(data)
    except (OSError, yaml.YAMLError, ValidationError) as e:
        raise ConfigurationError(f"{source}: {e}") from e
