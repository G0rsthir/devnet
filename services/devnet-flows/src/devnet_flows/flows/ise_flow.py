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


from devnet_flows.tasks.netbox import fetch_device
from prefect import flow, task

from ise import client, mapping, sync


@task(retries=3, retry_delay_seconds=60)
def read_ise_device(device_id: int) -> client.IseDevice | None:
    return client.find_device(netbox_id=device_id)


@task(retries=3, retry_delay_seconds=60)
def apply_to_ise(change: sync.Change) -> None:
    client.apply(change)


@flow(name="sync-ise-device")
def sync_ise_device(device_id: int, dry_run: bool = False) -> None:
    device = fetch_device(device_id)  # task: NetBox read
    change = sync.plan(mapping.desired(device), read_ise_device(device_id))  # transforms
    if change and not dry_run:
        apply_to_ise(change)
