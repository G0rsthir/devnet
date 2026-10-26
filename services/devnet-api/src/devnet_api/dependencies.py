from typing import Annotated

from fastapi import Depends, Request, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

from devnet_api.const import AccessScope, RefreshScope
from devnet_api.security.loader import AUTH_TOKEN_URL
from devnet_api.services.token import AuthTokenService

from .schemas.security import AccessSessionContext, RefreshSessionContext
from .security.manager import AuthManager


class AccessManagerDependency(OAuth2PasswordBearer):
    def __init__(self):
        super().__init__(tokenUrl=AUTH_TOKEN_URL, auto_error=False)
        self.permissions = {}

    async def __call__(self, request: Request, scopes: SecurityScopes) -> AccessSessionContext:  # type: ignore
        manager: AuthManager[AccessSessionContext] = request.app.state.access_manager
        return await manager(request=request, security_scopes=scopes)


class RefreshManagerDependency(OAuth2PasswordBearer):
    def __init__(self):
        super().__init__(tokenUrl=AUTH_TOKEN_URL, auto_error=False)

    async def __call__(self, request: Request, scopes: SecurityScopes) -> RefreshSessionContext:  # type: ignore
        manager: AuthManager[RefreshSessionContext] = request.app.state.refresh_manager
        return await manager(request=request, security_scopes=scopes)


_access_manager_dependency = AccessManagerDependency()

_refresh_manager_dependency = RefreshManagerDependency()


def AccessSecurity(*, scopes: list[AccessScope] | None = None):
    return Security(_access_manager_dependency, scopes=scopes)


def RefreshSecurity(*, scopes: list[RefreshScope] | None = None):
    return Security(_refresh_manager_dependency, scopes=scopes)


def get_token_service(request: Request) -> AuthTokenService:
    return AuthTokenService(
        access_manager=request.app.state.access_manager,
        refresh_manager=request.app.state.refresh_manager,
    )


TokenServiceDependency = Annotated[AuthTokenService, Depends(get_token_service)]
