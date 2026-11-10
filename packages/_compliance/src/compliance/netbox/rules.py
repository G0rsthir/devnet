from typing import Literal

from compliance.core import Device, Evidence, Finding, Rule
from compliance.netbox.evidence import NetboxDeviceRecord, is_empty


class NetboxMustHave(Rule):
    """
    The NetBox record of the device must have a value for each field

    Args:
        fields: Paths of the fields, e.g. `primary_ip4`, `tenant`, `custom_fields.owner`
    """

    kind: Literal["netbox_must_have"] = "netbox_must_have"
    fields: tuple[str, ...]

    async def check(self, device: Device, evidence: Evidence) -> list[Finding]:
        record = await evidence.get(NetboxDeviceRecord)
        missing = [field for field in self.fields if is_empty(record.value(field))]
        return [self.finding(f"NetBox has no value for: {', '.join(missing)}")] if missing else []
