Rules that keep it clean
Logic lives only in packages/. Flows and the webhook service only call it.
Set PREFECT_LOGGING_EXTRA_LOGGERS=devnet_core,compliance,ingest so the packages' normal log output shows up in the Prefect UI.

Imports go one way: everything else → compliance/ingest → devnet-core. Nothing imports from flows/, scripts/ or oneshot/.

Fill devnet-core as sharing appears. This answers your "not sure yet". Start it with settings, secrets, the NetBox client and device connections, and move code in only when a second user needs it.

NetBox is the inventory.
Use the same names in devnet-core's settings, so one .env file locally and one systemd EnvironmentFile on the VM cover both Ansible and Python.

## Dev environment

POSTGRES_PASSWORD=dev
PREFECT_API_AUTH_STRING=admin:dev
PREFECT_API_URL=http://127.0.0.1:4200/api

Compose fills ${...} from this file. Prefect also reads it when you run from the repo root, so your local code gets the server address and login. Everything else runs from your venv, without building images:

pytest
uv run python flows/ise_flow.py
uv run python flows/serve_local.py together with uv run devnet-api serve, for the full webhook chain
Occasionally: the production setup. After changing the Dockerfile, the dependencies or flows/prefect.yaml, run docker compose up -d --build and then docker compose run --rm deploy, as in my test. Don't use serve_local.py against the same server at the same time. Both register sync-ise-device/on-change: the serve script without a work pool, the deploy step with the devnet pool. Whichever ran last wins.

Two things blocking you now
Then run uv sync from the repo root to restore your venv.
Want me to add the Dockerfile, .dockerignore and compose.yaml, switch the pull step in flows/prefect.yaml, and update DEVELOPMENT.md? It still describes systemd units on a VM.
