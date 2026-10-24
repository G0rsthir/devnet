from pydantic import (
    BaseModel,
    ConfigDict,
)

from devnet_api.const import AccessScope, RefreshScope


class AuthSessionContextBase(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)


class AccessSessionContext(AuthSessionContextBase):
    """
    Stores data about active (current) access session.
    """

    scopes: list[AccessScope] | None = None


class RefreshSessionContext(AuthSessionContextBase):
    """
    Stores data about active (current) refresh session.
    """

    scopes: list[RefreshScope] | None = None
