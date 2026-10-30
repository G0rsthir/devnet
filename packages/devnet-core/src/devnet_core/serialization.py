from functools import cache
from typing import Any

from pydantic import TypeAdapter


@cache
def cached_type_adapter(model: Any) -> TypeAdapter[Any]:
    """
    One validator per type
    """
    return TypeAdapter(model)
