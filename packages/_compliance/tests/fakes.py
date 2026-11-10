from collections.abc import Sequence
from typing import Any

import httpx2

from compliance.core import Device
from compliance.device import CliTarget
from devnet_core.exceptions import SystemConnectionError
from system_netbox.client import NetboxClient
from system_netbox.config import NetboxConfig

IOS_XE = """\
Building configuration...

Current configuration : 1804 bytes
!
version 17.9
service password-encryption
!
hostname wan-rt1
!
vrf definition mng
 rd 65000:1
 !
 address-family ipv4
  import map MNG
 exit-address-family
!
vrf definition guest
 rd 65000:2
 !
 address-family ipv4
  import map MNG-OLD
 exit-address-family
!
interface GigabitEthernet0/0/0
 description uplink
 vrf forwarding mng
 ip address 10.0.0.1 255.255.255.0
!
ip http server
snmp-server community public RO
ntp server 10.0.0.10
!
banner motd ^C
 Authorized access only. Telnet is not permitted.
^C
!
line vty 0 4
 exec-timeout 10 0
 transport input ssh
line vty 5 15
 transport input telnet ssh
!
end
"""

NXOS = """\
!Command: show running-config
version 10.3(4a)
hostname dc-sw1
vrf context mng
  address-family ipv4 unicast
    import map MNG
ntp server 10.0.0.10
ntp server 10.0.0.11
line vty
  exec-timeout 10
"""


def device(name: str = "wan-rt1", **fields: Any) -> Device:
    defaults: dict[str, Any] = {"id": 1, "platform": "iosxe", "role": "wan-router", "primary_ip": "192.0.2.1"}
    return Device(name=name, **{**defaults, **fields})


class FakeCli:
    """
    DeviceCli adapter for tests: the output of a device is a string

    A device without an output is unreachable.
    """

    def __init__(self, outputs: dict[str, str]) -> None:
        self.outputs = outputs
        # (device, commands) of each session
        self.sessions: list[tuple[str, list[str]]] = []

    async def run(self, target: CliTarget, commands: Sequence[str]) -> list[str]:
        self.sessions.append((target.name, list(commands)))
        if target.name not in self.outputs:
            raise SystemConnectionError(name=target.name, msg="Connection timed out")
        return [self.outputs[target.name] for _ in commands]


def netbox_client(devices: dict[int, dict[str, Any]]) -> NetboxClient:
    """
    The real NetboxClient. `GET /api/dcim/devices/{id}/` answers from `devices`. Needs NETBOX_TOKEN
    """

    def handle(request: httpx2.Request) -> httpx2.Response:
        device_id = int(request.url.path.strip("/").split("/")[-1])
        if request.method != "GET" or device_id not in devices:
            return httpx2.Response(404, json={"detail": "Not found."})
        return httpx2.Response(200, json={"id": device_id, **devices[device_id]})

    config = NetboxConfig(base_url="http://netbox.test", token="${NETBOX_TOKEN}")  # type: ignore[arg-type]
    return NetboxClient(config, transport=httpx2.MockTransport(handle))
