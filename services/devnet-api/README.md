# Devnet API

The webhook service only hands work off. It checks NetBox's X-Hook-Signature header and picks the matching Prefect deployment. It starts it with run_deployment(..., timeout=0) and returns 202 right away. The real work runs in Prefect, which gives you retries, logs and run history.

## Setup

Define enviroment variables (core and devnet-api). .env.example

## Run

```bash
# Start Dev Server
uv run devnet-api run dev

# Start Prod Server
uv run devnet-api run prod
```

## Pachages

```bash
uv add --package devnet-api <package>
```
