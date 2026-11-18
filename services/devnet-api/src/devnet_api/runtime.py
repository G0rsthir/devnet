from collections.abc import Sequence
from dataclasses import dataclass

from devnet_api.settings import AppEnvSettings
from devnet_config.env import CoreEnvSettings
from devnet_core.const import Environments
from devnet_core.exceptions import ConfigurationError


@dataclass(frozen=True, kw_only=True)
class RuntimeContainer:
    core: CoreEnvSettings
    env: AppEnvSettings


def bootstrap_runtime(enviroment: Environments) -> RuntimeContainer:
    core = CoreEnvSettings(ENVIRONMENT=enviroment)
    env = AppEnvSettings()

    return RuntimeContainer(core=core, env=env)


def validate_server_startup(env: AppEnvSettings, required: Sequence[str] | None = None):
    if not required:
        return

    for name in required:
        if not getattr(env, name):
            raise ConfigurationError(f"DEVNET_API_{name} is not configured. Set this environment variable")
