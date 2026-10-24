Rules that keep it clean
Logic lives only in packages/. Flows and the webhook service only call it.
Set PREFECT_LOGGING_EXTRA_LOGGERS=devnet_core,compliance,ingest so the packages' normal log output shows up in the Prefect UI.

Imports go one way: everything else → compliance/ingest → devnet-core. Nothing imports from flows/, scripts/ or oneshot/.

Fill devnet-core as sharing appears. This answers your "not sure yet". Start it with settings, secrets, the NetBox client and device connections, and move code in only when a second user needs it.

NetBox is the inventory.
Use the same names in devnet-core's settings, so one .env file locally and one systemd EnvironmentFile on the VM cover both Ansible and Python.
