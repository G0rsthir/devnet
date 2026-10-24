"""Backup flow: run the read-only Ansible backup playbook.

Orchestration only. Running playbooks belongs in `devnet_core` (run_playbook()).
"""

from prefect import flow, get_run_logger


@flow(name="backups")
def backups(limit: str = "all") -> None:
    """Back up device configs for the hosts matched by the Ansible `limit` pattern."""
    logger = get_run_logger()
    logger.warning("backups: not implemented yet (limit=%s)", limit)
