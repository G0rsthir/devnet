"""
Ports and adapters: the rules do not change when the source of the config changes
"""

from pathlib import Path

import pytest
from fakes import IOS_XE, FakeCli, device

from compliance.cisco import CliConfigSource, ConfigMustNotMatch, FileConfigSource
from compliance.core import check_device

pytestmark = pytest.mark.anyio

RT1 = device("wan-rt1", platform="iosxe", primary_ip="192.0.2.1")
RULES = [
    ConfigMustNotMatch(name="no-http", pattern=r"^ip http server$"),
    ConfigMustNotMatch(name="no-public", pattern=r"^snmp-server community public\b"),
]


async def test_same_rules_same_result_from_the_device_and_from_a_file(tmp_path: Path) -> None:
    (tmp_path / "wan-rt1.cfg").write_text(IOS_XE)

    from_device = await check_device(RT1, RULES, [CliConfigSource(FakeCli({"wan-rt1": IOS_XE}))])
    from_file = await check_device(RT1, RULES, [FileConfigSource(tmp_path)])

    assert len(from_device.findings) == 2
    assert from_file.findings == from_device.findings


async def test_device_source_opens_one_session_for_all_rules() -> None:
    cli = FakeCli({"wan-rt1": IOS_XE})

    await check_device(RT1, RULES, [CliConfigSource(cli)])

    assert cli.sessions == [("wan-rt1", ["show running-config"])]


async def test_unreachable_device_is_in_the_report() -> None:
    report = await check_device(RT1, RULES, [CliConfigSource(FakeCli({}))])

    assert not report.compliant
    assert report.errors == ["RunningConfig: wan-rt1: Connection timed out (2 rules)"]


@pytest.mark.parametrize(
    ("fields", "reason"),
    [
        ({"primary_ip": None}, "RunningConfig: wan-rt1 has no primary IP in NetBox (2 rules)"),
        ({"platform": "junos"}, "RunningConfig: NetBox platform 'junos' has no network OS in PLATFORMS (2 rules)"),
    ],
)
async def test_device_that_netbox_does_not_describe_is_in_the_report(fields: dict[str, None], reason: str) -> None:
    cli = FakeCli({"wan-rt1": IOS_XE})

    report = await check_device(device("wan-rt1", **fields), RULES, [CliConfigSource(cli)])

    assert report.errors == [reason]
    assert cli.sessions == []


async def test_output_that_is_not_a_complete_config_is_an_error() -> None:
    cut_off = "hostname wan-rt1\nbanner motd ^C\nAuthorized access only.\n"

    empty = await check_device(RT1, RULES, [CliConfigSource(FakeCli({"wan-rt1": ""}))])
    partial = await check_device(RT1, RULES, [CliConfigSource(FakeCli({"wan-rt1": cut_off}))])

    assert empty.errors == ["RunningConfig: the config is empty (2 rules)"]
    assert partial.errors == ["RunningConfig: Unable to parse banner end. (2 rules)"]


async def test_file_source_without_a_file_is_an_error(tmp_path: Path) -> None:
    report = await check_device(RT1, RULES, [FileConfigSource(tmp_path)])

    assert report.errors == ["RunningConfig: no config file wan-rt1.cfg (2 rules)"]


async def test_file_source_reads_only_its_folder(tmp_path: Path) -> None:
    (tmp_path / "secret.cfg").write_text(IOS_XE)
    backups = tmp_path / "backups"
    backups.mkdir()

    report = await check_device(device("../secret"), RULES, [FileConfigSource(backups)])

    assert report.errors == ["RunningConfig: ../secret is not a valid file name (2 rules)"]
