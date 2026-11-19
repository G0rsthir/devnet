import itertools
import json
from typing import Any

import httpx2

from system_ise.client import IseClient
from system_ise.config import IseConfig

_DEVICES = "/ers/config/networkdevice"
_VERSION = "/ers/config/op/systemconfig/iseversion"


class FakeIse:
    """
    The network devices of the ISE ERS API, in memory

    It is not ISE: it checks only that a name is unique. A filter is `<field>.EQ.<value>`.
    """

    def __init__(self) -> None:
        # id -> network device, as ISE returns it
        self.devices: dict[str, dict[str, Any]] = {}
        # "POST", "PATCH", "DELETE"
        self.writes: list[str] = []
        self._ids = itertools.count(1)

    def client(self) -> IseClient:
        config = IseConfig.model_validate(
            {"base_url": "https://ise.test", "username": "${ISE_USERNAME}", "password": "${ISE_PASSWORD}"}
        )
        return IseClient(config, transport=httpx2.MockTransport(self._handle))

    def add(self, **device: Any) -> str:
        device_id = f"ise-{next(self._ids)}"
        self.devices[device_id] = {"id": device_id, **device}
        return device_id

    def find(self, **match: Any) -> dict[str, Any]:
        (device,) = [device for device in self.devices.values() if all(device.get(k) == v for k, v in match.items())]
        return device

    def _handle(self, request: httpx2.Request) -> httpx2.Response:
        path = request.url.path
        if path == _VERSION:
            return httpx2.Response(
                200, json={"OperationResult": {"resultValue": [{"name": "version", "value": "3.3"}]}}
            )
        if request.method != "GET":
            self.writes.append(request.method)

        if path == _DEVICES:
            if request.method == "GET":
                return self._search(request)
            data = json.loads(request.content)["NetworkDevice"]
            if any(device["name"] == data["name"] for device in self.devices.values()):
                return _error(400, "Device name already exists")
            return httpx2.Response(201, headers={"Location": f"https://ise.test{_DEVICES}/{self.add(**data)}"})

        device_id = path.rsplit("/", 1)[-1]
        if device_id not in self.devices:
            return _error(404, "Resource not found")
        if request.method == "DELETE":
            del self.devices[device_id]
            return httpx2.Response(204)
        if request.method == "PATCH":
            self.devices[device_id].update(json.loads(request.content)["NetworkDevice"])
        return httpx2.Response(200, json={"NetworkDevice": self.devices[device_id]})

    def _search(self, request: httpx2.Request) -> httpx2.Response:
        found = list(self.devices.values())
        for expression in request.url.params.get_list("filter"):
            field, _, value = expression.split(".", 2)
            found = [device for device in found if device.get(field) == value]
        resources = [{"id": d["id"], "name": d["name"], "description": d.get("description")} for d in found]
        return httpx2.Response(200, json={"SearchResult": {"total": len(resources), "resources": resources}})


def _error(status: int, title: str) -> httpx2.Response:
    return httpx2.Response(status, json={"ERSResponse": {"messages": [{"title": title}]}})
