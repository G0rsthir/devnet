# 0002. DiffSync For Reconciliation

- Status: Proposed
- Date: 2026-11-10

devnet uses [DiffSync](https://github.com/networktocode/diffsync) to compare two systems and to apply the difference. It replaces the reconciler of the old project (`netbox_pipelines/sync/common.py`)

## Why

- It is the common library for this job in network automation. Nautobot SSoT and network-importer use it
- Its models pair by names, not by database IDs. The whole change set is known before the first write, so a dry run is complete
- Parent and child order, skip rules (flags), diff and summary are part of the library. devnet does not maintain them
- One pattern for each direction: device to NetBox, NSX to NetBox, NetBox to ISE

## Consequences

- DiffSync is blocking code. devnet loads data with async code, and runs the DiffSync sync in a worker thread. Each write goes back to the event loop. See [the plan](../plans/ingest-framework.md#async)
- One write is one HTTP request. DiffSync has no bulk writes
- DiffSync logs with structlog. devnet sends these events to the `devnet.diffsync` logger
- New dependencies: `diffsync`, `structlog`

## Alternatives

| Alternative                                   | Why not                                                                                     |
| --------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Keep the old reconciler                       | Own engine to maintain. Pairs by NetBox ID, so children need a second and third pass        |
| DiffSync for the diff only, own async apply   | Async and bulk writes, but devnet writes the apply order and error rules again              |
| NetBox Diode                                  | One more service to run. It writes to NetBox only, so NetBox to ISE needs a second tool     |
| Generic diff libraries (DeepDiff, dictdiffer) | They compare dicts. They have no models, no parent and child order, no create/update/delete |
