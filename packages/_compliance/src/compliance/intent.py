"""
Rules that compare two systems: the config of a device against its data in NetBox
"""

from typing import Literal

from pydantic import field_validator

from compliance.cisco import RunningConfig
from compliance.core import Device, Evidence, Finding, NotApplicable, Rule
from compliance.netbox import NetboxDeviceRecord
from compliance.netbox.evidence import is_empty

_VALUE = "{value}"


class ConfigMustContainNetbox(Rule):
    """
    The config must have one top-level line for each value of a NetBox field

    Args:
        netbox_field: Path of the field, e.g. `config_context.ntp_servers`. One value or a list.
            The rule is skipped for a device without a value
        line: The config line for one value, e.g. `ntp server {value}`
    """

    kind: Literal["config_must_contain_netbox"] = "config_must_contain_netbox"
    netbox_field: str
    line: str

    @field_validator("line")
    @classmethod
    def _has_placeholder(cls, line: str) -> str:
        if _VALUE not in line:
            raise ValueError(f"must contain {_VALUE}")
        return line

    async def check(self, device: Device, evidence: Evidence) -> list[Finding]:
        record = await evidence.get(NetboxDeviceRecord)
        values = record.value(self.netbox_field)
        if is_empty(values):
            raise NotApplicable(f"NetBox has no value for {self.netbox_field}")
        if not isinstance(values, list):
            values = [values]

        config = await evidence.get(RunningConfig)
        present = {line.text for line in config.tree.top}
        missing = [line for value in values if (line := self.line.replace(_VALUE, str(value))) not in present]
        return [self.finding(f"missing: {'; '.join(missing)}")] if missing else []
