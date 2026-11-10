"""
The engine with the smallest possible feature: one kind of data, one source, one rule
"""

from dataclasses import dataclass
from typing import Literal

import pytest

from compliance.core import Device, Evidence, Finding, NotApplicable, Outcome, Rule, Scope, Severity, check_device

pytestmark = pytest.mark.anyio


@dataclass(frozen=True)
class Uptime:
    days: int


class UptimeSource:
    """
    An adapter of the Source port. A real one reads a system
    """

    provides = Uptime

    def __init__(self, days: dict[str, int]) -> None:
        self.days = days
        self.calls = 0

    async def collect(self, device: Device) -> Uptime:
        self.calls += 1
        if device.name not in self.days:
            raise LookupError(f"{device.name} is unreachable")
        return Uptime(days=self.days[device.name])


class MaxUptime(Rule):
    kind: Literal["max_uptime"] = "max_uptime"
    days: int

    async def check(self, device: Device, evidence: Evidence) -> list[Finding]:
        uptime = await evidence.get(Uptime)
        if uptime.days <= self.days:
            return []
        return [self.finding(f"up for {uptime.days} days, the limit is {self.days}")]


class Broken(Rule):
    kind: Literal["broken"] = "broken"

    async def check(self, device: Device, evidence: Evidence) -> list[Finding]:
        raise ZeroDivisionError("bug in the rule")


class OnlyWithStack(Rule):
    kind: Literal["only_with_stack"] = "only_with_stack"

    async def check(self, device: Device, evidence: Evidence) -> list[Finding]:
        raise NotApplicable("the device is not a stack")


SW1 = Device(id=1, name="sw1", role="access")
YEAR = MaxUptime(name="reboot-each-year", days=365, severity=Severity.ERROR)


async def test_compliant_device_passes() -> None:
    report = await check_device(SW1, [YEAR], [UptimeSource({"sw1": 30})])

    assert report.compliant
    assert [result.outcome for result in report.results] == [Outcome.PASSED]
    assert report.summary() == "sw1 compliance: passed=1 failed=0 skipped=0 error=0 findings=0"


async def test_problem_is_a_finding() -> None:
    report = await check_device(SW1, [YEAR], [UptimeSource({"sw1": 400})])

    assert not report.compliant
    assert report.findings == [
        Finding(rule="reboot-each-year", severity=Severity.ERROR, message="up for 400 days, the limit is 365")
    ]


async def test_rule_out_of_scope_is_skipped_and_collects_nothing() -> None:
    source = UptimeSource({"sw1": 400})
    core_only = MaxUptime(name="core", days=1, scope=Scope(roles=frozenset({"core"})))

    report = await check_device(SW1, [core_only], [source])

    assert report.compliant
    assert report.results[0].outcome == Outcome.SKIPPED
    assert report.results[0].detail == "out of scope"
    assert source.calls == 0


@pytest.mark.parametrize(
    ("scope", "matches"),
    [
        (Scope(), True),
        (Scope(roles=frozenset({"access", "core"})), True),
        (Scope(roles=frozenset({"core"})), False),
        (Scope(platforms=frozenset({"iosxe"}), sites=frozenset({"hq"})), True),
        (Scope(platforms=frozenset({"iosxe"}), sites=frozenset({"branch"})), False),
        # A device must have all tags of the scope
        (Scope(tags=frozenset({"pci"})), True),
        (Scope(tags=frozenset({"pci", "lab"})), False),
    ],
)
def test_scope(scope: Scope, matches: bool) -> None:
    device = Device(id=1, name="sw1", platform="iosxe", role="access", site="hq", tags=frozenset({"pci", "prod"}))

    assert scope.matches(device) is matches


async def test_data_is_collected_one_time_for_all_rules() -> None:
    source = UptimeSource({"sw1": 30})
    rules = [MaxUptime(name=f"limit-{days}", days=days) for days in (10, 100, 1000)]

    report = await check_device(SW1, rules, [source])

    assert [result.outcome for result in report.results] == [Outcome.FAILED, Outcome.PASSED, Outcome.PASSED]
    assert source.calls == 1


async def test_failed_source_is_an_error_and_other_rules_still_run() -> None:
    source = UptimeSource({})
    rules = [YEAR, MaxUptime(name="reboot-each-month", days=30), OnlyWithStack(name="stack")]

    report = await check_device(SW1, rules, [source])

    assert [result.outcome for result in report.results] == [Outcome.ERROR, Outcome.ERROR, Outcome.SKIPPED]
    assert not report.compliant
    assert report.findings == []
    assert report.errors == ["Uptime: sw1 is unreachable (2 rules)"]
    assert source.calls == 1


async def test_rule_that_raises_does_not_stop_the_other_rules() -> None:
    report = await check_device(SW1, [Broken(name="broken"), YEAR], [UptimeSource({"sw1": 30})])

    assert [result.outcome for result in report.results] == [Outcome.ERROR, Outcome.PASSED]
    assert report.errors == ["rule broken: ZeroDivisionError: bug in the rule"]


async def test_not_applicable_rule_is_skipped_with_its_reason() -> None:
    report = await check_device(SW1, [OnlyWithStack(name="stack")], [])

    assert report.compliant
    assert report.results[0].outcome == Outcome.SKIPPED
    assert report.results[0].detail == "the device is not a stack"


async def test_missing_source_is_an_error() -> None:
    report = await check_device(SW1, [YEAR], [])

    assert report.errors == ["Uptime: no source is configured"]
