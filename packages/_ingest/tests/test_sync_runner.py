"""
The sync framework with the smallest possible feature: named numbers, from one dict to another
"""

import asyncio
from typing import Any, ClassVar, cast

import pytest
from diffsync import DiffSyncModel

from ingest.sync import RemoteModel, SyncAdapter, run_sync

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class Item(DiffSyncModel):
    _modelname: ClassVar[str] = "item"
    _identifiers: ClassVar[tuple[str, ...]] = ("name",)
    _attributes: ClassVar[tuple[str, ...]] = ("value",)

    name: str
    value: int = 0


class Source(SyncAdapter):
    item = Item
    top_level = ["item"]

    def __init__(self, items: dict[str, int]) -> None:
        super().__init__(name="source")
        self.items = items

    async def aload(self) -> None:
        for name, value in self.items.items():
            self.add(Item(name=name, value=value))


class RemoteItem(RemoteModel, Item):
    @property
    def system(self) -> dict[str, int]:
        return cast(Target, self.adapter).system

    async def acreate(self) -> None:
        await asyncio.sleep(cast(Target, self.adapter).write_seconds)
        self.system[self.name] = self.value

    async def aupdate(self, attrs: dict[str, Any]) -> None:
        self.system[self.name] = attrs["value"]

    async def adelete(self) -> None:
        del self.system[self.name]


class Target(SyncAdapter):
    item = RemoteItem
    top_level = ["item"]

    def __init__(self, system: dict[str, int], *, write_seconds: float = 0) -> None:
        super().__init__(name="target")
        self.system = system
        self.write_seconds = write_seconds

    async def aload(self) -> None:
        for name, value in self.system.items():
            self.add(RemoteItem(name=name, value=value))


async def test_dry_run_is_the_default() -> None:
    system = {"a": 1, "b": 2, "c": 3}

    report = await run_sync(Source({"a": 1, "b": 20, "d": 4}), Target(system))

    assert report.planned == {"create": 1, "update": 1, "delete": 1, "no-change": 1}
    assert report.applied == {}
    assert system == {"a": 1, "b": 2, "c": 3}


async def test_sync_makes_the_target_match_the_source() -> None:
    system = {"a": 1, "b": 2, "c": 3}

    report = await run_sync(Source({"a": 1, "b": 20, "d": 4}), Target(system), dry_run=False)

    assert report.applied == {"create": 1, "update": 1, "delete": 1}
    assert system == {"a": 1, "b": 20, "d": 4}


async def test_mass_delete_is_blocked() -> None:
    system = {"a": 1, "b": 2, "c": 3}

    report = await run_sync(Source({"a": 10}), Target(system), dry_run=False)

    # The update is still applied
    assert system == {"a": 10, "b": 2, "c": 3}
    assert report.warnings == ["2 of 3 objects would be deleted: deletes blocked"]


async def test_cancelled_run_stops_writing() -> None:
    system: dict[str, int] = {}
    source = Source({f"item{i}": i for i in range(20)})

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(run_sync(source, Target(system, write_seconds=0.05), dry_run=False), timeout=0.12)

    written = len(system)
    await asyncio.sleep(0.2)
    # The write that was in progress can still finish
    assert len(system) <= written + 1 < 20
