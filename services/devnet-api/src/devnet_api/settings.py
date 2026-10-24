from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

from devnet_core.settings import BaseEnvSettings


class AppEnvSettings(BaseEnvSettings):
    model_config = SettingsConfigDict(env_prefix="DEVNET_API_", env_file=".env", extra="ignore")

    ACCESS_JWT_SECRET: SecretStr
    REFRESH_JWT_SECRET: SecretStr
