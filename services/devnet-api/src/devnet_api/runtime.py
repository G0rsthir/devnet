from dataclasses import dataclass

from devnet_api.settings import AppEnvSettings
from devnet_core.const import Environments
from devnet_core.exceptions import ConfigurationError
from devnet_core.settings import CoreEnvSettings


@dataclass(frozen=True, kw_only=True)
class RuntimeContainer:
    core: CoreEnvSettings
    env: AppEnvSettings


def bootstrap_runtime(enviroment: Environments = Environments.DEVELOPMENT) -> RuntimeContainer:
    core = CoreEnvSettings(ENVIRONMENT=enviroment)
    env = AppEnvSettings()

    return RuntimeContainer(core=core, env=env)


def validate_server_startup(env: AppEnvSettings):
    if not env.ACCESS_JWT_SECRET:
        raise ConfigurationError("DEVNET_API_ACCESS_JWT_SECRET is not configured. Set this environment variable")
    if not env.REFRESH_JWT_SECRET:
        raise ConfigurationError("DEVNET_API_REFRESH_JWT_SECRET is not configured. Set this environment variable")
