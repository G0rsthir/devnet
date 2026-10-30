import asyncio
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

from typer import Argument, BadParameter, Exit, Option, Typer, echo
from uvicorn import run as uvicorn_rum

import devnet_api
import devnet_core
from devnet_api.const import AccessScope
from devnet_api.infrastructure.logging import LOG_CONFIG_PATH
from devnet_api.provision import netbox_provision_config, provision_netbox
from devnet_api.runtime import bootstrap_runtime, validate_server_startup
from devnet_api.security.loader import create_auth_managers
from devnet_api.services.token import AuthTokenService
from devnet_config import get_config
from devnet_core.const import Environments
from devnet_core.exceptions import ConfigurationError, SystemConnectionError

DURATION_UNITS = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks", "y": "years"}

# Main CLI app
cli = Typer(no_args_is_help=True)

# Run CLI
run_cli = Typer(help="Commands for running the API", no_args_is_help=True)

# Token CLI
token_cli = Typer(help="Commands for API tokens", no_args_is_help=True)

cli.add_typer(run_cli, name="run")
cli.add_typer(token_cli, name="token")


@run_cli.command(name="dev")
def dev_server():
    """
    Run the server in development mode
    """
    container = bootstrap_runtime(Environments.DEVELOPMENT)

    echo("Running in development mode")
    echo("In development mode, for more details, please refer to the developer guide")

    validate_server_startup(env=container.env)

    uvicorn_rum(
        app="devnet_api.main:run_http_server_dev",
        reload=True,
        factory=True,
        port=8000,
        host="0.0.0.0",
        log_config=LOG_CONFIG_PATH,
        # devnet-core is an editable install: watch it too
        reload_dirs=[str(Path(devnet_api.__file__).parent), str(Path(devnet_core.__file__).parent)],
    )


@run_cli.command(name="prod")
def prod_server():
    """
    Run the server in production mode
    """
    container = bootstrap_runtime(Environments.PRODUCTION)

    echo("Running in production mode")

    validate_server_startup(env=container.env)

    uvicorn_rum(
        app="devnet_api.main:run_http_server_prod",
        factory=True,
        port=8000,
        host="0.0.0.0",
        log_config=LOG_CONFIG_PATH,
    )


def parse_duration(value: str) -> timedelta:
    match = re.fullmatch(r"([1-9][0-9]*)([mhdwy])", value)
    if not match:
        raise BadParameter("use a number and m, h, d, w or y, e.g. 90d")
    amount, unit = match.groups()
    return timedelta(**{DURATION_UNITS[unit]: int(amount)})


def _token_service() -> AuthTokenService:
    container = bootstrap_runtime()

    validate_server_startup(env=container.env)

    access_manager, refresh_manager = create_auth_managers(
        access_jwt_secret=container.env.ACCESS_JWT_SECRET,
        refresh_jwt_secret=container.env.REFRESH_JWT_SECRET,
    )

    return AuthTokenService(access_manager=access_manager, refresh_manager=refresh_manager)


@token_cli.command(name="create")
def create_token(
    name: Annotated[str, Argument(help="Who uses the token, e.g. netbox")],
    scopes: Annotated[list[AccessScope], Option("--scope", "-s", help="Repeat for more scopes")],
    expires_in: Annotated[
        timedelta,
        Option("--expires-in", "-e", parser=parse_duration, metavar="DURATION", help="e.g. 30m, 12h, 90d, 52w"),
    ],
):
    """
    Create an access token. Prints the token to stdout and its details to stderr
    """
    token_service = _token_service()

    expires_at = datetime.now(UTC) + expires_in

    token = token_service.issue_access_token(sub=name, expires_at=expires_at, scopes=scopes)

    echo(f"{name}: {', '.join(scopes)}, expires {expires_at:%Y-%m-%d %H:%M} UTC", err=True)
    echo(token)


@cli.command()
def provision():
    """
    Create or update the NetBox objects devnet-api needs
    """
    try:
        token_service = _token_service()
        webhook_url = netbox_provision_config().webhook_url
        asyncio.run(provision_netbox(get_config().systems.netbox, webhook_url, token_service))
    except (ConfigurationError, SystemConnectionError) as e:
        echo(str(e), err=True)
        raise Exit(1) from e

    echo("NetBox provisioned")
