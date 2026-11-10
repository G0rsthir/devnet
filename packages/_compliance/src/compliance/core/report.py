from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field

from compliance.core.models import Finding, Outcome


@dataclass(frozen=True, kw_only=True)
class RuleResult:
    """
    Args:
        detail: Why the rule was skipped, or why it could not run
    """

    rule: str
    outcome: Outcome
    findings: tuple[Finding, ...] = ()
    detail: str = ""


@dataclass(kw_only=True)
class DeviceReport:
    """
    Result of all rules for one device
    """

    device: str
    results: list[RuleResult] = field(default_factory=list)

    def count(self, outcome: Outcome) -> int:
        return sum(result.outcome == outcome for result in self.results)

    @property
    def findings(self) -> list[Finding]:
        return [finding for result in self.results for finding in result.findings]

    @property
    def errors(self) -> list[str]:
        """
        One line for each reason. Rules that could not run for the same reason share a line
        """
        reasons = Counter(result.detail for result in self.results if result.outcome == Outcome.ERROR)
        return [f"{reason} ({rules} rules)" if rules > 1 else reason for reason, rules in reasons.items()]

    @property
    def compliant(self) -> bool:
        """
        False also if a rule could not run: the device is then not known to be compliant
        """
        return not self.count(Outcome.FAILED) and not self.count(Outcome.ERROR)

    def summary(self) -> str:
        counts = " ".join(f"{outcome}={self.count(outcome)}" for outcome in Outcome)
        return f"{self.device} compliance: {counts} findings={len(self.findings)}"


@dataclass(kw_only=True)
class ComplianceRun:
    """
    The reports of all devices of one run
    """

    reports: list[DeviceReport]

    @property
    def non_compliant(self) -> list[DeviceReport]:
        return [report for report in self.reports if not report.compliant]

    @property
    def findings(self) -> list[tuple[str, Finding]]:
        """
        (device, finding), the most severe first
        """
        findings = [(report.device, finding) for report in self.reports for finding in report.findings]
        return sorted(findings, key=lambda item: -item[1].severity.rank)

    @property
    def errors(self) -> list[tuple[str, str]]:
        """
        (device, reason) for each rule that could not run
        """
        return [(report.device, error) for report in self.reports for error in report.errors]

    def to_markdown(self, *, max_rows: int = 50) -> str:
        """
        Args:
            max_rows: Limit for each table. The findings table drops the least severe findings first
        """
        findings, errors = self.findings, self.errors
        lines = ["# Compliance report", ""]

        if not findings and not errors:
            lines.append(f"All **{len(self.reports)}** devices compliant.")
            return "\n".join(lines)

        with_findings = sum(bool(report.findings) for report in self.reports)
        not_checked = sum(bool(report.errors) for report in self.reports)
        lines.append(
            f"**{len(self.reports)}** devices checked: **{with_findings}** with findings "
            f"(**{len(findings)}** findings), **{not_checked}** not fully checked."
        )

        if findings:
            rows = [
                (device, finding.severity, finding.rule, finding.message, "; ".join(finding.lines))
                for device, finding in findings[:max_rows]
            ]
            lines += ["", "## Findings", "", *_table(["Device", "Severity", "Rule", "Message", "Config"], rows)]
            lines += _more(len(findings), max_rows)

        if errors:
            lines += ["", "## Not Checked", "", *_table(["Device", "Reason"], errors[:max_rows])]
            lines += _more(len(errors), max_rows)

        return "\n".join(lines)


def _more(total: int, shown: int) -> list[str]:
    return ["", f"_...and {total - shown} more._"] if total > shown else []


def _cell(value: object, limit: int = 120) -> str:
    text = " ".join(str(value).split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _table(headers: list[str], rows: Sequence[Sequence[object]]) -> list[str]:
    cells = [headers, *([_cell(value) for value in row] for row in rows)]
    widths = [max(len(row[i]) for row in cells) for i in range(len(headers))]

    def line(row: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + " |"

    return [line(cells[0]), line(["-" * width for width in widths]), *(line(row) for row in cells[1:])]
