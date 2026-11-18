from typing import Protocol

import sentry_sdk

from devnet_core.const import Environments


class MonitoringSettings(Protocol):
    """
    The settings that setup_monitoring reads `CoreEnvSettings`
    """

    ENVIRONMENT: Environments
    SENTRY_DSN: str
    SENTRY_TRACES_SAMPLE_RATE: float
    SENTRY_PROFILES_SAMPLE_RATE: float


def setup_monitoring(env: MonitoringSettings, *, process: str) -> None:
    """
    Start sending what the process does to Sentry, or nothing without a DSN. Call it once, when the process starts.
    """
    if not env.SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=env.SENTRY_DSN,
        environment=env.ENVIRONMENT,
        traces_sample_rate=env.SENTRY_TRACES_SAMPLE_RATE,
        # Profile the code while a transaction runs
        profile_session_sample_rate=env.SENTRY_PROFILES_SAMPLE_RATE,
        profile_lifecycle="trace",
        # The records of the loggers go to Sentry as logs, and those of ERROR and above also as errors
        enable_logs=True,
        # No request bodies, because they hold the credentials
        max_request_body_size="never",
        max_value_length=1024,
    )
    sentry_sdk.get_global_scope().set_tag("process", process)
