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

## API Tokens

Clients send a token in the `Authorization: Bearer <token>` header. Create one where `DEVNET_API_ACCESS_JWT_SECRET` is set. Only the token goes to stdout. Its name, scopes, expiry and `jti` go to stderr. Note the `jti`: revoking the token needs it.

```bash
# --scope can repeat. --expires-in takes m, h, d or w
uv run devnet-api token create netbox --scope system:netbox --expires-in 365d

# In the container
docker compose run --rm api devnet-api token create netbox -s system:netbox -e 365d
```

To revoke a token before it expires, add its `jti` to `.env` and restart the API. With Docker, use `docker compose up -d api`: `restart` keeps the old environment. Remove the `jti` once the token has expired. Changing `DEVNET_API_ACCESS_JWT_SECRET` revokes every token.

```bash
DEVNET_API_REVOKED_JWT_TOKENS=["b9bff4ef2a0340aeaebaf92b9a3fa1fb"]
```

## Pachages

```bash
uv add --package devnet-api <package>
```

## ???

- **Redelivered webhooks don't start new runs.** The idempotency key is built from NetBox's `request_id`,
