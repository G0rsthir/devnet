from pydantic import BaseModel, ConfigDict

from compliance.core import Device
from compliance.netbox.evidence import NetboxDeviceRecord
from system_netbox.client import NetboxClient
from system_netbox.endpoints import Endpoint
from system_netbox.models.generated import WritableDeviceRequest


class _Record(BaseModel):
    # Rules select fields by name in the config file, so all fields of the response are kept
    model_config = ConfigDict(extra="allow")

    id: int


class NetboxDeviceSource:
    """
    Source adapter: the NetBox record of the device
    """

    provides = NetboxDeviceRecord

    def __init__(self, client: NetboxClient) -> None:
        self._devices = Endpoint(client, "/api/dcim/devices/", _Record, WritableDeviceRequest)

    async def collect(self, device: Device) -> NetboxDeviceRecord:
        record = await self._devices.get(device.id)
        return NetboxDeviceRecord(data=record.model_dump())
