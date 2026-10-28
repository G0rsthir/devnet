from __future__ import annotations

import asyncio

from prefect import get_client
from prefect.client.orchestration import PrefectClient
from prefect.exceptions import ObjectNotFound

from devnet_core.logging import get_logger

logger = get_logger(__name__)


# tag -> max concurrent task runs
LIMITS: dict[str, int] = {
    "device-conn": 30,
}


async def _concurrency(client: PrefectClient):
    for tag, limit in LIMITS.items():
        try:
            existing = await client.read_concurrency_limit_by_tag(tag)
        except ObjectNotFound:
            existing = None

        if existing and existing.concurrency_limit == limit:
            logger.info(f"= {tag}: already {limit}, skipping")
            continue

        if existing:
            # the API has no update; replace to change the value
            await client.delete_concurrency_limit_by_tag(tag)
            logger.info(f"~ {tag}: {existing.concurrency_limit} -> {limit} (recreating)")

        await client.create_concurrency_limit(tag=tag, concurrency_limit=limit)
        if not existing:
            logger.info(f"+ {tag}: created ({limit})")


async def main() -> int:
    async with get_client() as client:
        await _concurrency(client=client)

    logger.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
