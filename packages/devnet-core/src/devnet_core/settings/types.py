import json
import os
import re
from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, PlainSerializer, PlainValidator
from pydantic_settings import NoDecode

from devnet_core.exceptions import ConfigurationError

_ENV_REF = re.compile(r"\$\{(\w+)\}")


def json_or_empty_set(value: object) -> object:
    if isinstance(value, str):
        return json.loads(value) if value.strip() else set()
    return value


# Env setting as a JSON list. NoDecode passes the raw string, so a blank one can't fail JSON decoding
type EnvStrSet = Annotated[set[str], NoDecode, BeforeValidator(json_or_empty_set)]


@dataclass(frozen=True, kw_only=True)
class SecretRef:
    """
    A secret from the config file. Holds the variable's name, the value is read only when used
    """

    var: str

    def get_secret_value(self) -> str:
        """
        Raises:
            ConfigurationError: If the environment variable isn't set
        """
        value = os.environ.get(self.var)
        if not value:
            raise ConfigurationError(f"environment variable {self.var} is not set")
        return value


def secret_ref(value: object) -> SecretRef:
    error = ValueError("must be ${VAR}: secrets come from the environment, never from the file")

    if isinstance(value, SecretRef):
        return value

    if not isinstance(value, str):
        raise error

    match = _ENV_REF.fullmatch(value)

    if not match:
        raise error

    return SecretRef(match[1])


# A secret in the config file: written as ${VAR}, read from the environment when used
type EnvSecret = Annotated[SecretRef, PlainValidator(secret_ref), PlainSerializer(lambda ref: f"${{{ref.var}}}")]


def missing_secrets(value: object) -> list[str]:
    """
    Environment variables that aren't set
    """
    if isinstance(value, SecretRef):
        return [] if os.environ.get(value.var) else [value.var]
    if isinstance(value, BaseModel):
        return [var for name in type(value).model_fields for var in missing_secrets(getattr(value, name))]
    if isinstance(value, dict):
        return [var for item in value.values() for var in missing_secrets(item)]
    if isinstance(value, list | tuple):
        return [var for item in value for var in missing_secrets(item)]
    return []
