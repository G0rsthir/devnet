from typing import Annotated

from fastapi import APIRouter, Request, status
from prefect.deployments import arun_deployment

from devnet_api.const import AccessScope
from devnet_api.dependencies import AccessSecurity
from devnet_api.schemas.security import AccessSessionContext

router = APIRouter(prefix="/netbox")

# Deployments started when a NetBox device changes. Each flow decides what, if anything, to change.
DEVICE_SYNCS = ["sync-ise-device/on-change", "sync-prime-device/on-change"]


@router.post(path="/webhooks/device", status_code=status.HTTP_202_ACCEPTED, operation_id="NetboxWebhookDeviceChange")
async def netbox_device_changed(
    access_session: Annotated[AccessSessionContext, AccessSecurity(scopes=[AccessScope.SYSTEM_NETBOX])],
) -> dict[str, list[str]]:
    return {}


# async def verified_netbox_payload(request: Request) -> dict:
#     body = await request.body()
#     # AppEnvSettings.NETBOX_WEBHOOK_SECRET, i.e. DEVNET_API_NETBOX_WEBHOOK_SECRET in .env
#     secret = request.app.state.env.NETBOX_WEBHOOK_SECRET.encode()
#     expected = hmac.new(secret, body, hashlib.sha512).hexdigest()
#     if not hmac.compare_digest(expected, request.headers.get("X-Hook-Signature", "")):
#         raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature")
#     return json.loads(body)


# @router.post("/webhooks/netbox/device", status_code=status.HTTP_202_ACCEPTED)
# async def netbox_device_changed(request: Request) -> dict[str, list[str]]:
#     payload = await verified_netbox_payload(request)
#     device_id = payload["data"]["id"]
#     runs = [
#         await arun_deployment(
#             name,
#             parameters={"device_id": device_id},
#             timeout=0,
#             # One NetBox request can change many devices, so the key includes the device.
#             idempotency_key=f"{payload['request_id']}:{device_id}:{name}",
#         )
#         for name in DEVICE_SYNCS
#     ]
#     return {"flow_runs": [str(run.id) for run in runs]}
