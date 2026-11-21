# Sync

[DiffSync](https://github.com/networktocode/diffsync) is a utility library that can be used to compare and synchronize different datasets

In short: a **model** is one object. An **adapter** holds all the objects of one system. `run_sync()` compares two adapters and writes the difference to the target

Flags (`DiffSyncModelFlags`) exclude objects or change the order of the deletes

## Model

A sync has two kinds of model:

- **Contract model**, shared fields and logic by both systems
- **Target/Source model**, a subclass of the contract model. It has system-specific fields and logic, like the ID and writes to the system

The `_modelname` must be the same in both adapters. DiffSync pairs the two sides by this name

## Adapter

An adapter holds the objects of one system for one run, in memory.
A sync has two adapters: the source and target

`top_level` lists the types without a parent. DiffSync finds the children through their parent

A hook can raise `ChangeRejected` when its object can't be written. The sync records the failure in the report, skips the object's children and goes on.

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


# Source adapter
class VlanSource(SyncAdapter):
    vlan = Vlan
    top_level = ["vlan"]

    def __init__(self, vlans: dict[int, str]) -> None:
        super().__init__(name="source")
        self.vlans = vlans

    async def aload(self) -> None:
        for vid, name in self.vlans.items():
            self.add(Vlan(vid=vid, name=name))


# Target model
class RemoteVlan(Vlan):
    # Not in _attributes, so it is not compared
    pk: int | None = None

    @property
    def api(self) -> VlanApi:
        """
        Return the API of the adapter, for writing to the system
        """
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


# Target adapter
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

Run it

```python
# Dry run
report = await run_sync(VlanSource({10: "users", 20: "voice"}), VlanTarget(api))
print(report.diff)

# Real run
report = await run_sync(VlanSource({10: "users", 20: "voice"}), VlanTarget(api), dry_run=False)
print(report.summary())  # source -> target: create=1 update=1 delete=1 failed=0 warnings=0
```
