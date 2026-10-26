from collections.abc import Collection
from typing import Any

from pydantic import ValidationError

from devnet_api.schemas.security import AccessSessionContext, RefreshSessionContext
from devnet_core.logging import get_logger

from .manager import AuthManager

logger = get_logger(__name__)


async def load_access_context(context_info: dict[str, Any]) -> AccessSessionContext | None:
    try:
        session = AccessSessionContext.model_validate(context_info)
    except ValidationError as e:
        logger.debug("Failed to validate access session context", exc_info=e)
        return

    return session


async def load_refresh_context(context_info: dict[str, Any]) -> RefreshSessionContext | None:
    try:
        session = RefreshSessionContext.model_validate(context_info)
    except ValidationError as e:
        logger.debug("Failed to validate refresh session context", exc_info=e)
        return

    return session


AUTH_URL = "/api/v1/auth"
AUTH_TOKEN_URL = AUTH_URL + "/token"


def create_auth_managers(access_jwt_secret: str, refresh_jwt_secret: str, revoked_tokens: Collection[str] = ()):
    access_manager = AuthManager(
        secret=access_jwt_secret,
        token_url=AUTH_TOKEN_URL,
        use_cookie=False,
        context_callback=load_access_context,
        use_header=True,
        revoked_tokens=revoked_tokens,
    )

    refresh_manager = AuthManager(
        secret=refresh_jwt_secret,
        token_url=AUTH_TOKEN_URL,
        use_cookie=True,
        use_header=False,
        context_callback=load_refresh_context,
        revoked_tokens=revoked_tokens,
    )

    return access_manager, refresh_manager
