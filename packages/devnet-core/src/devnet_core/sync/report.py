from dataclasses import dataclass, field


@dataclass(kw_only=True)
class SyncReport:
    """
    Result of one sync run

    Args:
        planned: Number of changes in the diff, by action: create, update, delete, no-change
        applied: Number of changes written, by action. Empty for a dry run
        failures: One line for each object that could not be written
        warnings: Things a person must look at, e.g. blocked deletes
        diff: The diff as text, for logs and reports
    """

    source: str
    target: str
    dry_run: bool
    planned: dict[str, int] = field(default_factory=dict)
    applied: dict[str, int] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    diff: str = ""

    @property
    def ok(self) -> bool:
        return not self.failures

    def summary(self) -> str:
        counts = self.planned if self.dry_run else self.applied
        changes = " ".join(f"{action}={counts.get(action, 0)}" for action in ("create", "update", "delete"))
        prefix = "DRY-RUN " if self.dry_run else ""
        return f"{prefix}{self.source} -> {self.target}: {changes} failed={len(self.failures)} warnings={len(self.warnings)}"
