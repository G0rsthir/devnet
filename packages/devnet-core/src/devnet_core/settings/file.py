from pydantic import BaseModel, ConfigDict


class ConfigModel(BaseModel):
    """
    Base for every section of the config file
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
