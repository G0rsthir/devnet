from importlib.resources import files

from pydantic_settings import SettingsConfigDict

from devnet_core.settings import BaseEnvSettings, ConfigModel, load_yaml_model
from system_netbox.config import NetboxConfig


class Systems(ConfigModel):
    # One field per system package
    netbox: NetboxConfig


class DevnetConfig(ConfigModel):
    systems: Systems
    # compliance: ComplianceConfig


class FlowsEnvSettings(BaseEnvSettings):
    model_config = SettingsConfigDict(env_prefix="DEVNET_FLOWS_")

    # Which file in devnet_flows/config/ to load
    CONFIG: Literal["dev", "e2e", "prod"] = "dev"


@cache
def get_config() -> DevnetConfig:
    name = FlowsEnvSettings().CONFIG
    return load_yaml_model(files("devnet_flows") / "config" / f"{name}.yaml", DevnetConfig)
