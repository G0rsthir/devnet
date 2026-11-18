from pydantic import Field
from pydantic_settings import SettingsConfigDict

from devnet_config.env import BaseEnvSettings
from devnet_core.settings import EnvStrSet


class AppEnvSettings(BaseEnvSettings):
    model_config = SettingsConfigDict(env_prefix="DEVNET_API_")

    # Secret key used to encode and decode access JWT tokens
    ACCESS_JWT_SECRET: str = Field(default="", exclude=True)

    # Secret key used to encode and decode refresh JWT tokens
    REFRESH_JWT_SECRET: str = Field(default="", exclude=True)

    # Tokens to reject before they expire
    REVOKED_JWT_TOKENS: EnvStrSet = Field(default_factory=set)
