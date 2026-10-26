from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from devnet_api.const import AccessScope, RefreshScope


class AuthSessionContextBase(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)

    sub: str = Field(alias="sub")
    jti: str | None = Field(default=None, alias="jti")


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
