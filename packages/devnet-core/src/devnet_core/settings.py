from pydantic_settings import BaseSettings, SettingsConfigDict

from devnet_core.const import ENCODING, Environments


class BaseEnvSettings(BaseSettings):
    """
    Base settings class for environment-specific settings
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding=ENCODING)


class CoreEnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: Environments = Environments.DEVELOPMENT
