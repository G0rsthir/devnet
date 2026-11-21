import traceback
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from prefect.states import Completed, State

from devnet_core.sync import SyncReport


@dataclass(frozen=True, kw_only=True)
class RunReport:
    """
    The report of a batch run, built from the states of its task runs: one task for each object

    Args:
        flow: The name of the flow, e.g. "ingest-devices". The key of its artifact
        total: The objects of the run
        failed: Object -> the error that stopped its task
        attention: Object -> the lines of its report that a person must read
    """

    flow: str
    dry_run: bool
    total: int
    failed: dict[str, str] = field(default_factory=dict)
    attention: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    async def from_states(
        cls, flow: str, names: Sequence[str], states: Sequence[State[Any]], *, dry_run: bool
    ) -> "RunReport":
        """
        Args:
            names: The name of each object, in the order of the states
            states: The final state of each task run, from `.map(..., return_state=True)`
        """
        failed: dict[str, str] = {}
        attention: dict[str, list[str]] = {}
        for name, state in zip(names, states, strict=True):
            if not state.is_completed():
                failed[name] = await _error(state)
            elif lines := _attention(await state.aresult()):
                attention[name] = lines
        return cls(flow=flow, dry_run=dry_run, total=len(names), failed=failed, attention=attention)

    @property
    def needs_attention(self) -> bool:
        """
        True if a person must look at the run: a task failed, or a report has lines to read
        """
        return bool(self.failed or self.attention)

    @property
    def summary(self) -> str:
        """
        e.g. "ingest-devices DRY-RUN: 120 devices, 117 done, 3 failed, 5 need attention"
        """
        prefix = f"{self.flow} DRY-RUN" if self.dry_run else self.flow
        done = self.total - len(self.failed)
        counts = f"{self.total} devices, {done} done, {len(self.failed)} failed, {len(self.attention)} need attention"
        return f"{prefix}: {counts}"

    def markdown(self) -> str:
        """
        The summary, a line for each failed object, and the lines of each report that needs attention
        """
        lines = [f"# {self.summary}"]
        if self.failed:
            lines += ["", "## Failed", ""]
            lines += [f"- **{name}**: {error}" for name, error in self.failed.items()]
        if self.attention:
            lines += ["", "## Needs attention", ""]
            for name, items in self.attention.items():
                lines.append(f"- **{name}**")
                lines += [f"  - {item}" for item in items]
        return "\n".join(lines) + "\n"

    def state(self) -> State[Any]:
        """
        The final state of the run: Completed, with the summary. A failed task is a line of the report
        """
        return Completed(message=self.summary)


async def _error(state: State[Any]) -> str:
    error = await state.aresult(raise_on_failure=False)
    if isinstance(error, BaseException):
        # With the notes of the error, e.g. "sync stopped at: create interface sw1__Gi0/1"
        return "; ".join(line.strip() for line in traceback.format_exception_only(error))
    return state.message or state.name or "failed"


def _attention(result: object) -> list[str]:
    """
    The lines of the report of a job that a person must read
    """
    if isinstance(result, SyncReport):
        return [*result.failures, *result.warnings]
    raise TypeError(f"RunReport can't read a {type(result).__name__}")
