"""
Rules come from the config file. This is also the whole feature, end to end
"""

from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from fakes import IOS_XE, NXOS, device, netbox_client
from pydantic import ValidationError

from compliance.cisco import ConfigMustContain, FileConfigSource, VrfHasImportMap
from compliance.config import ComplianceConfig
from compliance.core import AnySource, ComplianceRun, Severity, check_device
from compliance.netbox import NetboxDeviceSource

pytestmark = pytest.mark.anyio

# The `compliance` section of devnet.yaml
CONFIG = r"""
rules:
  - name: mng-vrf-import-map
    kind: vrf_has_import_map
    vrf: mng
    map_name: MNG
    scope:
      roles: [wan-core-router, wan-router]

  - name: vty-ssh-only
    kind: config_must_contain
    description: Remote access is SSH only
    severity: error
    section: ^line vty
    lines:
      - transport input ssh
    scope:
      platforms: [ios, iosxe]

  - name: no-http-server
    kind: config_must_not_match
    severity: critical
    pattern: ^ip http server$

  - name: netbox-required-fields
    kind: netbox_must_have
    fields: [primary_ip4, serial, tenant]

  - name: ntp-servers
    kind: config_must_contain_netbox
    netbox_field: config_context.ntp_servers
    line: ntp server {value}
"""

NETBOX: dict[int, dict[str, Any]] = {
    1: {"name": "wan-rt1", "serial": "FOC1", "tenant": None, "primary_ip4": {"address": "192.0.2.1/32"}},
    2: {"name": "dc-sw1", "serial": "FOC2", "tenant": {"slug": "it"}, "primary_ip4": {"address": "192.0.2.2/32"}},
    3: {"name": "dc-sw2", "serial": "FOC3", "tenant": {"slug": "it"}, "primary_ip4": {"address": "192.0.2.3/32"}},
}
for record in NETBOX.values():
    record["config_context"] = {"ntp_servers": ["10.0.0.10", "10.0.0.11"]}


def load(text: str) -> ComplianceConfig:
    return ComplianceConfig.model_validate(yaml.safe_load(text))


def test_kind_selects_the_rule_class() -> None:
    rules = load(CONFIG).rules

    assert isinstance(rules[0], VrfHasImportMap)
    assert rules[0].scope.roles == {"wan-core-router", "wan-router"}
    assert isinstance(rules[1], ConfigMustContain)
    assert rules[1].severity == Severity.ERROR


@pytest.mark.parametrize(
    ("rule", "error"),
    [
        ("{name: a, kind: no_such_kind}", "does not match any of the expected tags"),
        ("{name: a, kind: vrf_has_import_map, vrf: mng}", "map_name"),
        ("{name: a, kind: vrf_has_import_map, vrf: mng, map_name: MNG, typo: 1}", "Extra inputs are not permitted"),
        ("{name: a, kind: config_must_not_match, pattern: '('}", "not a regular expression"),
        ("{name: a, kind: config_must_contain_netbox, netbox_field: f, line: ntp server}", "must contain {value}"),
    ],
)
def test_bad_rule_fails_when_the_config_loads(rule: str, error: str) -> None:
    with pytest.raises(ValidationError, match=error):
        load(f"rules: [{rule}]")


def test_rule_names_are_unique() -> None:
    rule = "{name: a, kind: config_must_not_match, pattern: x}"

    with pytest.raises(ValidationError, match="rule names must be unique: a"):
        load(f"rules: [{rule}, {rule}]")


async def test_run_report(tmp_path: Path) -> None:
    (tmp_path / "wan-rt1.cfg").write_text(IOS_XE)
    (tmp_path / "dc-sw1.cfg").write_text(NXOS)
    devices = [
        device("wan-rt1", id=1, platform="iosxe", role="wan-router"),
        device("dc-sw1", id=2, platform="nxos", role="dc-switch"),
        # No config file: the device is "unreachable"
        device("dc-sw2", id=3, platform="nxos", role="dc-switch"),
    ]
    rules = load(CONFIG).rules

    async with netbox_client(NETBOX) as client:
        sources: list[AnySource] = [FileConfigSource(tmp_path), NetboxDeviceSource(client)]
        run = ComplianceRun(reports=[await check_device(each, rules, sources) for each in devices])

    assert [report.summary() for report in run.reports] == [
        "wan-rt1 compliance: passed=1 failed=4 skipped=0 error=0 findings=4",
        "dc-sw1 compliance: passed=3 failed=0 skipped=2 error=0 findings=0",
        "dc-sw2 compliance: passed=1 failed=0 skipped=2 error=2 findings=0",
    ]
    assert run.to_markdown() == EXPECTED_REPORT


EXPECTED_REPORT = """\
# Compliance report

**3** devices checked: **1** with findings (**4** findings), **1** not fully checked.

## Findings

| Device  | Severity | Rule                   | Message                                     | Config         |
| ------- | -------- | ---------------------- | ------------------------------------------- | -------------- |
| wan-rt1 | critical | no-http-server         | lines that match ^ip http server$: 1        | ip http server |
| wan-rt1 | error    | vty-ssh-only           | line vty 5 15: missing: transport input ssh | line vty 5 15  |
| wan-rt1 | warning  | netbox-required-fields | NetBox has no value for: tenant             |                |
| wan-rt1 | warning  | ntp-servers            | missing: ntp server 10.0.0.11               |                |

## Not Checked

| Device | Reason                                             |
| ------ | -------------------------------------------------- |
| dc-sw2 | RunningConfig: no config file dc-sw2.cfg (2 rules) |"""
