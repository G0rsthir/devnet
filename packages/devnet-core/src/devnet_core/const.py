from enum import Enum, StrEnum
from typing import Final

ENCODING: Final = "utf-8"


class UnsetEnum(Enum):
    UNSET = "UNSET"


UNSET = UnsetEnum.UNSET


class Environments(StrEnum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"
