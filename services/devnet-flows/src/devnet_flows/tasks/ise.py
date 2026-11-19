from prefect import task
from prefect.cache_policies import NO_CACHE

import domain_ingest.ise
from devnet_core.logging import get_logger
from devnet_core.sync import SyncReport
from devnet_flows import systems

logger = get_logger(__name__)


@task(
    name="sync-device-to-ise",
    task_run_name="sync-device-to-ise-{device_id}",
    retries=1,
    retry_delay_seconds=30,
    retry_condition_fn=systems.transient,
    timeout_seconds=120,
    cache_policy=NO_CACHE,
)
async def sync_device_to_ise(device_id: int, dry_run: bool) -> SyncReport:
    """
    Make ISE match one NetBox device
    """
    async with systems.netbox() as netbox, systems.ise() as ise:
        report = await domain_ingest.ise.sync_device(netbox, ise, device_id=device_id, dry_run=dry_run)
    if dry_run:
        logger.info(report.diff)
    return report
