from devnet_core.sync import SyncReport, run_sync
from domain_ingest.ise.source import NetboxDeviceSource
from domain_ingest.ise.target import IseDeviceTarget
from system_ise.client import IseClient
from system_netbox.client import NetboxClient


async def sync_device(netbox: NetboxClient, ise: IseClient, *, device_id: int, dry_run: bool = True) -> SyncReport:
    """
    Make ISE match one NetBox device: create, update or delete its network device

    Args:
        device_id: NetBox ID of the device. If NetBox no longer has it, its ISE device is deleted
        dry_run: Compute the changes and write nothing

    Raises:
        SystemConnectionError: If NetBox or ISE can't be read. Write errors are in the report
        DataIntegrityError: If ISE has more than one device with this NetBox ID
    """
    source = NetboxDeviceSource(netbox, device_id=device_id)
    target = IseDeviceTarget(ise, netbox_id=device_id)
    # One device on each side, so a delete is always 100% of the target. A device deleted in NetBox must go
    return await run_sync(source, target, dry_run=dry_run, max_delete_fraction=1.0)
