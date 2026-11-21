# Sync

DiffSync is a utility library that can be used to compare and synchronize different datasets

[DiffSync](https://github.com/networktocode/diffsync)

In short: a **model** is one object. An **adapter** holds all the objects of one system. `run_sync()` compares two adapters and writes the difference through the models of the target.

## Model

A sync has two kinds of model:

- **Contract model**, e.g. `Vlan`: a `DiffAsyncModel` subclass. The source uses it as it is
- **Target model**, e.g. `RemoteVlan`: a subclass of the contract model. It adds a field for the ID in the target system, and writes the hooks

The `_modelname` must be the same in both adapters. DiffSync pairs the two sides by this name

```text
DiffAsyncModel
└── Vlan              contract model, used by the source
    └── RemoteVlan    target model: writes to the target
```

## Adapter

An adapter holds the objects of one system for one run, in memory.
A sync has two adapters: the source and target

`top_level` lists the types without a parent. DiffSync finds the children through their parent

## Example

```python
from typing import Any, ClassVar, cast

from devnet_core.sync import DiffAsyncModel, SyncAdapter, run_sync


# Contract model: both sides use it
class Vlan(DiffAsyncModel):
    # Name of the type
    _modelname: ClassVar[str] = "vlan"

    # The fields that identify an object, like a primary key. Names that both systems know
    _identifiers: ClassVar[tuple[str, ...]] = ("vid",)

    # The fields that are compared
    _attributes: ClassVar[tuple[str, ...]] = ("name",)

    vid: int
    name: str = ""


# Source adapter: the VLANs that must exist
class VlanSource(SyncAdapter):
    vlan = Vlan
    top_level = ["vlan"]

    def __init__(self, vlans: dict[int, str]) -> None:
        super().__init__(name="source")
        self.vlans = vlans

    async def aload(self) -> None:
        for vid, name in self.vlans.items():
            self.add(Vlan(vid=vid, name=name))


# Target model: the contract model, the ID in the target system and the writes
class RemoteVlan(Vlan):
    # Not in _attributes, so it is not compared
    pk: int | None = None

    # A model reaches its system through its adapter
    @property
    def api(self) -> VlanApi:
        return cast(VlanTarget, self.adapter).api

    async def acreate(self) -> None:
        """
        Create the object in the remote system. Keep its ID on `self`
        """
        self.pk = await self.api.create(vid=self.vid, name=self.name)

    async def aupdate(self, attrs: dict[str, Any]) -> None:
        """
        Update the object in the remote system. `attrs` is the changed attributes
        """
        await self.api.update(self.pk, attrs)

    async def adelete(self) -> None:
        """
        Delete the object in the remote system
        """
        await self.api.delete(self.pk)


# Target adapter: the VLANs that exist now
class VlanTarget(SyncAdapter):
    vlan = RemoteVlan
    top_level = ["vlan"]

    def __init__(self, api: VlanApi) -> None:
        super().__init__(name="target")
        self.api = api

    async def aload(self) -> None:
        for row in await self.api.list():
            self.add(RemoteVlan(vid=row["vid"], name=row["name"], pk=row["id"]))
```

Run it. The target has VLAN 10 `staff` and VLAN 30 `old`:

```python
# Dry run: computes the changes and writes nothing
report = await run_sync(VlanSource({10: "users", 20: "voice"}), VlanTarget(api))
print(report.summary())  # DRY-RUN source -> target: create=1 update=1 delete=1 failed=0 warnings=0
print(report.diff)

# Real run, with new adapters
report = await run_sync(VlanSource({10: "users", 20: "voice"}), VlanTarget(api), dry_run=False)
print(report.summary())  # source -> target: create=1 update=1 delete=1 failed=0 warnings=0
```

## Rules

- A hook finds other objects in its adapter, e.g. the ID of its parent. See `NetboxIPAddress.acreate()` in [netbox.py](../../../../domain-ingest/src/domain_ingest/device/netbox.py)

- Flags (`DiffSyncModelFlags`) exclude objects or change the order of the deletes: `IGNORE`, `SKIP_UNMATCHED_SRC`, `NATURAL_DELETION_ORDER`. See [the plan](../../../../../docs/plans/ingest-framework.md#rules)
- A `Diff` subclass sets the order of the changes: `run_sync(..., diff_class=DeviceDiff)`
