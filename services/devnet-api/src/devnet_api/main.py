from devnet_api.app import create_http_server
from devnet_api.runtime import bootstrap_runtime
from devnet_core.const import Environments
from devnet_core.monitoring import setup_monitoring


def run_http_server_prod():
    return _start_http_server(Environments.PRODUCTION)


def run_http_server_dev():
    return _start_http_server(Environments.DEVELOPMENT)


def _start_http_server(environment: Environments):
    runtime = bootstrap_runtime(environment)
    # Before the app is built, so that Sentry instruments it
    setup_monitoring(runtime.core, process="api")
    return create_http_server(runtime)
