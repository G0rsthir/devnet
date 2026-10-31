# Development

## Environment Setup

Create .env for development. Update required variables

```bash
cp .env.dev.example .env
```

Instal UV environment manager

```bash
pip install uv
```

Synchronize python environment with uv

```bash
uv sync
```

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Start docker containers (Prefect Server) and optionally Netbox

```bash
docker compose -f deploy/docker/docker-compose.dev.yml --profile netbox  up  -d
```

Prefect UI - <http://localhost:4200/>

Netbox UI - <http://localhost:8080/>

## Python Environment

````bash
# add python package
uv add --package devnet-api fastapi[standard]

# create workspace
uv init --lib --vcs none --no-pin-python packages/ise

## End to End Docker Test

```bash
docker compose -f deploy/docker/docker-compose.e2e.yml up
````

Prefect UI <http://127.0.0.1:4210>
