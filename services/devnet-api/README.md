# Devnet API

The webhook service only hands work off

## Setup

For development guide, see [docs/DEVELOPMENT.md](../../docs/DEVELOPMENT.md).

### Run

```bash
# Start Dev Server
uv run devnet-api run dev

# Start Prod Server
uv run devnet-api run prod
```

## API Token generation

Clients send a token in the `Authorization: Bearer <token>` header

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

## Design

- **Redelivered webhooks don't start new runs.** The idempotency key is built from NetBox's `request_id`,
