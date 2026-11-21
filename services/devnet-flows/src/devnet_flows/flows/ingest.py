from prefect import flow, unmapped
from prefect.states import Completed
from prefect.task_runners import ThreadPoolTaskRunner

from devnet_config import get_config
from devnet_flows.inventory import DeviceQuery
from devnet_flows.monitoring import monitored
from devnet_flows.report import RunReport
from devnet_flows.tasks.ingest import import_device, load_vrf_rules
from devnet_flows.tasks.inventory import select_devices
from devnet_flows.tasks.report import publish_report


@flow(
    name="ingest-devices",
    # Devices of this run at the same time
    task_runner=ThreadPoolTaskRunner(max_workers=20),
)
# The cron of ingest-devices/schedule: Sentry alerts when a run fails, runs too long or is missed
@monitored("ingest-devices", cron="0 2 * * *")
async def ingest_devices(devices: DeviceQuery = DeviceQuery(), dry_run: bool = True):
    """
    Make NetBox match each device: serial, interfaces, IP addresses and MAC addresses
    """
    if not get_config().features.ingest:
        return Completed(message="features.ingest is off")

    selected = await select_devices(devices)
    vrfs = await load_vrf_rules()
    states = import_device.map(selected, vrfs=unmapped(vrfs), dry_run=unmapped(dry_run), return_state=True)

    run = await RunReport.from_states("ingest-devices", [device.name for device in selected], states, dry_run=dry_run)
    await publish_report(run)
    return run.state()
