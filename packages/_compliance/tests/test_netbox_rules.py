from typing import Any

import pytest
from fakes import IOS_XE, NXOS, FakeCli, device, netbox_client

from compliance.cisco import CliConfigSource
from compliance.core import AnySource, DeviceReport, Outcome, Rule, check_device
from compliance.intent import ConfigMustContainNetbox
from compliance.netbox import NetboxDeviceSource, NetboxMustHave

pytestmark = pytest.mark.anyio

# What NetBox returns for a field that is not set: null, "" or an empty list
RT1: dict[str, Any] = {
    "name": "wan-rt1",
    "serial": "",
    "tenant": None,
    "primary_ip4": {"id": 7, "address": "192.0.2.1/32"},
    "tags": [],
    "custom_fields": {"owner": "netops"},
    "config_context": {"ntp_servers": ["10.0.0.10", "10.0.0.11"], "syslog_server": "10.0.0.20"},
}


async def check(rule: Rule, *, name: str = "wan-rt1", netbox: dict[str, Any] = RT1) -> DeviceReport:
    cli = FakeCli({"wan-rt1": IOS_XE, "dc-sw1": NXOS})
    platform = "iosxe" if name == "wan-rt1" else "nxos"
    async with netbox_client({1: netbox}) as client:
        sources: list[AnySource] = [NetboxDeviceSource(client), CliConfigSource(cli)]
        return await check_device(device(name, id=1, platform=platform), [rule], sources)


async def test_netbox_must_have_reports_the_empty_fields() -> None:
    rule = NetboxMustHave(name="required", fields=("primary_ip4", "serial", "tenant", "custom_fields.owner"))

    report = await check(rule)

    assert [finding.message for finding in report.findings] == ["NetBox has no value for: serial, tenant"]


async def test_netbox_rule_needs_no_session_to_the_device() -> None:
    cli = FakeCli({})
    async with netbox_client({1: RT1}) as client:
        rule = NetboxMustHave(name="owner", fields=("custom_fields.owner",))
        report = await check_device(device(), [rule], [NetboxDeviceSource(client), CliConfigSource(cli)])

    assert report.compliant
    assert cli.sessions == []


async def test_device_that_is_not_in_netbox_is_an_error() -> None:
    async with netbox_client({}) as client:
        rule = NetboxMustHave(name="owner", fields=("custom_fields.owner",))
        report = await check_device(device(), [rule], [NetboxDeviceSource(client)])

    assert report.errors == ["NetboxDeviceRecord: netbox: 404 Not Found. Not found."]


async def test_config_must_contain_a_line_for_each_netbox_value() -> None:
    rule = ConfigMustContainNetbox(name="ntp", netbox_field="config_context.ntp_servers", line="ntp server {value}")

    router = await check(rule)
    switch = await check(rule, name="dc-sw1")

    assert [finding.message for finding in router.findings] == ["missing: ntp server 10.0.0.11"]
    assert switch.compliant


async def test_netbox_value_can_be_one_value() -> None:
    rule = ConfigMustContainNetbox(
        name="syslog", netbox_field="config_context.syslog_server", line="logging host {value}"
    )

    report = await check(rule)

    assert [finding.message for finding in report.findings] == ["missing: logging host 10.0.0.20"]


async def test_rule_is_skipped_if_netbox_has_no_value() -> None:
    rule = ConfigMustContainNetbox(name="dns", netbox_field="config_context.dns_servers", line="ip name-server {value}")

    report = await check(rule)

    assert report.results[0].outcome == Outcome.SKIPPED
    assert report.results[0].detail == "NetBox has no value for config_context.dns_servers"
