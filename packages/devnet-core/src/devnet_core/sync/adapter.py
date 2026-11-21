from __future__ import annotations

from collections import Counter
from typing import Any, NoReturn

from diffsync import Adapter, DiffSyncModel


class SyncAdapter(Adapter):
    """
    Holds the objects of one system
    """

    def __init__(self, *, name: str) -> None:
        super().__init__(name=name)

        # True if the system returned no data. The runner then blocks deletes
        self.empty = False

        # Data that could not be loaded
        self.problems: list[str] = []

        # Filled by apply_diff during a sync
        self.applied: Counter[str] = Counter()

        # Filled by apply_diff during a sync
        self.failures: list[str] = []

    async def aload(self) -> None:
        """
        Read the system and add its models to the store

        Use `self.add(model)` and `parent.add_child(child)` to build the hierarchy
        """
        raise NotImplementedError


class DiffAsyncModel(DiffSyncModel):
    """
    Base of every DiffSync's model

    This class is a Pydantic model
    """

    async def acreate(self) -> None:
        """
        Create this object in the system and keep its ID on self
        """
        raise NotImplementedError(f"{type(self).__name__} does not support create")

    async def aupdate(self, attrs: dict[str, Any]) -> None:
        """
        Write the changed attributes to the system

        Args:
            attrs: Only the attributes that differ, self still has the old ones
        """
        raise NotImplementedError(f"{type(self).__name__} does not support update")

    async def adelete(self) -> None:
        raise NotImplementedError(f"{type(self).__name__} does not support delete")

    @classmethod
    def create(cls, adapter: Adapter, ids: dict[str, Any], attrs: dict[str, Any]) -> NoReturn:
        _use_apply_diff()

    def update(self, attrs: dict[str, Any]) -> NoReturn:
        _use_apply_diff()

    def delete(self) -> NoReturn:
        _use_apply_diff()


class ChangeRejected(Exception):
    """
    Raise it from a hook when this object can't be written, but the rest of the sync can go on
    """


def _use_apply_diff() -> NoReturn:
    raise TypeError("a DiffAsyncModel is written by apply_diff, not by DiffSync's sync_from")
