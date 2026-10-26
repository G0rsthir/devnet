from datetime import datetime

from fastapi.encoders import jsonable_encoder

from devnet_api.const import AccessScope, RefreshScope
from devnet_api.schemas.security import AccessSessionContext, RefreshSessionContext
from devnet_api.security.manager import AuthManager


class AuthTokenService:
    def __init__(
        self,
        access_manager: AuthManager,
        refresh_manager: AuthManager,
    ):
        self.access_manager = access_manager
        self.refresh_manager = refresh_manager
        self.refresh_cookie_name = refresh_manager.cookie_name
        self.token_url = refresh_manager.token_url

    def issue_access_token(
        self,
        *,
        sub: str,
        expires_at: datetime,
        scopes: list[AccessScope] | None = None,
    ) -> str:

        access_ctx = AccessSessionContext(
            sub=sub,
            scopes=scopes,
        )

        return self.access_manager.create_access_token(
            data=jsonable_encoder(access_ctx.model_dump(exclude_none=True, exclude_defaults=True)),
            expires_at=expires_at,
        )

    def issue_refresh_token(self, *, sub: str, expires_at: datetime) -> str:

        refresh_ctx = RefreshSessionContext(sub=sub, scopes=[RefreshScope.TOKEN_REFRESH])

        return self.refresh_manager.create_access_token(
            data=jsonable_encoder(refresh_ctx.model_dump(exclude_none=True, exclude_defaults=True)),
            expires_at=expires_at,
        )
