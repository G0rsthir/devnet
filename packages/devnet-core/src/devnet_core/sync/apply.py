from typing import Any, cast

from diffsync.diff import Diff, DiffElement
from diffsync.enum import DiffSyncActions, DiffSyncModelFlags

from devnet_core.logging import get_logger
from devnet_core.sync.adapter import DiffAsyncModel, SyncAdapter

logger = get_logger(__name__)


async def apply_diff(target: SyncAdapter, diff: Diff) -> None:
    """
    Write the changes of a diff to the target system

    The async version of DiffSync's sync_from with CONTINUE_ON_FAILURE: a change that fails is recorded
    on the target, the changes to that object's children are skipped, and the sync goes on with the next object.
    """
    for element in diff.get_children():
        await _apply(target, element, parent=None)


async def _apply(target: SyncAdapter, element: DiffElement, parent: DiffAsyncModel | None) -> None:
    model_class: type[DiffAsyncModel] = getattr(target, element.type)
    attrs = element.get_attrs_diffs().get("+", {})
    if element.action == DiffSyncActions.CREATE:
        model = model_class(**element.keys, **attrs, adapter=target)
    else:
        # The diff was computed from this store, so the object is in it
        model = cast(DiffAsyncModel, target.get(model_class, element.keys))

    # NATURAL_DELETION_ORDER: delete the children before their parent
    children_first = element.action == DiffSyncActions.DELETE and bool(
        model.model_flags & DiffSyncModelFlags.NATURAL_DELETION_ORDER
    )
    if children_first:
        await _apply_children(target, element, model)
    if element.action is not None and not await _write(target, element.action, model, attrs, parent):
        # As in DiffSync: the children of a failed object are skipped
        return
    if not children_first:
        await _apply_children(target, element, model)


async def _apply_children(target: SyncAdapter, element: DiffElement, model: DiffAsyncModel) -> None:
    for child in element.get_children():
        await _apply(target, child, parent=model)


async def _write(
    target: SyncAdapter, action: str, model: DiffAsyncModel, attrs: dict[str, Any], parent: DiffAsyncModel | None
) -> bool:
    """
    Write one change to the system, then to the store

    Returns:
        False if the change failed
    """
    change = f"{action} {model.get_type()} {model.get_unique_id()}"
    try:
        if action == DiffSyncActions.CREATE:
            await model.acreate()
        elif action == DiffSyncActions.UPDATE:
            await model.aupdate(attrs)
        else:
            await model.adelete()
    except Exception as e:
        target.failures.append(f"{change}: {e}")
        logger.error(f"{change} failed: {e}")
        return False
    target.applied[action] += 1
    logger.info(change)

    # Keep the store up to date with the system
    # A later write can look this object up
    if action == DiffSyncActions.CREATE:
        target.add(model)
        if parent is not None:
            parent.add_child(model)
    elif action == DiffSyncActions.UPDATE:
        for name, value in attrs.items():
            setattr(model, name, value)
    else:
        if parent is not None:
            parent.remove_child(model)
        target.remove(model)
    return True
