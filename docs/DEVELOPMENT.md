# Development

## Structure

```markdown
devnet/
├── pyproject.toml           # uv workspace root: one .venv, one uv.lock
├── uv.lock
├── prefect.yaml             # all deployments + schedules (process worker pool)
├── Makefile                 # sync / lint / test / deploy
├── .pre-commit-config.yaml  # ruff, yamllint, ansible-lint, gitleaks
├── .env.example             # NETBOX_API, NETBOX_TOKEN, DEVICE_USER… (names only)
│
├── packages/                # ALL logic: plain Python, no Prefect/FastAPI
│   ├── devnet-core/         # settings, secrets, NetBox client, device access
│   ├── compliance/          # collect → normalize → check → report (+ CLI)
│   └── ingest/              # fetch → normalize → diff → write (+ CLI)
│
├── services/
│   └── devnet-api/          # FastAPI: NetBox webhooks + other requests → start Prefect run → 202
│
├── flows/                   # thin Prefect wrappers: schedule, retry, combine
│   ├── compliance.py
│   ├── ingest.py
│   └── backups.py           # runs a playbook via devnet_core.run_playbook()
│
├── ansible/                 # read-only playbooks, started by flows
│   ├── ansible.cfg
│   ├── requirements.yml     # pinned collections: netbox.netbox, cisco.ios…
│   ├── inventory/
│   │   ├── netbox.yml       # nb_inventory plugin, no static hosts
│   │   └── group_vars/      # device creds via lookup('env', …)
│   └── playbooks/
│
├── scripts/                 # reusable, maintained, have --help
├── oneshot/                 # 2026-10-23_vlan-cleanup/: README + script, run once
├── deploy/docker/           # Dockerfile.automation + compose files (dev, e2e, prod)
└── .github/workflows/       # or .gitlab-ci.yml
Each package has the same layout inside:


packages/compliance/
├── pyproject.toml           # dependencies = ["devnet-core"]
├── src/compliance/
│   ├── collect.py
│   ├── checks/              # ntp.py, aaa.py, bgp.py: intended (NetBox) vs actual
│   ├── report.py
│   └── cli.py               # `compliance run --site X`: same function the flow calls
└── tests/fixtures/          # saved device output, so CI tests checks offline
```

## Enviroment Setup

Create .env for development. Update required variables

```bash
cp .env.example .env
```

Start docker containers (Prefect Server)

```bash
docker compose -f deploy/docker/docker-compose.dev.yml up -d
```

Prefect UI - <http://localhost:4200/>

## Python Enviroment

```bash
# add python package
uv add --package devnet-api fastapi[standard]

#
uv init --lib --vcs none --no-pin-python packages/ise
```

## End to End Docker Test

```bash
docker compose -f deploy/docker/docker-compose.e2e.yml up
```

Prefect UI <http://127.0.0.1:4210>
