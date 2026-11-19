from prefect import flow
from prefect.states import Completed

from devnet_config.models import get_config
from devnet_flows.tasks.ise import sync_device_to_ise


@flow(name="sync-ise-device", flow_run_name="sync-ise-device-{device_id}")
async def sync_ise_device(device_id: int, dry_run: bool = True):
    """
    Make ISE match NetBox for one device. devnet-api starts it for each NetBox change
    """
    if not get_config().features.ise_sync:
        return Completed(message="features.ise_sync is off")

    return await sync_device_to_ise(device_id, dry_run=dry_run)
