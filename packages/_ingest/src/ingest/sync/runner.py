from functools import partial

from anyio import to_thread
from diffsync.diff import Diff
from diffsync.enum import DiffSyncFlags

from devnet_core.logging import get_logger
from ingest.sync.adapter import SyncAdapter
from ingest.sync.logging import configure_logging
from ingest.sync.report import SyncReport

logger = get_logger(__name__)

_ACTIONS = ("create", "update", "delete", "no-change")


async def run_sync(
    source: SyncAdapter,
    target: SyncAdapter,
    *,
    dry_run: bool = True,
    max_delete_fraction: float = 0.5,
    diff_class: type[Diff] = Diff,
) -> SyncReport:
    """
    Make the target match the source: load both, diff, check the deletes, apply

    Args:
        dry_run: Compute the diff and write nothing
        max_delete_fraction: Block the deletes if they are more than this part of the target's objects
        diff_class: Diff subclass that sets the order of the changes
    """
    configure_logging()

    await source.aload()
    await target.aload()

    # One object that fails must not stop the others
    flags = DiffSyncFlags.CONTINUE_ON_FAILURE
    diff = target.diff_from(source, diff_class=diff_class, flags=flags)
    warnings = [*source.problems, *target.problems]

    # A collection that failed without an error looks the same as "everything was removed"
    deletes = diff.summary()["delete"]
    if deletes and (source.empty or deletes > max_delete_fraction * len(target)):
        flags |= DiffSyncFlags.SKIP_UNMATCHED_DST
        diff = target.diff_from(source, diff_class=diff_class, flags=flags)
        warnings.append(f"{deletes} of {len(target)} objects would be deleted: deletes blocked")

    summary = diff.summary()
    report = SyncReport(
        source=str(source.name),
        target=str(target.name),
        dry_run=dry_run,
        planned={action: summary[action] for action in _ACTIONS},
        warnings=warnings,
        diff=diff.str(),
    )

    if not dry_run and diff.has_diffs():
        # DiffSync's sync is blocking code. It runs in a worker thread, and RemoteModel
        # sends each write back to this event loop
        try:
            await to_thread.run_sync(partial(target.sync_from, source, diff_class=diff_class, flags=flags, diff=diff))
        finally:
            # A cancelled await does not stop the thread. This does, before its next write
            target.closed = True
        report.applied = dict(target.applied)
        report.failures = list(target.failures)

    logger.info(report.summary())
    return report
