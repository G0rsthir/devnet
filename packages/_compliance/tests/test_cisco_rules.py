import pytest
from fakes import IOS_XE, NXOS, FakeCli, device

from compliance.cisco import (
    CliConfigSource,
    ConfigMustContain,
    ConfigMustNotMatch,
    ConfigTree,
    VrfHasImportMap,
)
from compliance.core import DeviceReport, Outcome, Rule, check_device

pytestmark = pytest.mark.anyio

RT1 = device("wan-rt1", platform="iosxe")
SW1 = device("dc-sw1", platform="nxos")


async def check(rule: Rule, *, on: str = "wan-rt1") -> DeviceReport:
    cli = FakeCli({"wan-rt1": IOS_XE, "dc-sw1": NXOS})
    return await check_device(RT1 if on == "wan-rt1" else SW1, [rule], [CliConfigSource(cli)])


def test_config_tree_has_sections_and_no_comments() -> None:
    tree = ConfigTree(IOS_XE, network_os="cisco_xe")

    (vty,) = tree.find(r"^line vty 0 4$", top_level=True)
    assert [line.text for line in vty.children] == ["exec-timeout 10 0", "transport input ssh"]
    (import_map,) = tree.find(r"^import map MNG$")
    assert import_map.path == "vrf definition mng > address-family ipv4 > import map MNG"
    assert not tree.find(r"^!")


def test_config_tree_does_not_search_the_text_of_a_banner() -> None:
    tree = ConfigTree(IOS_XE, network_os="cisco_xe")

    assert not tree.find(r"Telnet is not permitted")
    (banner,) = tree.find(r"^banner motd")
    assert banner.children[0].text.startswith("Authorized access only. Telnet is not permitted.")


async def test_must_contain_top_level_lines() -> None:
    passed = await check(ConfigMustContain(name="encrypt", lines=("service password-encryption",)))
    failed = await check(ConfigMustContain(name="aaa", lines=("service password-encryption", "aaa new-model")))

    assert passed.compliant
    assert [finding.message for finding in failed.findings] == ["missing: aaa new-model"]


async def test_must_contain_checks_each_section_that_matches() -> None:
    rule = ConfigMustContain(name="vty-ssh-only", section=r"^line vty", lines=("transport input ssh",))

    report = await check(rule)

    assert [(finding.message, finding.lines) for finding in report.findings] == [
        ("line vty 5 15: missing: transport input ssh", ("line vty 5 15",))
    ]


async def test_must_contain_finds_a_line_at_any_depth_below_the_section() -> None:
    # `import map MNG` is below `address-family ipv4`. The vrf `guest` has a different map
    rule = ConfigMustContain(name="vrf-import", section=r"^vrf definition", lines=("import map MNG",))

    report = await check(rule)

    assert [finding.message for finding in report.findings] == ["vrf definition guest: missing: import map MNG"]


async def test_must_contain_without_a_matching_section_is_skipped() -> None:
    report = await check(ConfigMustContain(name="bgp", section=r"^router bgp", lines=("bgp log-neighbor-changes",)))

    assert report.results[0].outcome == Outcome.SKIPPED
    assert report.results[0].detail == "no section matches ^router bgp"


async def test_must_not_match_shows_the_lines_with_their_parents() -> None:
    report = await check(ConfigMustNotMatch(name="no-telnet", pattern=r"^transport input .*telnet"))

    (finding,) = report.findings
    assert finding.message == "lines that match ^transport input .*telnet: 1"
    assert finding.lines == ("line vty 5 15 > transport input telnet ssh",)
    assert (await check(ConfigMustNotMatch(name="no-finger", pattern=r"^ip finger"))).compliant


@pytest.mark.parametrize("on", ["wan-rt1", "dc-sw1"])
async def test_vrf_has_import_map(on: str) -> None:
    report = await check(VrfHasImportMap(name="mng-import", vrf="mng", map_name="MNG"), on=on)

    assert report.compliant
    assert report.results[0].outcome == Outcome.PASSED


async def test_vrf_import_map_with_a_longer_name_is_not_the_map() -> None:
    # The old rule tested `"import map MNG" in line`, so MNG-OLD passed
    report = await check(VrfHasImportMap(name="guest-import", vrf="guest", map_name="MNG"))

    assert [finding.message for finding in report.findings] == ["vrf guest: no import map 'MNG' configured"]
    assert report.findings[0].lines == ("vrf definition guest",)


async def test_vrf_that_is_not_defined_is_skipped() -> None:
    report = await check(VrfHasImportMap(name="voice-import", vrf="voice", map_name="MNG"))

    assert report.compliant
    assert report.results[0].detail == "vrf voice is not defined"
