import json
from typing import Annotated

from pydantic import BeforeValidator
from pydantic_settings import NoDecode


def json_or_empty_set(value: object) -> object:
    if isinstance(value, str):
        return json.loads(value) if value.strip() else set()
    return value


# Env setting as a JSON list. NoDecode passes the raw string, so a blank one can't fail JSON decoding
type EnvStrSet = Annotated[set[str], NoDecode, BeforeValidator(json_or_empty_set)]
