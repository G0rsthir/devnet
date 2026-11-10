from collections.abc import Sequence
from typing import Any

import anyio
from anyio import to_thread
from netutils.lib_mapper import PYATS_LIB_MAPPER_REVERSE

from compliance.device.cli import CliTarget
from devnet_core.exceptions import SystemConnectionError

# Old IOS images negotiate only these algorithms
LEGACY_SSH_OPTIONS = (
    "-o KexAlgorithms=+diffie-hellman-group1-sha1,diffie-hellman-group14-sha1 "
    "-o HostKeyAlgorithms=+ssh-rsa -o Ciphers=+aes128-cbc"
)


class PyatsCli:
    """
    DeviceCli adapter: a pyATS (unicon) session over SSH

    This module is the only place that imports pyATS. pyATS is not a dependency of the package:
    install `pyats`, `unicon` and `genie` in the environment that uses this adapter.

    Args:
        ssh_options: Extra options for the ssh command
        port_timeout: Seconds to wait for the TCP port before the session opens, so that an
            unreachable device fails fast. None: no check
    """

    def __init__(
        self,
        *,
        username: str,
        password: str,
        enable_password: str | None = None,
        ssh_options: str | None = LEGACY_SSH_OPTIONS,
        port_timeout: float | None = 3.0,
    ) -> None:
        self._username = username
        self._password = password
        self._enable_password = enable_password
        self._ssh_options = ssh_options
        self._port_timeout = port_timeout

    async def run(self, target: CliTarget, commands: Sequence[str]) -> list[str]:
        if self._port_timeout is not None and not await _port_open(target.host, target.port, self._port_timeout):
            raise SystemConnectionError(name=target.name, msg=f"{target.host}:{target.port} is unreachable")
        # pyATS is blocking code. If this call is cancelled, the thread still closes the session
        return await to_thread.run_sync(self._run, target, list(commands), abandon_on_cancel=True)

    def _run(self, target: CliTarget, commands: list[str]) -> list[str]:
        from genie.testbed import load  # type: ignore[import-not-found, unused-ignore]
        from unicon.core.errors import (  # type: ignore[import-not-found, unused-ignore]
            ConnectionError as UniconConnectionError,
        )
        from unicon.core.errors import SubCommandFailure  # type: ignore[import-not-found, unused-ignore]

        device = load({"devices": {target.name: self._testbed_entry(target)}}).devices[target.name]
        try:
            device.connect(
                log_stdout=False,
                learn_hostname=True,
                # The default enters config mode at each connect and sets `no logging console` and
                # `exec-timeout 0` on the console and on vty 0 4. This adapter only reads
                init_config_commands=[],
                # The default writes the session, with the config, to a file in /tmp that each user can read
                log_buffer=True,
            )
            return [device.execute(command) for command in commands]
        except UniconConnectionError as e:
            raise SystemConnectionError(name=target.name, msg=f"Unable to connect: {e}") from e
        except SubCommandFailure as e:
            raise SystemConnectionError(name=target.name, msg=f"Command failed: {e}") from e
        finally:
            if device.connected:
                device.disconnect()

    def _testbed_entry(self, target: CliTarget) -> dict[str, Any]:
        try:
            os = PYATS_LIB_MAPPER_REVERSE[target.network_os]
        except KeyError:
            raise SystemConnectionError(name=target.name, msg=f"pyATS has no OS for {target.network_os}") from None
        credentials = {"default": {"username": self._username, "password": self._password}}
        if self._enable_password:
            credentials["enable"] = {"password": self._enable_password}
        # The default waits 10 seconds after each disconnect
        settings = {"POST_DISCONNECT_WAIT_SEC": 0}
        return {
            "os": os,
            "type": "router",
            "credentials": credentials,
            "connections": {"cli": {**self._connection(target), "settings": settings}},
        }

    def _connection(self, target: CliTarget) -> dict[str, Any]:
        connection: dict[str, Any] = {"protocol": "ssh", "ip": target.host, "port": target.port}
        if self._ssh_options:
            connection["ssh_options"] = self._ssh_options
        return connection


async def _port_open(host: str, port: int, timeout: float) -> bool:
    try:
        with anyio.fail_after(timeout):
            stream = await anyio.connect_tcp(host, port)
    except (TimeoutError, OSError):
        return False
    await stream.aclose()
    return True
