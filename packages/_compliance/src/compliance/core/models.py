from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        """
        Higher is more severe
        """
        return list(Severity).index(self)


class Outcome(StrEnum):
    PASSED = "passed"
    # The rule returned findings
    FAILED = "failed"
    # The rule does not apply to this device
    SKIPPED = "skipped"
    # The rule could not run: its data could not be collected, or the rule raised
    ERROR = "error"


@dataclass(frozen=True, kw_only=True)
class Device:
    """
    The device that a run checks, as the inventory (NetBox) knows it

    Args:
        platform: NetBox platform slug
        role: NetBox role slug
        site: NetBox site slug
        tags: NetBox tag slugs
        primary_ip: Address without the prefix length
    """

    id: int
    name: str
    platform: str | None = None
    role: str | None = None
    site: str | None = None
    tags: frozenset[str] = frozenset()
    primary_ip: str | None = None


@dataclass(frozen=True, kw_only=True)
class Finding:
    """
    One thing that is not compliant

    Args:
        rule: Name of the rule
        lines: Config lines or values that show the problem, for the report
    """

    rule: str
    severity: Severity
    message: str
    lines: tuple[str, ...] = ()
