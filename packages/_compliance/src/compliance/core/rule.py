import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Annotated

from pydantic import AfterValidator

from compliance.core.evidence import Evidence
from compliance.core.models import Device, Finding, Severity
from devnet_core.settings import ConfigModel


def _regex(value: str) -> str:
    try:
        re.compile(value)
    except re.error as e:
        raise ValueError(f"not a regular expression: {e}") from e
    return value


# A pattern in the config file. A bad pattern fails when the config loads, not when a rule runs
type Regex = Annotated[str, AfterValidator(_regex)]


class NotApplicable(Exception):
    """
    Raised by a rule: the thing that the rule checks is not on this device

    The outcome is `skipped`, with the message as the reason.
    """


class Scope(ConfigModel):
    """
    The devices that a rule applies to. An empty field matches each device

    Args:
        platforms: NetBox platform slugs
        roles: NetBox role slugs
        sites: NetBox site slugs
        tags: NetBox tag slugs. The device must have all of them
    """

    platforms: frozenset[str] = frozenset()
    roles: frozenset[str] = frozenset()
    sites: frozenset[str] = frozenset()
    tags: frozenset[str] = frozenset()

    def matches(self, device: Device) -> bool:
        return (
            (not self.platforms or device.platform in self.platforms)
            and (not self.roles or device.role in self.roles)
            and (not self.sites or device.site in self.sites)
            and self.tags <= device.tags
        )


class Rule(ConfigModel, ABC):
    """
    Base of each rule kind

    A subclass is one kind of rule. Its fields are the parameters of the rule in the config file.
    It adds `kind: Literal["..."]`, which selects the class when the config loads.

    Args:
        name: Identifies the rule in the report. Unique in the config file
    """

    name: str
    description: str = ""
    severity: Severity = Severity.WARNING
    scope: Scope = Scope()

    @abstractmethod
    async def check(self, device: Device, evidence: Evidence) -> list[Finding]:
        """
        Returns:
            One finding for each problem. An empty list if the device is compliant

        Raises:
            NotApplicable: If the device does not have the thing that the rule checks
        """

    def finding(self, message: str, *, lines: Iterable[str] = ()) -> Finding:
        return Finding(rule=self.name, severity=self.severity, message=message, lines=tuple(lines))
