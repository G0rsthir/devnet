# import ingest.device
# from prefect import task
# from prefect.cache_policies import NO_CACHE
# from prefect.concurrency.asyncio import concurrency

# from devnet_core.sync import SyncReport
# from devnet_flows import systems
# from devnet_flows.inventory import InventoryDevice


# @task(
#     name="import-device",
#     task_run_name="import-device-{device.name}",
#     timeout_seconds=300,
#     cache_policy=NO_CACHE,
# )
# async def import_device(device: InventoryDevice, vrfs: ingest.device.VrfRules, dry_run: bool) -> SyncReport:
#     async with concurrency(systems.DEVICE_CONN, strict=True):
#         collected = await ingest.device.collect(systems.device_cli(), device.cli_target())
#     async with systems.netbox() as netbox:
#         return await ingest.device.import_device(
#             netbox, device_id=device.id, device_name=device.name, collected=collected, vrfs=vrfs, dry_run=dry_run
#         )
