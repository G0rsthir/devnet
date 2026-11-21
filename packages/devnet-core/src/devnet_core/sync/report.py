from dataclasses import dataclass, field


@dataclass(kw_only=True)
class SyncReport:
    """
    Result of one sync run
    """

    source: str
    target: str
    dry_run: bool

    # Number of changes in the diff, by action: create, update, delete, no-change
    planned: dict[str, int] = field(default_factory=dict)

    # Number of changes written, by action. Empty for a dry run
    applied: dict[str, int] = field(default_factory=dict)

    # List of failed operations
    failures: list[str] = field(default_factory=list)

    # List of warnings
    warnings: list[str] = field(default_factory=list)

    # The diff as text, for logs and reports
    diff: str = ""

    @property
    def ok(self) -> bool:
        return not self.failures

    def summary(self) -> str:
        counts = self.planned if self.dry_run else self.applied
        changes = " ".join(f"{action}={counts.get(action, 0)}" for action in ("create", "update", "delete"))
        prefix = "DRY-RUN " if self.dry_run else ""
        return f"{prefix}{self.source} -> {self.target}: {changes} failed={len(self.failures)} warnings={len(self.warnings)}"
