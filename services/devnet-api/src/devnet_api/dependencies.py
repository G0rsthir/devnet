from fastapi import Request
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

from devnet_api.security.loader import AUTH_TOKEN_URL

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
