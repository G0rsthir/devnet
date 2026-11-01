from functools import cache
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import Field, ValidationError
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    SettingsError,
    YamlConfigSettingsSource,
)

from devnet_config.env import CoreEnvSettings
from devnet_core.const import ENCODING
from devnet_core.exceptions import ConfigurationError
from devnet_core.settings import ConfigModel
from system_ise.config import IseConfig
from system_netbox.config import NetboxConfig


class Systems(ConfigModel):
    netbox: NetboxConfig
    ise: IseConfig


class DevnetConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEVNET_", env_nested_delimiter="__", extra="forbid", frozen=True)

    systems: Systems

    provision: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_settings = YamlConfigSettingsSource(
            settings_cls,
            yaml_file=[CoreEnvSettings().CONFIG],
            yaml_file_encoding=ENCODING,
            deep_merge=True,
        )
        return init_settings, env_settings, yaml_settings


@cache
def get_config() -> DevnetConfig:
    """
    Raises:
        ConfigurationError: If a config file can't be read
    """
    # EnvSecret reads os.environ
    load_dotenv(".env")
    try:
        return DevnetConfig()
    except (OSError, yaml.YAMLError, ValidationError, SettingsError) as e:
        raise ConfigurationError(str(e)) from e
