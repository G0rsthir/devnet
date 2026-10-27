from __future__ import annotations

import asyncio

from network_shared.prefect.blocks import DeviceCredentials, NetboxServer, NsxServer, RedisServer
from prefect import get_client
from prefect.blocks.core import Block
from prefect.client.orchestration import PrefectClient
from prefect.exceptions import ObjectNotFound
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from devnet_core.logging import get_logger

logger = get_logger(__name__)


class NetboxCfg(BaseModel):
    url: str
    token: str
    verify_ssl: bool = True


class IvantiCfg(BaseModel):
    url: str
    token: str
    verify_ssl: bool = True


class RedisCfg(BaseModel):
    url: str


class DeviceCredentialsCfg(BaseModel):
    username: str
    password: str


class NsxCfg(BaseModel):
    url: str
    username: str
    password: str
    verify_ssl: bool = True
    domain: str = "default"


async def _create(name: str, block: type[Block], model: BaseModel | None):
    if not model:
        logger.info(f"! Block '{block.__name__}: {name}' not provided, skipping")
        return

    await block(**model.model_dump()).asave(name, overwrite=True)

    logger.info(f"+ Block '{block.__name__}: {name}' created")


async def _parameters(params: PrefectParameters) -> None:
    for name, cfg in params.tacacs.items():
        await _create(name=f"nsx-{name}", block=DeviceCredentials, model=cfg)


class PrefectParameters(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PROVISION_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    nsx: dict[str, DeviceCredentialsCfg] = Field(default_factory=dict)


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


async def _blocks(client: PrefectClient):
    await DeviceCredentials.aregister_type_and_schema()


async def main() -> int:
    params = PrefectParameters()
    async with get_client() as client:
        await _concurrency(client=client)
        await _blocks(client=client)

    await _parameters(params)

    logger.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
