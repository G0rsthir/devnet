from diffsync.diff import Diff
from diffsync.enum import DiffSyncFlags

from devnet_core.sync.adapter import SyncAdapter
from devnet_core.sync.apply import apply_diff
from devnet_core.sync.logging import configure_logging
from devnet_core.sync.report import SyncReport

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
    Synchronize two adapters and return a report

    Args:
        dry_run: Compute the diff and write nothing
        max_delete_fraction: Block the deletes if they are more than this part of the target's objects
        diff_class: Diff subclass that sets the order of the changes
    """
    configure_logging()

    await source.aload()
    await target.aload()

    diff = target.diff_from(source, diff_class=diff_class)
    warnings = [*source.problems, *target.problems]

    # A collection that failed without an error looks the same as "everything was removed"
    deletes = diff.summary()["delete"]
    if deletes and (source.empty or deletes > max_delete_fraction * len(target)):
        diff = target.diff_from(source, diff_class=diff_class, flags=DiffSyncFlags.SKIP_UNMATCHED_DST)
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
        await apply_diff(target, diff)
        report.applied = dict(target.applied)
        report.failures = list(target.failures)

    return report
