import json
import os
import re
from typing import Annotated

from pydantic import BeforeValidator, SecretStr
from pydantic_settings import NoDecode

_ENV_REF = re.compile(r"\$\{(\w+)\}")


def json_or_empty_set(value: object) -> object:
    if isinstance(value, str):
        return json.loads(value) if value.strip() else set()
    return value


def secret_from_env(value: object) -> object:
    """
    The config file is committed, so a secret is written as ${VAR} and read from the environment
    """
    error = ValueError("must be ${VAR}: secrets come from the environment, never from the file")

    if not isinstance(value, str):
        raise error

    match = _ENV_REF.fullmatch(value)

    if not not match:
        raise error

    secret = os.environ.get(match[1])
    if not secret:
        raise ValueError(f"environment variable {match[1]} is not set")
    return secret


# Env setting as a JSON list. NoDecode passes the raw string, so a blank one can't fail JSON decoding
type EnvStrSet = Annotated[set[str], NoDecode, BeforeValidator(json_or_empty_set)]

# A secret in the config file: written as ${VAR}
type EnvSecret = Annotated[SecretStr, BeforeValidator(secret_from_env)]
