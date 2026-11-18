from pathlib import Path

from pydantic import Field, FilePath
from pydantic_settings import BaseSettings, SettingsConfigDict

from devnet_core.const import ENCODING, Environments


class BaseEnvSettings(BaseSettings):
    """
    Base settings class for environment-specific settings
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding=ENCODING, extra="ignore")


class CoreEnvSettings(BaseEnvSettings):
    model_config = SettingsConfigDict(env_prefix="DEVNET_")

    ENVIRONMENT: Environments = Environments.DEVELOPMENT

    # The DSN of the Sentry project that gets the errors, traces
    # Empty turns Sentry off
    SENTRY_DSN: str = ""

    # The share of the requests and the task runs that Sentry traces, from 0 to 1
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=1.0, ge=0, le=1)

    # The share of the processes that Sentry profiles while they trace, from 0 to 1
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=1.0, ge=0, le=1)

    CONFIG: FilePath = Path("devnet.yaml")
