from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from devnet_api.runtime import RuntimeContainer
from devnet_api.security.loader import create_auth_managers
from devnet_core.const import Environments

from .routes import api_router


# TODO improve description
def create_http_server(app_context: RuntimeContainer, **kwargs) -> FastAPI:
    debug = False

    if app_context.core.ENVIRONMENT == Environments.DEVELOPMENT:
        debug = True

    app = FastAPI(
        title="API Documentation",
        description=(
            "## Authentication\n"
            "\n"
            "All endpoints require a bearer token in the `Authorization` header.\n"
            "\n"
            "Create a token on the server:\n"
            "\n"
            "```bash\n"
            "devnet-api token create netbox --scope system:netbox --expires-in 365d\n"
            "```\n"
            "\n"
            "Send it on every request:\n"
            "\n"
            "```\n"
            "Authorization: Bearer <your-token>\n"
            "```\n"
            "\n"
            "Example:\n"
            "\n"
            "```bash\n"
            'curl -H "Authorization: Bearer $TOKEN" https://your-host/api/v1/identity/users\n'
            "```\n"
        ),
        debug=debug,
        docs_url="/api/v1/docs" if debug else None,
        redoc_url="/api/v1/redoc" if debug else None,
        openapi_url="/api/v1/openapi.json" if debug else None,
        version="v1",
    )

    access_manager, refresh_manager = create_auth_managers(
        access_jwt_secret=app_context.env.ACCESS_JWT_SECRET,
        refresh_jwt_secret=app_context.env.REFRESH_JWT_SECRET,
        revoked_tokens=app_context.env.REVOKED_JWT_TOKENS,
    )

    app.state.env = app_context.env
    app.state.app_context = app_context

    app.state.access_manager = access_manager
    app.state.refresh_manager = refresh_manager

    # Compression
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)

    app.include_router(api_router, prefix="/api/v1")

    return app
