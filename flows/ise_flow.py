from ise.sync import devices_to_check, sync_device
from prefect import flow, get_run_logger


@flow(name="sync-ise-device", retries=3, retry_delay_seconds=120)
def sync_ise_device(device_id: int, dry_run: bool = False) -> None:
    """Make ISE match NetBox for one device."""
    change = sync_device(device_id, dry_run=dry_run)
    get_run_logger().info("ISE: %s", change)


@flow(name="reconcile-ise")
def reconcile_ise(dry_run: bool = False) -> None:
    """Nightly safety net: sync every NetBox device and every ISE device devnet manages."""
    for device_id in devices_to_check():
        sync_device(device_id, dry_run=dry_run)
