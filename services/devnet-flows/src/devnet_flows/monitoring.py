from collections.abc import Callable, Coroutine
from functools import cache, wraps
from typing import Any

from devnet_config.env import CoreEnvSettings
from devnet_core.monitoring import cron_monitor, setup_monitoring

# Minutes that a scheduled run can start late before Sentry counts it as missed
CHECKIN_MARGIN = 10


def monitored[**P, R](
    slug: str, *, cron: str | None = None, timezone: str = "UTC", max_runtime: int = 60
) -> Callable[[Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]]:
    """
    Send the errors of the runs of a flow to Sentry, and with a cron, check in with the Sentry cron monitor of the flow

    Goes under `@flow`. The monitor alerts when a run fails, runs longer than max_runtime or does not start

    Args:
        slug: The name of the flow, e.g. "ingest-devices"
        cron: The cron of the deployment `schedule` of the flow. None for a flow without a schedule
        timezone: The timezone of that cron
        max_runtime: Minutes that a run can take
    """

    def decorate(fn: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(fn)
        async def run(*args: P.args, **kwargs: P.kwargs) -> R:
            _setup()
            if cron is None:
                return await fn(*args, **kwargs)
            with cron_monitor(
                slug, cron=cron, timezone=timezone, checkin_margin=CHECKIN_MARGIN, max_runtime=max_runtime
            ):
                return await fn(*args, **kwargs)

        return run

    return decorate


@cache
def _setup() -> None:
    # Once for each process. The process worker starts a process for each flow run
    setup_monitoring(CoreEnvSettings(), process="flows")
