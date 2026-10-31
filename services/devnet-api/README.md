# Devnet API

The webhook service only hands work off

## Setup

Define environment variables (core and devnet-api). .env.dev.example

## Run

```bash
# Start Dev Server
uv run devnet-api run dev

# Start Prod Server
uv run devnet-api run prod
```

## API Tokens

Clients send a token in the `Authorization: Bearer <token>` header.

```bash
# --scope can repeat. --expires-in takes m, h, d, w, y
uv run devnet-api token create netbox --scope system:netbox --expires-in 365d

# In the container
docker compose run --rm api devnet-api token create netbox -s system:netbox -e 365d
```

To revoke a token before it expires, add its `jti` to `.env` and restart the API.

```bash
DEVNET_API_REVOKED_JWT_TOKENS=["b9bff4ef2a0340aeaebaf92b9a3fa1fb"]
```

## Pachages

```bash
uv add --package devnet-api <package>
```

## ???

- **Redelivered webhooks don't start new runs.** The idempotency key is built from NetBox's `request_id`,
