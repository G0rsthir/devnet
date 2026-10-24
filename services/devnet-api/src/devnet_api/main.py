from devnet_api.app import create_http_server
from devnet_api.runtime import bootstrap_runtime
from devnet_core.const import EnvironmentsEnum


def run_http_server_prod():
    container = bootstrap_runtime(EnvironmentsEnum.PRODUCTION)
    return create_http_server(app_context=container)


def run_http_server_dev():
    container = bootstrap_runtime(EnvironmentsEnum.DEVELOPMENT)
    return create_http_server(app_context=container)
