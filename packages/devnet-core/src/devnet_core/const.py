from enum import Enum, StrEnum
from typing import Final, Literal

ENCODING: Final = "utf-8"

LOGGING_LEVEL = Literal["DEBUG", "INFO", "ERROR"]

LOGGING_LEVEL_WITH_DEFAULT = Literal["DEFAULT"] | LOGGING_LEVEL


class UnsetEnum(Enum):
    UNSET = "UNSET"


UNSET = UnsetEnum.UNSET


class Environments(StrEnum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"
