from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field, PlainSerializer
from pydantic.json_schema import SkipJsonSchema

from devnet_api.schemas._validation import empty_to_none

# Placeholder sent instead of a stored secret
SECRET_MASK = "******"

MaskedStr = Annotated[str, PlainSerializer(lambda value: SECRET_MASK if value else "", return_type=str)]

# Allows to remove an inherited field from a model
ExcludedField = SkipJsonSchema[Annotated[Any, Field(default=None, exclude=True), AfterValidator(lambda s: None)]]


type OptionalStr = Annotated[str | None, BeforeValidator(empty_to_none)]
