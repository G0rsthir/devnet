import re
from typing import Literal

from compliance.cisco.evidence import RunningConfig
from compliance.core import Device, Evidence, Finding, NotApplicable, Regex, Rule


class ConfigMustContain(Rule):
    """
    Each line must be in the config

    Args:
        lines: Whole lines, without the indent
        section: Pattern of a top-level line, e.g. `^line vty`. Each section that matches must have
            the lines below it, at any depth. Without a section, the lines must be top-level lines
    """

    kind: Literal["config_must_contain"] = "config_must_contain"
    lines: tuple[str, ...]
    section: Regex | None = None

    async def check(self, device: Device, evidence: Evidence) -> list[Finding]:
        config = await evidence.get(RunningConfig)

        if self.section is None:
            present = {line.text for line in config.tree.top}
            missing = [line for line in self.lines if line not in present]
            return [self.finding(f"missing: {'; '.join(missing)}")] if missing else []

        sections = config.tree.find(self.section, top_level=True)
        if not sections:
            raise NotApplicable(f"no section matches {self.section}")
        findings = []
        for section in sections:
            present = {line.text for line in section.descendants()}
            missing = [line for line in self.lines if line not in present]
            if missing:
                findings.append(self.finding(f"{section.text}: missing: {'; '.join(missing)}", lines=[section.text]))
        return findings


class ConfigMustNotMatch(Rule):
    """
    No line of the config can match the pattern

    Args:
        pattern: Searched in each line, at any depth, without the indent
    """

    kind: Literal["config_must_not_match"] = "config_must_not_match"
    pattern: Regex

    async def check(self, device: Device, evidence: Evidence) -> list[Finding]:
        config = await evidence.get(RunningConfig)
        found = config.tree.find(self.pattern)
        if not found:
            return []
        return [self.finding(f"lines that match {self.pattern}: {len(found)}", lines=[line.path for line in found])]


class VrfHasImportMap(Rule):
    """
    A VRF must have an import map

    Args:
        vrf: Name of the VRF. The rule is skipped for a device without this VRF
        map_name: Name of the route map
    """

    kind: Literal["vrf_has_import_map"] = "vrf_has_import_map"
    vrf: str
    map_name: str

    async def check(self, device: Device, evidence: Evidence) -> list[Finding]:
        config = await evidence.get(RunningConfig)
        sections = config.tree.find(rf"^(?:ip vrf|vrf definition|vrf context) {re.escape(self.vrf)}$", top_level=True)
        if not sections:
            raise NotApplicable(f"vrf {self.vrf} is not defined")
        # Not a substring test: `import map MNG-OLD` is not `import map MNG`
        wanted = re.compile(rf"import map {re.escape(self.map_name)}(\s.*)?")
        return [
            self.finding(f"vrf {self.vrf}: no import map '{self.map_name}' configured", lines=[section.text])
            for section in sections
            if not any(wanted.fullmatch(line.text) for line in section.descendants())
        ]
