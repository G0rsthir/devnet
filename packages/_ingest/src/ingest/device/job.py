from ingest.device.collected import CollectedDevice
from ingest.device.models import DeviceDiff
from ingest.device.netbox import NetboxDeviceAdapter
from ingest.device.source import CollectedDeviceAdapter
from ingest.sync import SyncReport, run_sync
from system_netbox.client import NetboxClient


async def import_device(
    client: NetboxClient,
    *,
    device_id: int,
    device_name: str,
    collected: CollectedDevice,
    ip_only: bool = False,
    dry_run: bool = True,
) -> SyncReport:
    """
    Make one NetBox device match what the device reports: serial, interfaces, IP and MAC addresses

    The device must be in NetBox already.

    Args:
        device_id: NetBox ID of the device
        device_name: NetBox name of the device
        ip_only: Only manage interfaces that have an IPv4 address
        dry_run: Compute the changes and write nothing

    Raises:
        SystemConnectionError: If NetBox can't be read. Write errors are in the report
    """
    source = CollectedDeviceAdapter(collected, name=device_name, ip_only=ip_only)
    target = NetboxDeviceAdapter(client, device_id=device_id)
    return await run_sync(source, target, dry_run=dry_run, diff_class=DeviceDiff)
