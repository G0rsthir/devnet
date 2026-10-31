# Network Automation

A collection of network automation scripts that use NetBox as the source of truth

## Docs

Development - [docs/DEVELOPMENT](docs/DEVELOPMENT.md)

Deployment and Debug - [docs/DEPLOYMENT](docs/DEPLOYMENT.md)

git commit --no-verify

uv add --dev pre-commit import-linter
uv run pre-commit install # each developer runs this once
uv run pre-commit run --all-files # check everything
