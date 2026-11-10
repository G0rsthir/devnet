"""
The pyATS adapter against the mock device of unicon

pyATS is not a dependency of the workspace. Without it, the tests that open a session are skipped.
"""

import socket
import sys
import tempfile
from importlib.util import find_spec
from pathlib import Path
from typing import Any

import pytest

from compliance.cisco import CliConfigSource, ConfigMustNotMatch
from compliance.core import Device, check_device
from compliance.device import CliTarget
from compliance.device.pyats_cli import PyatsCli
from devnet_core.exceptions import SystemConnectionError

pytestmark = pytest.mark.anyio

needs_pyats = pytest.mark.skipif(find_spec("unicon") is None or find_spec("genie") is None, reason="needs pyATS")

MOCK_DATA = Path(__file__).parent / "mock_iosxe"
RT1 = CliTarget(name="wan-rt1", host="192.0.2.1", network_os="cisco_xe")


class MockPyatsCli(PyatsCli):
    """
    PyatsCli that starts the mock device of unicon in place of ssh
    """

    def __init__(self) -> None:
        super().__init__(username="user", password="password", port_timeout=None)

    def _connection(self, target: CliTarget) -> dict[str, Any]:
        mock_device = Path(sys.executable).parent / "mock_device_cli"
        return {
            "command": f"{mock_device} --os iosxe --mock_data_dir {MOCK_DATA} --state enable --hostname {target.name}"
        }


@needs_pyats
async def test_runs_the_commands_in_one_session() -> None:
    config, clock = await MockPyatsCli().run(RT1, ["show running-config", "show clock"])

    assert "hostname wan-rt1" in config
    assert clock == "10:11:12.000 UTC Tue Nov 10 2026"


@needs_pyats
async def test_session_does_not_change_the_config() -> None:
    # unicon's default enters config mode at connect and sets `exec-timeout 0` on vty 0 4
    (config,) = await MockPyatsCli().run(RT1, ["show running-config"])

    assert "exec-timeout 10 0" in config
    assert "exec-timeout 0 0" not in config


@needs_pyats
async def test_session_leaves_no_log_file() -> None:
    logs = Path(tempfile.gettempdir())
    before = set(logs.glob("wan-rt1-cli-*.log"))

    await MockPyatsCli().run(RT1, ["show running-config"])

    assert set(logs.glob("wan-rt1-cli-*.log")) == before


@needs_pyats
async def test_rejected_command_is_a_connection_error() -> None:
    with pytest.raises(SystemConnectionError, match="wan-rt1: Command failed"):
        await MockPyatsCli().run(RT1, ["show no-such-thing"])


@needs_pyats
async def test_rules_run_on_a_config_from_pyats() -> None:
    device = Device(id=1, name="wan-rt1", platform="iosxe", primary_ip="192.0.2.1")
    rule = ConfigMustNotMatch(name="no-http", pattern=r"^ip http server$")

    report = await check_device(device, [rule], [CliConfigSource(MockPyatsCli())])

    assert [finding.lines for finding in report.findings] == [("ip http server",)]


async def test_closed_port_fails_before_pyats_starts() -> None:
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    cli = PyatsCli(username="user", password="password", port_timeout=1.0)

    with pytest.raises(SystemConnectionError, match=f"wan-rt1: 127.0.0.1:{port} is unreachable"):
        await cli.run(CliTarget(name="wan-rt1", host="127.0.0.1", network_os="cisco_xe", port=port), ["show clock"])
