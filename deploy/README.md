# Deployment

## On the prod host, next to compose.yaml. The token only lives in this shell

```bash
read -rsp "NetBox provisioning token: " NETBOX_PROVISION_TOKEN && export NETBOX_PROVISION_TOKEN

docker compose run --rm -e NETBOX_PROVISION_TOKEN api devnet-api provision --dry-run
docker compose run --rm -e NETBOX_PROVISION_TOKEN api devnet-api provision
docker compose run --rm prefect-worker devnet-flows provision
```
