# Development

## Environment Setup

### IDE, Docker and Package Management

UV Package Manager - <https://docs.astral.sh>

Rootless Docker - <https://docs.docker.com/engine/security/rootless/>

VS Code and recommended extensions - <https://code.visualstudio.com/>

### Packages

```bash
# Create .env for development. Update required variables
cp .env.dev.example .env

# Copy or merge .vscode/settings.json for development
cp .vscode/settings.json.default .vscode/settings.json

# Install python dependencies
uv sync

# Run pre-commit hooks
uv run pre-commit install
uv run pre-commit run --all-files

```

### Start docker containers (Netbox, Prefect, etc.)

```bash
docker compose -f deploy/docker/docker-compose.dev.yml --profile netbox  up  -d
```

Prefect UI - <http://localhost:4200/>

Netbox UI - <http://localhost:8080/>

## Common Development Commands

```bash
# add python package
uv add --package devnet-api <package-name>

# remove python package
uv remove --no-sync --package devnet-flows <package-name>

# create workspace
uv init --lib --vcs none --no-pin-python packages/system-<name>

```
