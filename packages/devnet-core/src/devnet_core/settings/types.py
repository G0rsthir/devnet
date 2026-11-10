import json
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    PlainValidator,
    SecretStr,
    ValidationError,
    create_model,
)
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict, SettingsError

from devnet_core.const import ENCODING
from devnet_core.exceptions import ConfigurationError

_ENV_REF = re.compile(r"\$\{(\w+)\}")

# Where Docker mounts secrets
_DOCKER_SECRETS = Path("/run/secrets")


def json_or_empty_set(value: object) -> object:
    if isinstance(value, str):
        return json.loads(value) if value.strip() else set()
    return value


# Env setting as a JSON list. NoDecode passes the raw string, so a blank one can't fail JSON decoding
type EnvStrSet = Annotated[set[str], NoDecode, BeforeValidator(json_or_empty_set)]


class SecretSettings(BaseSettings):
    """
    Any setting: environment, .env, then Docker secrets
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding=ENCODING,
        env_ignore_empty=True,
        secrets_dir=_DOCKER_SECRETS if _DOCKER_SECRETS.is_dir() else None,
        extra="ignore",
        # A validation error would show the secret
        hide_input_in_errors=True,
    )

    value: SecretStr | None = None


@cache
def _secret_settings(var: str) -> type[SecretSettings]:
    """
    SecretSettings that looks its value up as var
    """
    return create_model(
        "SecretSettings",
        __base__=SecretSettings,
        value=(SecretStr | None, Field(default=None, validation_alias=var)),
    )


@dataclass(frozen=True, kw_only=True)
class SecretRef:
    var: str

    def get_secret_value(self) -> str:
        """
        Raises:
            ConfigurationError: If no source has the secret, or one can't be read
        """
        try:
            secret = _secret_settings(self.var)().value
        except (OSError, SettingsError, ValidationError) as e:
            raise ConfigurationError(f"secret {self.var} can't be read: {e}") from e
        if secret is None or not secret.get_secret_value():
            raise ConfigurationError(f"secret {self.var} is not set")
        return secret.get_secret_value()


def secret_ref(value: object) -> SecretRef:
    error = ValueError("must be ${VAR}: secrets come from the environment, never from the file")

    if isinstance(value, SecretRef):
        return value

    if not isinstance(value, str):
        raise error

    match = _ENV_REF.fullmatch(value)

    if not match:
        raise error

    return SecretRef(var=match[1])


# A secret in the config file: written as ${VAR}, read from the environment when used
type EnvSecret = Annotated[SecretRef, PlainValidator(secret_ref), PlainSerializer(lambda ref: f"${{{ref.var}}}")]


# TODO add?
def missing_secrets(value: object) -> list[str]:
    """
    Variables of the secrets that can't be read
    """
    if isinstance(value, SecretRef):
        try:
            value.get_secret_value()
        except ConfigurationError:
            return [value.var]
        return []
    if isinstance(value, BaseModel):
        return [var for name in type(value).model_fields for var in missing_secrets(getattr(value, name))]
    if isinstance(value, dict):
        return [var for item in value.values() for var in missing_secrets(item)]
    if isinstance(value, list | tuple):
        return [var for item in value for var in missing_secrets(item)]
    return []
