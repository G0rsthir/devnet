from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class NetboxRequest(BaseModel):
    """
    The NetBox request behind a change. One request can change many objects
    """

    id: UUID
    user: str


class NetboxRef(BaseModel):
    id: int


class NetboxDeviceChange(BaseModel):
    """
    Body of the webhook NetBox sends when a device is created, updated or deleted

    Only what devnet-api uses: flows read the device from NetBox themselves. NetBox doesn't retry by default,
    so rejecting a body over a field nothing reads would lose the event
    """

    event: Literal["created", "updated", "deleted"]
    timestamp: datetime
    # IDs are per type: without this, a VM's ID could be synced as a device's
    object_type: Literal["dcim.device"]
    request: NetboxRequest
    data: NetboxRef
