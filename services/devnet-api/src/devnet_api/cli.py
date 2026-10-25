from pathlib import Path

import uvicorn
from typer import Typer, echo

import devnet_api.infrastructure.logging
import devnet_api.runtime
import devnet_core
import devnet_core.const

# Shipped inside the package
LOG_CONFIG = Path(devnet_api.infrastructure.logging.__file__).parent / "logging.yaml"

# Main CLI app
cli = Typer(no_args_is_help=True)

# Run CLI
run_cli = Typer(help="Commands for running the API", no_args_is_help=True)

cli.add_typer(run_cli, name="run")


@run_cli.command(name="dev")
def dev_server():
    """
    Run the server in development mode
    """
    container = devnet_api.runtime.bootstrap_runtime(devnet_core.const.Environments.DEVELOPMENT)

    echo("Running in development mode")
    echo("In development mode, for more details, please refer to the developer guide.")

    devnet_api.runtime.validate_server_startup(env=container.env)

    uvicorn.run(
        app="devnet_api.main:run_http_server_dev",
        reload=True,
        factory=True,
        port=8000,
        host="0.0.0.0",
        log_config=LOG_CONFIG,
        # devnet-core is an editable install: watch it too.
        reload_dirs=[str(Path(devnet_api.__file__).parent), str(Path(devnet_core.__file__).parent)],
    )


@run_cli.command(name="prod")
def prod_server():
    """
    Run the server in production mode
    """
    container = devnet_api.runtime.bootstrap_runtime(devnet_core.const.Environments.PRODUCTION)

    echo("Running in production mode")

    devnet_api.runtime.validate_server_startup(env=container.env)

    uvicorn.run(
        app="devnet_api.main:run_http_server_prod",
        factory=True,
        port=8000,
        host="0.0.0.0",
        log_config=LOG_CONFIG,
    )
