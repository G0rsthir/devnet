from pydantic import Field
from pydantic_settings import SettingsConfigDict

from devnet_core.settings import BaseEnvSettings


class AppEnvSettings(BaseEnvSettings):
    model_config = SettingsConfigDict(env_prefix="DEVNET_API_", env_file=".env", extra="ignore")

    # Secret key used to encode and decode access JWT tokens
    ACCESS_JWT_SECRET: str = Field(default="", exclude=True)

    # Secret key used to encode and decode refresh JWT tokens
    REFRESH_JWT_SECRET: str = Field(default="", exclude=True)
