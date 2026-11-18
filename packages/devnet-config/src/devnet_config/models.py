from typing import Any, Self

import yaml
from cachetools.func import ttl_cache
from pydantic import Field, ValidationError, model_validator
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

# Seconds until get_config reads the files again
CONFIG_TTL = 60


class Systems(ConfigModel):
    netbox: NetboxConfig
    ise: IseConfig | None = None


class Features(ConfigModel):
    ingest: bool = True
    compliance: bool = True
    ise_sync: bool = True
    backups: bool = True
    netbox_webhook: bool = True


class DevnetConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEVNET_", env_nested_delimiter="__", extra="forbid", frozen=True)

    features: Features = Features()

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

    # TODO
    @model_validator(mode="after")
    def _systems_for_features(self) -> Self:
        if self.features.ise_sync and self.systems.ise is None:
            raise ValueError("features.ise_sync is on: add systems.ise, or set ise_sync to false")
        return self


@ttl_cache(maxsize=1, ttl=CONFIG_TTL)
def get_config() -> DevnetConfig:
    """
    Raises:
        ConfigurationError: If a config file can't be read
    """
    try:
        return DevnetConfig()  # pyright: ignore[reportCallIssue]
    except (OSError, yaml.YAMLError, ValidationError, SettingsError) as e:
        raise ConfigurationError(str(e)) from e
