from contextlib import AbstractContextManager
from typing import Protocol

import sentry_sdk
from sentry_sdk.crons import monitor

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


def cron_monitor(
    slug: str, *, cron: str, timezone: str, checkin_margin: int, max_runtime: int
) -> AbstractContextManager[None]:
    """
    Sentry creates the monitor with this schedule

    Args:
        cron: The schedule of the job, e.g. "0 * * * *"
        timezone: The timezone of the schedule, e.g. "UTC"
        checkin_margin: Minutes that a run can start late before Sentry counts it as missed
        max_runtime: Minutes that a run can take before Sentry counts it as failed
    """
    return monitor(
        monitor_slug=slug,
        monitor_config={
            "schedule": {"type": "crontab", "value": cron},
            "timezone": timezone,
            "checkin_margin": checkin_margin,
            "max_runtime": max_runtime,
        },
    )
