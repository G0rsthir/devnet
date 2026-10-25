"""Ingestion flow: collect data and write it to NetBox and other systems.

Orchestration only. Sources, diffing and writes belong in the `ingest` package.
"""

from prefect import flow, get_run_logger


@flow(name="ingest")
def ingest(source: str, dry_run: bool = True) -> None:
    """Ingest data from `source`. With `dry_run`, report the changes without writing them."""
    logger = get_run_logger()
    logger.warning("ingest: not implemented yet (source=%s, dry_run=%s)", source, dry_run)
