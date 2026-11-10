from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Coroutine
from typing import Any, Self, cast

from anyio import from_thread
from diffsync import Adapter, DiffSyncModel
from diffsync.enum import DiffSyncStatus
from diffsync.exceptions import ObjectCrudException


class SyncAdapter(Adapter):
    """
    One side of a sync: the models of one system, for one scope (e.g. one device)

    DiffSync never calls a load method itself, so aload can be async
    """

    def __init__(self, *, name: str) -> None:
        super().__init__(name=name)
        # True if the system returned no data. The runner then blocks deletes
        self.empty = False
        # Data that could not be loaded, e.g. "Gi0/1: VRF 'x' has no mapping". Shown in the report
        self.problems: list[str] = []
        # Filled by RemoteModel during a sync
        self.applied: Counter[str] = Counter()
        self.failures: list[str] = []
        # Set by the runner when the run ends. A worker thread that is still alive then stops writing
        self.closed = False

    async def aload(self) -> None:
        """
        Read the system and add its models to the store
        """
        raise NotImplementedError


class RemoteModel(DiffSyncModel):
    """
    Model of a system that devnet writes to

    DiffSync calls create, update and delete from a worker thread. They run the async hooks below
    on the event loop and record the result on the adapter. A subclass writes only the hooks.
    A hook that raises fails that object and its children. The sync continues with the next object.
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
            attrs: Only the attributes that differ, with their new values. self still has the old ones
        """
        raise NotImplementedError(f"{type(self).__name__} does not support update")

    async def adelete(self) -> None:
        raise NotImplementedError(f"{type(self).__name__} does not support delete")

    @classmethod
    def create(cls, adapter: Adapter, ids: dict[str, Any], attrs: dict[str, Any]) -> Self | None:
        model = cls(**ids, **attrs, adapter=adapter)
        model._apply("create", model.acreate)
        model.set_status(DiffSyncStatus.SUCCESS, "Created")
        return model

    def update(self, attrs: dict[str, Any]) -> Self | None:
        self._apply("update", self.aupdate, attrs)
        return super().update(attrs)

    def delete(self) -> Self | None:
        self._apply("delete", self.adelete)
        return super().delete()

    def _apply(self, action: str, hook: Callable[..., Coroutine[Any, Any, None]], *args: Any) -> None:
        adapter = cast(SyncAdapter, self.adapter)
        if adapter.closed:
            # Not an ObjectCrudException: it ends the whole sync, not only this object
            raise RuntimeError("the sync run was cancelled")
        try:
            from_thread.run(hook, *args)
        except Exception as e:
            adapter.failures.append(f"{action} {self.get_type()} {self.get_unique_id()}: {e}")
            # The only exception that DiffSync's CONTINUE_ON_FAILURE catches
            raise ObjectCrudException(str(e)) from e
        adapter.applied[action] += 1
