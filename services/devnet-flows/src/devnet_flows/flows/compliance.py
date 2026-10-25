"""Compliance flow: check device config/state against intent from NetBox.

Orchestration only. The collection and checks belong in the `compliance` package.
"""

from prefect import flow, get_run_logger


@flow(name="compliance")
def compliance(site: str | None = None) -> None:
    """Run compliance checks for one site, or for every site when `site` is None."""
    logger = get_run_logger()
    logger.warning("compliance: not implemented yet (site=%s)", site)
