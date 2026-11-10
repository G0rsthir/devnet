from collections.abc import Iterable

from compliance.core.evidence import AnySource, Evidence, EvidenceError
from compliance.core.models import Device, Outcome
from compliance.core.report import DeviceReport, RuleResult
from compliance.core.rule import NotApplicable, Rule
from devnet_core.logging import get_logger

logger = get_logger(__name__)


async def check_device(device: Device, rules: Iterable[Rule], sources: Iterable[AnySource]) -> DeviceReport:
    """
    Run each rule against one device

    A rule that fails or raises does not stop the other rules. This function does not raise for
    a device that is unreachable: the report then has the outcome `error` for the rules that need the device.

    Args:
        sources: One source for each kind of data that the rules ask for
    """
    evidence = Evidence(device, sources)
    report = DeviceReport(device=device.name)
    for rule in rules:
        report.results.append(await _run(rule, device, evidence))
    logger.info(report.summary())
    return report


async def _run(rule: Rule, device: Device, evidence: Evidence) -> RuleResult:
    if not rule.scope.matches(device):
        return RuleResult(rule=rule.name, outcome=Outcome.SKIPPED, detail="out of scope")
    try:
        findings = await rule.check(device, evidence)
    except NotApplicable as e:
        return RuleResult(rule=rule.name, outcome=Outcome.SKIPPED, detail=str(e))
    except EvidenceError as e:
        return RuleResult(rule=rule.name, outcome=Outcome.ERROR, detail=str(e))
    except Exception as e:
        logger.error("Rule %s raised on %s", rule.name, device.name, exc_info=e)
        return RuleResult(rule=rule.name, outcome=Outcome.ERROR, detail=f"rule {rule.name}: {type(e).__name__}: {e}")
    if findings:
        return RuleResult(rule=rule.name, outcome=Outcome.FAILED, findings=tuple(findings))
    return RuleResult(rule=rule.name, outcome=Outcome.PASSED)
