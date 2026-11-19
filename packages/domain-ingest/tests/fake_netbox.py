import itertools
import json
from collections import defaultdict
from typing import Any

import httpx2

from system_netbox.client import NetboxClient
from system_netbox.config import NetboxConfig

# Fields that NetBox takes as a value and returns as an object
_CHOICES = {"type", "status", "role"}
_RELATED = {"device": "devices", "parent": "interfaces", "vrf": "vrfs", "primary_mac_address": "mac-addresses"}


class FakeNetbox:
    """
    The part of the NetBox REST API that the device import uses, in memory

    It is not NetBox: it has no validation. It answers list, get, create, update and delete,
    and deletes the addresses of a deleted interface, as NetBox does.
    """

    def __init__(self) -> None:
        # table -> id -> row, as NetBox returns it
        self.rows: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
        # "POST interfaces", "PATCH devices", ...
        self.writes: list[str] = []
        # A create with one of these names gets a 400
        self.reject_names: set[str] = set()
        self._ids = itertools.count(1)

    def client(self) -> NetboxClient:
        config = NetboxConfig(base_url="http://netbox.test", token="${NETBOX_TOKEN}")  # type: ignore[arg-type]
        return NetboxClient(config, transport=httpx2.MockTransport(self._handle))

    def add(self, table: str, **data: Any) -> int:
        """
        Add a row. `data` is what a client sends in a create
        """
        row = {"id": next(self._ids), **self._as_returned(data)}
        self.rows[table][row["id"]] = row
        return row["id"]

    def find(self, table: str, **match: Any) -> dict[str, Any]:
        (row,) = [row for row in self.rows[table].values() if all(row.get(k) == v for k, v in match.items())]
        return row

    def _as_returned(self, data: dict[str, Any]) -> dict[str, Any]:
        row: dict[str, Any] = {}
        for key, value in data.items():
            if value is not None and key in _CHOICES:
                row[key] = {"value": value}
            elif value is not None and key in _RELATED:
                row[key] = {"id": value, "name": self.rows[_RELATED[key]][value].get("name", "")}
            else:
                row[key] = value
        return row

    def _device_id(self, table: str, row: dict[str, Any]) -> int | None:
        if table == "interfaces":
            return row["device"]["id"]
        interface = self.rows["interfaces"].get(row.get("assigned_object_id", 0))
        return interface["device"]["id"] if interface else None

    def _handle(self, request: httpx2.Request) -> httpx2.Response:
        # /api/dcim/interfaces/5/
        _, _, table, *rest = request.url.path.strip("/").split("/")
        rows = self.rows[table]
        if request.method != "GET":
            self.writes.append(f"{request.method} {table}")

        if not rest:
            if request.method == "GET":
                device_id = request.url.params.get("device_id")
                results = [
                    row for row in rows.values() if device_id is None or self._device_id(table, row) == int(device_id)
                ]
                return httpx2.Response(200, json={"results": results, "next": None})
            data = json.loads(request.content)
            if data.get("name") in self.reject_names:
                return httpx2.Response(400, json={"name": ["Rejected by the test."]})
            return httpx2.Response(201, json=rows[self.add(table, **data)])

        row_id = int(rest[0])
        if row_id not in rows:
            return httpx2.Response(404, json={"detail": "Not found."})

        if request.method == "GET":
            return httpx2.Response(200, json=rows[row_id])

        if request.method == "PATCH":
            rows[row_id].update(self._as_returned(json.loads(request.content)))
            return httpx2.Response(200, json=rows[row_id])

        if request.method == "DELETE":
            del rows[row_id]
            if table == "interfaces":
                for addresses in (self.rows["ip-addresses"], self.rows["mac-addresses"]):
                    for address_id in [i for i, row in addresses.items() if row.get("assigned_object_id") == row_id]:
                        del addresses[address_id]
            return httpx2.Response(204)

        return httpx2.Response(405)
