"""
Sync framework: a thin layer over DiffSync

DiffSync gives the models, the diff and the sync order. This package adds what devnet needs around it:
async I/O, a dry run, a delete guard and a report. See docs/plans/ingest-framework.md
"""

from .adapter import RemoteModel, SyncAdapter
from .report import SyncReport
from .runner import run_sync

__all__ = ["RemoteModel", "SyncAdapter", "SyncReport", "run_sync"]
